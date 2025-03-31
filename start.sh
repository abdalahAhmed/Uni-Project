#!/bin/bash

echo "⏳ Waiting for PostgreSQL to be ready..."

while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "✅ PostgreSQL is ready!"

python manage.py migrate
python manage.py collectstatic --noinput
gunicorn university_display.wsgi:application --bind 0.0.0.0:$PORT
