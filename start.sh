#!/bin/sh
set -e

echo "Starting WhatsApp Bot..."
echo "PORT: $PORT"
echo "DATABASE_URL set: $(if [ -n "$DATABASE_URL" ]; then echo yes; else echo no; fi)"

echo "Running migrations..."
python manage.py migrate --noinput || echo "Migration failed, continuing anyway"

echo "Starting Gunicorn on port ${PORT:-8000}..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120
