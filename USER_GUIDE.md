# WhatsApp Intake Form Bot - User Guide

## Table of Contents
1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Meta WhatsApp Integration Setup](#meta-whatsapp-integration-setup)
4. [Admin Panel Guide](#admin-panel-guide)
5. [Viewing Collected Data](#viewing-collected-data)
6. [API Endpoints](#api-endpoints)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The WhatsApp Intake Form Bot automatically extracts structured data from WhatsApp group messages. When someone submits an intake form in a connected WhatsApp group, the bot:

1. **Receives** the message via Meta's WhatsApp Cloud API
2. **Filters** to identify intake forms (ignores regular chat)
3. **Extracts** structured fields (name, phone, email, project, school, etc.)
4. **Stores** the data in a PostgreSQL database
5. **Responds** with a confirmation message

### What Gets Extracted

| Field | Example | Required |
|-------|---------|----------|
| Name | John Doe | ✅ Yes |
| Phone | +237612345678 | No |
| Email | john@school.edu | No |
| Project | Education Platform | ✅ Yes |
| School | Lincoln High School | No |
| Teacher | Ms. Smith | No |
| Grade | 10th Grade | No |
| Subject | Mathematics | No |
| Lesson Titles | Algebra Basics | No |
| Lesson References | Chapter 5 | No |
| Notes | Additional info | No |

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MESSAGE FLOW                                       │
└─────────────────────────────────────────────────────────────────────────────┘

   WhatsApp Group                Meta Cloud API              Your Server
   ┌───────────┐                ┌─────────────┐            ┌─────────────┐
   │           │   Message      │             │  Webhook   │             │
   │  User     │ ───────────►   │   Meta      │ ────────►  │  Django     │
   │  sends    │                │   Servers   │            │  Bot        │
   │  form     │                │             │            │             │
   └───────────┘                └─────────────┘            └──────┬──────┘
                                                                  │
                                      ┌───────────────────────────┘
                                      │
                                      ▼
                               ┌─────────────┐
                               │   Parser    │
                               │  (Filter +  │
                               │  Extract)   │
                               └──────┬──────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
            ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
            │  Database   │   │  Admin      │   │  WhatsApp   │
            │  (Store)    │   │  Panel      │   │  Response   │
            └─────────────┘   └─────────────┘   └─────────────┘
```

### Smart Filtering Logic

The bot uses **intelligent filtering** to distinguish intake forms from regular chat:

- **Intake Form**: Message contains **2 or more** field markers (Name:, Phone:, Project:, etc.)
- **Regular Chat**: Messages with fewer than 2 markers are logged but ignored

**Example Intake Form (PROCESSED):**
```
Name: Jane Smith
Phone: +237612345678
Email: jane@school.edu
Project: Science Fair Project
School: Oak Elementary
Teacher: Mr. Johnson
Grade: 5th Grade
Subject: Science
Lesson: Solar System
Notes: Please prioritize this request
```

**Example Regular Chat (IGNORED):**
```
Hey everyone, meeting at 3pm today!
```

---

## Meta WhatsApp Integration Setup

### Prerequisites

- Meta Business Account
- Facebook Developer Account
- Verified Business (for production)
- Server with HTTPS (required by Meta)

### Step 1: Create Meta Developer App

1. Go to [Meta Developer Console](https://developers.facebook.com/)
2. Click **"My Apps"** → **"Create App"**
3. Select **"Business"** type
4. Enter App name: `WS4ED WhatsApp Bot`
5. Select your Business Account
6. Click **"Create App"**

### Step 2: Add WhatsApp Product

1. In your app dashboard, click **"Add Product"**
2. Find **"WhatsApp"** and click **"Set Up"**
3. Select or create a **WhatsApp Business Account**
4. You'll get a **test phone number** for development

### Step 3: Get API Credentials

From the WhatsApp section in Meta Console:

| Credential | Where to Find | What to Copy |
|------------|---------------|--------------|
| **Access Token** | WhatsApp → API Setup → Generate Token | Long string starting with `EAA...` |
| **Phone Number ID** | WhatsApp → API Setup → Phone Number ID | Numeric ID like `123456789012345` |
| **Business Account ID** | WhatsApp → API Setup | Numeric ID |

### Step 4: Configure Your Server

Edit the `.env` file in your whatsapp_bot folder:

```env
# WhatsApp Cloud API Credentials
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token_here
WHATSAPP_API_VERSION=v18.0
```

**Important:** The `WHATSAPP_VERIFY_TOKEN` is a secret you create yourself. You'll use this same value when configuring the webhook in Meta.

### Step 5: Configure Webhook in Meta Console

1. In Meta Console, go to **WhatsApp → Configuration**
2. Click **"Edit"** under Webhook

3. Enter your webhook details:
   - **Callback URL:** `https://your-domain.com/webhook/whatsapp/`
   - **Verify Token:** Same as `WHATSAPP_VERIFY_TOKEN` in your .env

4. Click **"Verify and Save"**

5. Subscribe to webhook fields:
   - ✅ `messages` - Required for receiving messages
   - ✅ `message_templates` - Optional, for template status

### Step 6: Expose Your Local Server (Public URL Options)

Meta requires an HTTPS URL to send webhooks. Here are several free alternatives:

#### Option 1: Cloudflare Tunnel (Recommended - Free & Reliable)

```bash
# Install cloudflared
# Windows: Download from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

# Or using winget:
winget install Cloudflare.cloudflared

# Run tunnel (no account needed for quick tunnels)
cloudflared tunnel --url http://localhost:90
```

This gives you a URL like `https://random-words.trycloudflare.com`

#### Option 2: LocalTunnel (Simple, No Install)

```bash
# Using npx (requires Node.js)
npx localtunnel --port 90

# Or install globally
npm install -g localtunnel
lt --port 90
```

This gives you a URL like `https://your-subdomain.loca.lt`

#### Option 3: Serveo (SSH-based, No Install)

```bash
# Using SSH (works on any system with SSH)
ssh -R 80:localhost:90 serveo.net
```

This gives you a URL like `https://random.serveo.net`

#### Option 4: Tailscale Funnel (Best for Teams)

```bash
# Install Tailscale: https://tailscale.com/download
# Login and enable Funnel

tailscale funnel 90
```

This gives you a URL like `https://your-machine.your-tailnet.ts.net`

#### Option 5: Loophole (Simple Alternative)

```bash
# Download from https://loophole.cloud/download

# Run tunnel
loophole http 90
```

#### Option 6: Free Cloud Hosting Platforms

**🌟 Best Free Options for Django:**

##### Railway (Recommended - Easiest)
- **Free Tier:** $5 credit/month (enough for small apps)
- **URL:** https://railway.app

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Deploy from your project folder
cd whatsapp_bot
railway init
railway up

# 4. Add PostgreSQL
railway add --plugin postgresql

# 5. Get your public URL
railway domain
```

##### Render (Best Free Tier)
- **Free Tier:** 750 hours/month, auto-sleep after 15min inactivity
- **URL:** https://render.com

```yaml
# Create render.yaml in project root
services:
  - type: web
    name: whatsapp-bot
    env: docker
    plan: free
    healthCheckPath: /api/health/

databases:
  - name: whatsapp-db
    plan: free
```

Then connect GitHub repo and deploy.

##### Fly.io (Good Performance)
- **Free Tier:** 3 shared VMs, 3GB storage
- **URL:** https://fly.io

```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh

# 2. Login
flyctl auth login

# 3. Launch app
cd whatsapp_bot
flyctl launch

# 4. Deploy
flyctl deploy

# 5. Get URL
flyctl info
```

##### Koyeb (Simple)
- **Free Tier:** 1 nano instance
- **URL:** https://koyeb.com

Connect GitHub and deploy with one click.

##### PythonAnywhere (Python-Specific)
- **Free Tier:** 1 web app, limited outbound requests
- **URL:** https://pythonanywhere.com
- **Note:** Free tier blocks external API calls (won't work for WhatsApp)

##### Vercel + Supabase (Serverless)
- **Free Tier:** Generous limits
- Requires converting to serverless (more complex)

##### Hugging Face Spaces (ML-Focused)
- **Free Tier:** Unlimited for public spaces
- **URL:** https://huggingface.co/spaces
- Can host Docker containers

---

### 🚀 Quick Deploy to Railway (Step-by-Step)

**1. Create Railway Account**
Go to https://railway.app and sign up with GitHub

**2. Create Procfile**
```bash
# Create file: Procfile
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

**3. Create runtime.txt**
```bash
# Create file: runtime.txt
python-3.11.0
```

**4. Deploy**
```bash
# In whatsapp_bot folder
railway login
railway init
railway up
```

**5. Add Database**
- Go to Railway dashboard
- Click "New" → "Database" → "PostgreSQL"
- Railway auto-configures DATABASE_URL

**6. Set Environment Variables**
In Railway dashboard → Variables:
```
WHATSAPP_ACCESS_TOKEN=your_token
WHATSAPP_PHONE_NUMBER_ID=your_id
WHATSAPP_VERIFY_TOKEN=your_verify_token
SECRET_KEY=your_secret_key
DEBUG=False
```

**7. Get Your Public URL**
Railway gives you: `https://your-app.up.railway.app`

Use this as your Meta webhook URL!

---

### 🚀 Quick Deploy to Render (Step-by-Step)

**1. Create render.yaml**
```yaml
services:
  - type: web
    name: whatsapp-bot
    env: docker
    plan: free
    envVars:
      - key: DEBUG
        value: "False"
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: whatsapp-db
          property: connectionString

databases:
  - name: whatsapp-db
    plan: free
```

**2. Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/whatsapp-bot.git
git push -u origin main
```

**3. Deploy on Render**
- Go to https://render.com
- Click "New" → "Blueprint"
- Connect your GitHub repo
- Render auto-deploys!

**4. Set WhatsApp Variables**
In Render dashboard → Environment:
```
WHATSAPP_ACCESS_TOKEN=your_token
WHATSAPP_PHONE_NUMBER_ID=your_id
WHATSAPP_VERIFY_TOKEN=your_verify_token
```

**5. Get Your URL**
Render gives you: `https://whatsapp-bot.onrender.com`

---

### Comparison: Free Hosting Platforms

| Platform | Free Tier | Database | Sleep? | Best For |
|----------|-----------|----------|--------|----------|
| **Railway** | $5/month credit | ✅ PostgreSQL | No | Easiest setup |
| **Render** | 750 hrs/month | ✅ PostgreSQL | Yes (15min) | Best free tier |
| **Fly.io** | 3 VMs | ✅ PostgreSQL | No | Performance |
| **Koyeb** | 1 nano | ✅ PostgreSQL | Yes | Simple |
| **Vercel** | Unlimited | ❌ (use Supabase) | No | Serverless |
| **Hugging Face** | Unlimited | ❌ | Yes | Docker apps |

**⚠️ Note on Sleep Mode:** Some free tiers "sleep" after inactivity. This means the first webhook request after sleep might timeout. Railway and Fly.io don't sleep on free tier.

---

#### Option 7: Self-Hosted Open Source Platforms

If you have your own server/VPS:

##### Coolify (Self-Hosted Heroku Alternative)
- **URL:** https://coolify.io
- Open source, self-hosted PaaS
- One-click Docker deployments

```bash
# Install on your VPS
curl -fsSL https://get.coolify.io | bash
```

##### CapRover (Self-Hosted PaaS)
- **URL:** https://caprover.com
- Open source Heroku/Dokku alternative

```bash
# Install on VPS with Docker
docker run -p 80:80 -p 443:443 -p 3000:3000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /captain:/captain \
  caprover/caprover
```

##### Dokku (Mini-Heroku)
- **URL:** https://dokku.com
- Git-push deployments

```bash
# Install on Ubuntu VPS
wget https://dokku.com/install/v0.32.3/bootstrap.sh
sudo DOKKU_TAG=v0.32.3 bash bootstrap.sh
```

#### Option 8: Deploy to VPS (Production)

For production, deploy to a VPS with a real domain:

**Recommended Providers:**
- **DigitalOcean** - $4/month droplet
- **Linode** - $5/month
- **Vultr** - $5/month
- **Hetzner** - €3.79/month (cheapest)

**Quick Deploy to VPS:**
```bash
# 1. SSH to your VPS
ssh root@your-vps-ip

# 2. Install Docker
curl -fsSL https://get.docker.com | sh

# 3. Clone/copy your project
git clone your-repo  # or use scp to copy files

# 4. Run with Docker
cd whatsapp_bot
cp .env.example .env
nano .env  # Edit with your credentials
docker-compose up -d

# 5. Setup SSL with Caddy (automatic HTTPS)
# Install Caddy: https://caddyserver.com/docs/install
caddy reverse-proxy --from your-domain.com --to localhost:90
```

#### Comparison Table

| Method | Persistent URL | Speed | Setup | Best For |
|--------|---------------|-------|-------|----------|
| Cloudflare Tunnel | No* | Fast | Easy | Development |
| LocalTunnel | No | Medium | Easiest | Quick testing |
| Serveo | No | Medium | None | SSH users |
| Tailscale Funnel | Yes | Fast | Medium | Teams |
| VPS + Domain | Yes | Fast | Complex | Production |

*Cloudflare offers persistent URLs with a free account

### Step 7: Add Phone Number to WhatsApp Group

1. Add your WhatsApp Business phone number to the target group
2. Messages sent to the group will now be received by your bot

---

## Admin Panel Guide

### Accessing the Admin Panel

**URL:** http://localhost:90/admin/

**Credentials:**
- Username: `admin`
- Password: `admin123`

### Admin Sections

#### 1. Intake Forms
View and manage all extracted intake form submissions.

| Field | Description |
|-------|-------------|
| Name | Extracted contact name |
| Phone | Phone number |
| Project | Project name |
| Status | new / processing / completed / archived |
| Confidence | Parser confidence score |
| Created | When form was received |

**Actions:**
- Click any entry to view full details
- Change status (new → processing → completed)
- Export data
- Delete entries

#### 2. Message Logs
View ALL messages received (both forms and regular chat).

| Field | Description |
|-------|-------------|
| From | Sender's phone number |
| Type | `intake_form` or `chat` |
| Was Processed | Whether data was extracted |
| Content | Raw message text |

#### 3. WhatsApp Groups
Manage which groups the bot responds to.

| Field | Description |
|-------|-------------|
| Group ID | WhatsApp group identifier |
| Group Name | Display name |
| Is Active | Enable/disable processing |
| Auto Reply | Send confirmation messages |

#### 4. Bot Responses
Configure automated response templates.

| Trigger | When Sent |
|---------|-----------|
| `form_received` | After successful form extraction |
| `form_error` | When required fields are missing |
| `welcome` | When bot joins a group |

---

## Viewing Collected Data

### Method 1: Admin Panel (Recommended)

1. Go to http://localhost:90/admin/
2. Login with admin credentials
3. Click **"Intake forms"**
4. View, filter, and export submissions

**Filtering Options:**
- By status (new, processing, completed)
- By date range
- By project name
- By school

### Method 2: REST API

#### List All Submissions
```bash
curl -X GET http://localhost:90/api/intake-forms/ \
  -H "Cookie: sessionid=your_session_id"
```

#### Filter by Status
```bash
curl -X GET "http://localhost:90/api/intake-forms/?status=new"
```

#### Filter by Project
```bash
curl -X GET "http://localhost:90/api/intake-forms/?project=Education"
```

#### Get Dashboard Statistics
```bash
curl -X GET http://localhost:90/api/dashboard/
```

Response:
```json
{
  "total_forms": 150,
  "forms_today": 12,
  "forms_this_week": 45,
  "forms_by_status": {
    "new": 30,
    "processing": 15,
    "completed": 100,
    "archived": 5
  },
  "forms_by_project": [
    {"project": "Education Platform", "count": 50},
    {"project": "Science Fair", "count": 30}
  ],
  "total_messages": 500,
  "messages_today": 25,
  "active_groups": 3
}
```

### Method 3: Direct Database Access

Connect to PostgreSQL:
```bash
docker exec -it whatsapp_bot_db psql -U whatsapp -d whatsapp_bot
```

Query examples:
```sql
-- All submissions
SELECT * FROM bot_intakeform ORDER BY created_at DESC;

-- Today's submissions
SELECT * FROM bot_intakeform 
WHERE created_at >= CURRENT_DATE;

-- By project
SELECT project, COUNT(*) as count 
FROM bot_intakeform 
GROUP BY project;

-- Export to CSV (in psql)
\COPY (SELECT * FROM bot_intakeform) TO '/tmp/export.csv' CSV HEADER;
```

---

## API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health/` | Health check |
| GET/POST | `/webhook/whatsapp/` | WhatsApp webhook |

### Authenticated Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/intake-forms/` | List all forms |
| GET | `/api/intake-forms/{id}/` | Get single form |
| PATCH | `/api/intake-forms/{id}/` | Update form |
| DELETE | `/api/intake-forms/{id}/` | Delete form |
| POST | `/api/intake-forms/{id}/mark_complete/` | Mark as complete |
| GET | `/api/message-logs/` | All message logs |
| GET | `/api/dashboard/` | Statistics |
| POST | `/api/send-message/` | Send WhatsApp message |

### Query Parameters

```
?status=new              Filter by status
?project=Education       Filter by project name
?school=Lincoln          Filter by school
?start_date=2025-01-01   Filter from date
?end_date=2025-12-31     Filter to date
```

---

## Troubleshooting

### Webhook Not Receiving Messages

1. **Check webhook URL is HTTPS** - Meta requires SSL
2. **Verify token mismatch** - Ensure `.env` matches Meta Console
3. **Check server logs:**
   ```bash
   docker logs whatsapp_bot_web --tail 100
   ```

### Messages Not Being Parsed

1. **Check message format** - Needs 2+ field markers
2. **View message logs** in admin panel
3. **Test parser:**
   ```bash
   docker exec whatsapp_bot_web python manage.py parse_test "Name: John\nProject: Test"
   ```

### Admin Panel Login Issues

Reset password:
```bash
docker exec whatsapp_bot_web python manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.get(username='admin')
u.set_password('newpassword')
u.save()
"
```

### Database Connection Issues

Check database container:
```bash
docker logs whatsapp_bot_db
docker exec whatsapp_bot_db pg_isready -U whatsapp
```

### Container Status

```bash
# View all containers
docker ps

# Restart all services
docker-compose restart

# Rebuild and restart
docker-compose up --build -d
```

---

## Quick Reference

### URLs
| Service | URL |
|---------|-----|
| Admin Panel | http://localhost:90/admin/ |
| API Root | http://localhost:90/api/ |
| Health Check | http://localhost:90/api/health/ |
| Webhook | http://localhost:90/webhook/whatsapp/ |

### Credentials
| User | Password |
|------|----------|
| admin | admin123 |

### Docker Commands
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker logs whatsapp_bot_web -f

# Rebuild
docker-compose up --build -d
```

### Important Files
```
whatsapp_bot/
├── .env                 # Your credentials (edit this!)
├── config/settings.py   # Django settings
├── bot/parser.py        # Message parsing logic
└── bot/models.py        # Database models
```

---

## Support

For issues or questions:
1. Check container logs: `docker logs whatsapp_bot_web`
2. Review message logs in admin panel
3. Test webhook: `curl http://localhost:90/api/health/`
