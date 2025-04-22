#!/bin/bash

# تنتظر قاعدة البيانات تشتغل
echo "⏳ Waiting for PostgreSQL to be ready..."

# التأكد إن قاعدة البيانات جاهزة قبل البدء
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  echo "⏳ Waiting for PostgreSQL on $DB_HOST:$DB_PORT..."
  sleep 1
done

echo "✅ PostgreSQL is ready!"

# تشغيل المايجريشن
echo "🔁 Running Django migrations..."
python manage.py migrate --noinput

# تجميع الملفات الثابتة
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# تشغيل السيرفر
echo "🚀 Starting Gunicorn..."
exec gunicorn university_display.wsgi:application --bind 0.0.0.0:$PORT
# Force rebuild to detect start.sh

