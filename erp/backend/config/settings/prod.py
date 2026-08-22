"""Production settings — hardened defaults; all secrets come from env."""

from config import env
from config.settings.base import *  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = env.get_list("DJANGO_ALLOWED_HOSTS", [])

# HTTPS / cookie hardening (assumes TLS termination in front).
SECURE_SSL_REDIRECT = env.get_bool("SECURE_SSL_REDIRECT", True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.get_int("SECURE_HSTS_SECONDS", 60 * 60 * 24 * 30)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

if SECRET_KEY == "insecure-dev-key-change-me":  # noqa: F405
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production.")
