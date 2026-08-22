#!/usr/bin/env bash
# Backend container entrypoint: wait for Postgres, run migrations, seed platform
# RBAC, then hand off to the given command (gunicorn / celery / runserver).
set -euo pipefail

DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.dev}"
export DJANGO_SETTINGS_MODULE

echo "[entrypoint] settings=${DJANGO_SETTINGS_MODULE}"

# Wait for the database to accept connections.
python - <<'PY'
import os, time, socket
host = os.environ.get("POSTGRES_HOST", "postgres")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
for attempt in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"[entrypoint] database reachable at {host}:{port}")
            break
    except OSError:
        print(f"[entrypoint] waiting for database ({attempt+1})...")
        time.sleep(2)
else:
    raise SystemExit("[entrypoint] database never became reachable")
PY

# Foundation ships without committed migrations; generate then apply.
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py seed_rbac || true

if [ "${COLLECT_STATIC:-0}" = "1" ]; then
    python manage.py collectstatic --noinput
fi

exec "$@"
