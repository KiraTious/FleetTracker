#!/bin/bash
set -e

export FLASK_APP=${FLASK_APP:-app.py}

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-postgres}
DB_NAME=${DB_NAME:-fleettracker}

until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  echo "Waiting for database $DB_HOST:$DB_PORT..."
  sleep 2
done

echo "Applying database migrations..."
flask db upgrade

echo "Seeding initial data..."
PGPASSWORD="$DB_PASSWORD" psql -v ON_ERROR_STOP=1 -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f /app/db_seed.sql

echo "Starting application..."
exec gunicorn -b 0.0.0.0:${PORT:-5000} app:app
