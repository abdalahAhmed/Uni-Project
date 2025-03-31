#!/bin/bash

echo "⏳ Waiting for PostgreSQL to be ready..."

while ! nc -z $DB_HOST $DB_PORT; do
  echo "⏳ Waiting for PostgreSQL on $DB_HOST:$DB_PORT..."
  sleep 1
done

echo "✅ PostgreSQL is ready!"

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start the server
echo "🚀 Starting Gunicorn..."
gunicorn university_display.wsgi:application --bind 0.0.0.0:$PORT
