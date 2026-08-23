#!/usr/bin/env bash
# Backend container entrypoint: wait for Postgres, apply the COMMITTED database
# migrations, seed platform RBAC, then hand off to the given command
# (gunicorn / celery / runserver).
#
# NOTE: migrations are generated at development time and committed with the
# code (CI verifies there is no drift via `makemigrations --check`). The
# container intentionally does NOT run `makemigrations` at startup — schema
# changes must go through review, never appear implicitly on deploy.
#
# Environment variables that control entrypoint behaviour:
#   SEED_RBAC_STRICT   if "true"/"1", fail the container when seed_rbac fails
#                      (production). Otherwise warn and continue (dev).
#   COLLECT_STATIC     if "1", run collectstatic before handing off (set in
#                      production when static files are served by whitenoise).
#   POSTGRES_HOST      database hostname (default: postgres)
#   POSTGRES_PORT      database port (default: 5432)
set -euo pipefail

DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.dev}"
export DJANGO_SETTINGS_MODULE

echo "[entrypoint] settings=${DJANGO_SETTINGS_MODULE}"

# Wait for the database to accept connections.
python - <<'PY'
import os, time, socket
host = os.environ.get("POSTGRES_HOST", "postgres")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
deadline = time.monotonic() + 120
while time.monotonic() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"[entrypoint] database reachable at {host}:{port}")
            break
    except OSError:
        print(f"[entrypoint] waiting for database {host}:{port} ...")
        time.sleep(2)
else:
    raise SystemExit("[entrypoint] database never became reachable after 120 s")
PY

# Apply committed migrations.
echo "[entrypoint] applying database migrations..."
python manage.py migrate --noinput

# Seed platform RBAC (permissions + admin role).
# In production (SEED_RBAC_STRICT=1/true) we exit if seeding fails;
# in development we tolerate failure so the container still starts.
echo "[entrypoint] seeding RBAC..."
if python manage.py seed_rbac; then
    echo "[entrypoint] RBAC seeded successfully."
else
    strict_val="$(echo "${SEED_RBAC_STRICT:-false}" | tr '[:upper:]' '[:lower:]')"
    if [ "$strict_val" = "true" ] || [ "$strict_val" = "1" ]; then
        echo "[entrypoint] FATAL: seed_rbac failed and SEED_RBAC_STRICT=${SEED_RBAC_STRICT}." >&2
        exit 1
    fi
    echo "[entrypoint] WARNING: seed_rbac failed; continuing without a seeded permission catalogue." >&2
fi

# Optionally collect static files (production path — whitenoise serves them).
if [ "${COLLECT_STATIC:-0}" = "1" ]; then
    echo "[entrypoint] collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "[entrypoint] handing off to: $*"
exec "$@"