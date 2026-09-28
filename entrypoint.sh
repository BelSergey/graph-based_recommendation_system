#!/bin/sh
set -e

echo "Ожидание PostgreSQL (${DB_HOST}:${DB_PORT})..."

while ! nc -z "${DB_HOST}" "${DB_PORT}"; do
    sleep 0.5
done

echo "PostgreSQL доступен."

echo "Применение миграций..."
python manage.py migrate --noinput

echo "Сборка статики..."
python manage.py collectstatic --noinput

echo "Запуск gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 60