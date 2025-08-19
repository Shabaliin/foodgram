#!/bin/sh
set -e

# Wait for DB (simple retry loop)
if [ -n "$POSTGRES_HOST" ]; then
  echo "Waiting for database at $POSTGRES_HOST:$POSTGRES_PORT..."
  ATTEMPTS=0
  until python - <<'PY'
import sys
import os
import psycopg2
try:
    psycopg2.connect(
        host=os.getenv('POSTGRES_HOST','db'),
        port=int(os.getenv('POSTGRES_PORT','5432')),
        dbname=os.getenv('POSTGRES_DB','foodgram'),
        user=os.getenv('POSTGRES_USER','foodgram'),
        password=os.getenv('POSTGRES_PASSWORD','foodgram'),
    ).close()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
PY
  do
    ATTEMPTS=$((ATTEMPTS+1))
    if [ $ATTEMPTS -gt 30 ]; then
      echo "Database not ready after 30 attempts" >&2
      exit 1
    fi
    sleep 2
  done
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn foodgram_backend.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3}
