#!/bin/sh
set -e

echo "Ожидаем Postgres на ${POSTGRES_HOST}:${POSTGRES_PORT}..."
until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" >/dev/null 2>&1; do
  sleep 1
done
echo "Postgres готов."

python manage.py migrate --noinput
python manage.py seed_demo
python manage.py collectstatic --noinput

exec "$@"
