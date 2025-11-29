#!/bin/sh
set -e

echo "=== WhatsApp Intake Bot Starting ==="
echo "PORT: ${PORT:-8000}"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120
