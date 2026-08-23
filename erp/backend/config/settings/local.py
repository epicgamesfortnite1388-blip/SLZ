"""Fully self-contained local-development settings — zero external services.

Use these when you want to run the API on the host WITHOUT Docker/PostgreSQL/
Redis (e.g. first clone, or a Windows machine without Docker):

    set DJANGO_SETTINGS_MODULE=config.settings.local   # Windows
    export DJANGO_SETTINGS_MODULE=config.settings.local
    python manage.py migrate
    python manage.py seed_rbac
    python manage.py runserver

Differences from ``dev``:
* SQLite database file in the backend root (gitignored via ``db.sqlite3``).
* Celery runs eagerly in-process, so Redis is not needed.
Everything else (RBAC, audit trail, error envelope, throttling) is identical.
NOT for production: production must use PostgreSQL (``config.settings.prod``).
"""

from pathlib import Path

from config import env
from config.settings.dev import *  # noqa: F401,F403

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# No Redis in this mode; run Celery tasks synchronously.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# Use local-memory cache instead of Redis (no external service needed).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "slz-erp-local",
    }
}

# Allow the frontend's custom correlation-id header through CORS preflight.
from corsheaders.defaults import default_headers  # noqa: E402

CORS_ALLOW_HEADERS = list(default_headers) + ["x-correlation-id"]

# Local file uploads next to the SQLite database.
MEDIA_ROOT = BASE_DIR / "media"
