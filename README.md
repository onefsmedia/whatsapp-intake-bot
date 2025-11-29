# WhatsApp Intake Form Bot

A Django-based WhatsApp bot that extracts structured data from intake form messages in WhatsApp groups using the official Meta Cloud API.

## Features

- 🤖 **Smart Form Detection**: Automatically identifies intake form messages vs regular chat
- 📝 **Data Extraction**: Parses structured fields (name, phone, email, project, school, etc.)
- 🔄 **Webhook Integration**: Real-time message processing via Meta WhatsApp Cloud API
- 📊 **REST API**: Full CRUD operations for managing submissions
- 🛡️ **Group Filtering**: Only processes messages from allowed WhatsApp groups
- 📈 **Dashboard Stats**: Aggregated statistics and analytics
- 🐳 **Docker Ready**: Production-ready containerized deployment

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  WhatsApp User  │─────▶│ Meta Cloud API   │─────▶│  Your Server    │
│  (Group/DM)     │      │  (Webhook)       │      │  (Django)       │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                                           │
                              ┌─────────────────────────────┼─────────────────────────────┐
                              │                             ▼                             │
                              │  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐  │
                              │  │  Webhook    │───▶│   Parser     │───▶│  Database   │  │
                              │  │  Handler    │    │  (Filter)    │    │ (PostgreSQL)│  │
                              │  └─────────────┘    └──────────────┘    └─────────────┘  │
                              │         │                                      │          │
                              │         ▼                                      ▼          │
                              │  ┌─────────────┐                       ┌─────────────┐   │
                              │  │  WhatsApp   │                       │  REST API   │   │
                              │  │  Service    │                       │  (DRF)      │   │
                              │  └─────────────┘                       └─────────────┘   │
                              └───────────────────────────────────────────────────────────┘
```

## Extracted Fields

The bot extracts the following fields from intake form messages:

| Field | Description | Required |
|-------|-------------|----------|
| `name` | Contact name | ✅ Yes |
| `phone` | Phone number | No |
| `email` | Email address | No |
| `project` | Project name | ✅ Yes |
| `school` | School name | No |
| `teacher` | Teacher name | No |
| `grade` | Grade level | No |
| `subject` | Subject area | No |
| `lesson_titles` | Lesson titles | No |
| `lesson_references` | Reference materials | No |
| `notes` | Additional notes | No |

## Quick Start

### Prerequisites

- Python 3.10+
- Meta Developer Account with WhatsApp Business API
- PostgreSQL (production) or SQLite (development)

### Local Development

1. **Clone and setup environment:**
   ```bash
   cd whatsapp_bot
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   copy .env.example .env
   # Edit .env with your WhatsApp credentials
   ```

3. **Initialize database:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Run development server:**
   ```bash
   python manage.py runserver
   ```

5. **Access:**
   - Admin Panel: http://localhost:8000/admin/
   - API: http://localhost:8000/api/
   - Health: http://localhost:8000/api/health/

### Docker Deployment

1. **Development:**
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```

2. **Production:**
   ```bash
   docker-compose up --build -d
   ```

## WhatsApp Setup

### 1. Create Meta Developer App

1. Go to [Meta Developer Console](https://developers.facebook.com/)
2. Create a new app → Business → WhatsApp
3. Set up WhatsApp Business API

### 2. Configure Webhook

1. In Meta Console, go to WhatsApp → Configuration
2. Add webhook URL: `https://your-domain.com/webhook/whatsapp/`
3. Set verify token (same as `WHATSAPP_VERIFY_TOKEN` in .env)
4. Subscribe to: `messages`, `message_templates`

### 3. Get Credentials

Copy these from Meta Console to your `.env`:
- `WHATSAPP_ACCESS_TOKEN` - From System Users → Generate Token
- `WHATSAPP_PHONE_NUMBER_ID` - From WhatsApp → Phone Numbers

## API Endpoints

### Intake Forms
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/intake-forms/` | List all submissions |
| GET | `/api/intake-forms/{id}/` | Get single submission |
| PATCH | `/api/intake-forms/{id}/` | Update submission |
| DELETE | `/api/intake-forms/{id}/` | Delete submission |
| GET | `/api/intake-forms/by-status/?status=new` | Filter by status |
| POST | `/api/intake-forms/{id}/mark_complete/` | Mark as complete |

### Message Logs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/message-logs/` | All message logs |
| GET | `/api/message-logs/intake-forms/` | Only form messages |
| GET | `/api/message-logs/chat/` | Only chat messages |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/` | Get statistics |
| POST | `/api/send-message/` | Send WhatsApp message |
| GET | `/api/health/` | Health check |

### Webhook
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/webhook/whatsapp/` | Meta verification |
| POST | `/webhook/whatsapp/` | Receive messages |

## Message Format

The bot recognizes intake forms with these markers:

```
Name: John Doe
Phone: +1234567890
Email: john@example.com
Project: Education App
School: Lincoln High School
Teacher: Ms. Smith
Grade: 10th
Subject: Mathematics
Lesson: Algebra Basics
Notes: Please prioritize this request
```

A message needs **at least 2 field markers** to be classified as an intake form.

## Security Considerations

1. **HTTPS Required**: WhatsApp webhooks require HTTPS in production
2. **Token Security**: Never commit `.env` files
3. **Webhook Verification**: Always verify webhook signatures
4. **Group Whitelist**: Use `WhatsAppGroup` model to control which groups are processed

## Project Structure

```
whatsapp_bot/
├── config/                 # Django project settings
│   ├── settings.py        # Main configuration
│   ├── urls.py            # Root URL routing
│   └── wsgi.py            # WSGI entry point
├── bot/                   # Main application
│   ├── models.py          # Database models
│   ├── parser.py          # Message parsing logic
│   ├── views.py           # REST API views
│   ├── serializers.py     # DRF serializers
│   ├── whatsapp_service.py # WhatsApp API client
│   ├── webhook_handler.py  # Webhook processing
│   ├── admin.py           # Django admin config
│   └── urls.py            # API URL routing
├── nginx/                 # Nginx configuration
├── docker-compose.yml     # Production Docker
├── docker-compose.dev.yml # Development Docker
├── Dockerfile             # Container build
├── requirements.txt       # Python dependencies
└── .env.example          # Environment template
```

## Troubleshooting

### Webhook not receiving messages
- Ensure URL is HTTPS (use ngrok for local testing)
- Check webhook subscription in Meta Console
- Verify `WHATSAPP_VERIFY_TOKEN` matches

### Messages not being parsed
- Check `MessageLog` for raw messages
- Verify message has at least 2 field markers
- Review `bot/parser.py` patterns

### Database connection issues
- Verify `DATABASE_URL` format
- Ensure PostgreSQL is running
- Check Docker network connectivity

## License

MIT License - See LICENSE file
