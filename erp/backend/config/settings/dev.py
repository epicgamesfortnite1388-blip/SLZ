"""Development settings."""

from config import env
from config.settings.base import *  # noqa: F401,F403

DEBUG = env.get_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env.get_list("DJANGO_ALLOWED_HOSTS", ["*"])
# Convenience for local runs without Redis available.
CELERY_TASK_ALWAYS_EAGER = env.get_bool("CELERY_TASK_ALWAYS_EAGER", True)
