#!/bin/sh
set -e

echo "Starting WhatsApp Bot..."
echo "PORT: $PORT"
echo "DATABASE_URL: ${DATABASE_URL:-not set}"

echo "Testing database connection..."
python -c "
import os
import sys
try:
    import psycopg2
    db_url = os.environ.get('DATABASE_URL', '')
    print(f'Attempting connection to: {db_url[:50]}...')
    conn = psycopg2.connect(db_url, connect_timeout=10)
    print('Database connection successful!')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
    print('Starting without database...')
" || echo "Database test script failed"

echo "Running migrations..."
python manage.py migrate --noinput 2>&1 || echo "Migration warning - continuing"

echo "Starting Gunicorn on port ${PORT:-8000}..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120
