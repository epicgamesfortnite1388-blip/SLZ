#!/usr/bin/env bash
# Backend container entrypoint: wait for Postgres, apply the COMMITTED database
# migrations, seed platform RBAC, then hand off to the given command
# (gunicorn / celery / runserver).
#
# NOTE: migrations are generated at development time and committed with the
# code (CI verifies there is no drift via `makemigrations --check`). The
# container intentionally does NOT run `makemigrations` at startup — schema
# changes must go through review, never appear implicitly on deploy.
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

python manage.py migrate --noinput

# Seed platform RBAC (permissions + admin role). Tolerated failure: seeding is
# idempotent, but never silently — say why we continue without it.
if ! python manage.py seed_rbac; then
    echo "[entrypoint] WARNING: seed_rbac failed; continuing without a seeded permission catalogue." >&2
fi

if [ "${COLLECT_STATIC:-0}" = "1" ]; then
    python manage.py collectstatic --noinput
fi

exec "$@"
