"""PostgreSQL-backed test settings — for tests that need real database
semantics (row-level locks, advisory locks, true two-connection concurrency).

Standard CI runs on SQLite via ``config.settings.test``; the tests that require
PostgreSQL (e.g. the two-thread concurrency regression suite) skip themselves
there and are executed against the compose Postgres instance instead::

    docker compose exec -T backend python manage.py test \\
        apps.inventory.tests.test_concurrency_postgres \\
        apps.shipment.tests.test_concurrency_postgres \\
        --settings=config.settings.test_pg --noinput

Everything else (MD5 hashers for speed, locmem cache, eager Celery) matches
``config.settings.test`` exactly.
"""

import os

from config.settings.test import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "slz_erp"),
        "USER": os.environ.get("POSTGRES_USER", "slz_erp"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "slz_erp"),
        "HOST": os.environ.get("POSTGRES_HOST", "postgres"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
