"""Test settings — SQLite so the suite runs without PostgreSQL.

The application code is database-agnostic (standard Django ORM); PostgreSQL is
used in dev/prod while tests stay fast and dependency-light. A throwaway
file-backed database avoids shared-cache in-memory instability on Windows.
"""

import os
import tempfile
from pathlib import Path

from config.settings.base import *  # noqa: F401,F403

DEBUG = False
# Unique per process so parallel/aborted runs never contend for the same file.
_SQLITE_TEST_FILE = Path(tempfile.gettempdir()) / f"slz_erp_test_{os.getpid()}.sqlite3"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(_SQLITE_TEST_FILE),
        "TEST": {"NAME": str(_SQLITE_TEST_FILE)},
    }
}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
CELERY_TASK_ALWAYS_EAGER = True
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
# Keep upload-test bytes out of the repository's backend/media/ directory.
MEDIA_ROOT = str(Path(tempfile.gettempdir()) / "slz_erp_test_media")
