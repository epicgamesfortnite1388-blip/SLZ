"""Base Django settings shared across all environments.

Environment-specific modules (dev/prod/test) import from here. No secrets are
hard-coded; everything sensitive is read from the environment (see ``.env``).
"""

from __future__ import annotations

from pathlib import Path

from config import env

# --- Paths -----------------------------------------------------------------
# config/settings/base.py -> config/settings -> config -> backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env.load_dotenv(BASE_DIR / ".env")

# --- Core security ---------------------------------------------------------
SECRET_KEY = env.get("DJANGO_SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = env.get_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env.get_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1"])

# --- Applications ----------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
]

# Order matters: core first (base models), then platform modules.
LOCAL_APPS = [
    "apps.core",
    "apps.identity",
    "apps.organization",
    "apps.audit",
    "apps.documents",
    "apps.localization",
    "apps.notifications",
    "apps.workflow",
    # Task 004 — Master Data domain modules.
    "apps.partners",
    "apps.catalog",
    "apps.hr",
    # Task 005 — Product Engineering (versioned specification).
    "apps.engineering",
    # Task 006 — Manufacturing (BOM & Routing engineering definition).
    "apps.manufacturing",
    # Task 007 — Inventory Foundation.
    "apps.inventory",
    # Task 008 — Quality (inspection / quality plan definition).
    "apps.quality",
    # Task 009 — Procurement (requisitions & purchase orders).
    "apps.procurement",
    # Task 010 — Sales (customer orders).
    "apps.sales",
    # Task 011 — Production (work orders).
    "apps.production",
    # Task 012 — Costing (dated weighted-average valuation).
    "apps.costing",
    # Task 013 — Shipment (allocation + delivery).
    "apps.shipment",
    # Task 014 — Planning (reorder policies + read-only planning engine).
    "apps.planning",
    # Task 015 — Recall (traceability-based quality events).
    "apps.recall",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Platform middleware: assigns a correlation id to every request and
    # exposes the current request for the audit/event layers.
    "apps.core.middleware.CorrelationIdMiddleware",
    # Company-scoped RBAC: reads X-SLZ-Company header, validates membership,
    # sets request.company_id for downstream HasPermission checks (Q-055).
    "apps.core.middleware.CompanyContextMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database (PostgreSQL via env) ----------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.get("POSTGRES_DB", "slz_erp"),
        "USER": env.get("POSTGRES_USER", "slz_erp"),
        "PASSWORD": env.get("POSTGRES_PASSWORD", "slz_erp"),
        "HOST": env.get("POSTGRES_HOST", "localhost"),
        "PORT": env.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": env.get_int("DB_CONN_MAX_AGE", 60),
    }
}

AUTH_USER_MODEL = "identity.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Internationalization / calendars -------------------------------------
# Persian (fa-IR, RTL) and English (en-US, LTR). Datetimes are always stored
# timezone-aware in UTC; Jalali rendering happens at the presentation layer.
LANGUAGE_CODE = env.get("DJANGO_LANGUAGE_CODE", "fa")
LANGUAGES = [("fa", "فارسی"), ("en", "English")]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = env.get("DJANGO_TIME_ZONE", "Asia/Tehran")
USE_I18N = True
USE_TZ = True

# --- Static / media --------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- REST framework --------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": env.get_int("API_PAGE_SIZE", 25),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ),
    "EXCEPTION_HANDLER": "apps.core.handlers.standardized_exception_handler",
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    # Baseline brute-force resistance for the unauthenticated auth endpoints
    # (login / token refresh); per-IP, see apps.identity.views.AuthAnonThrottle.
    "DEFAULT_THROTTLE_RATES": {
        "auth": env.get("AUTH_THROTTLE_RATE", "30/min"),
    },
}

# --- JWT auth --------------------------------------------------------------
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.get_int("JWT_ACCESS_MINUTES", 60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.get_int("JWT_REFRESH_DAYS", 7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

# --- File upload policy (see apps/documents) ------------------------------
DOCUMENTS_MAX_UPLOAD_BYTES = env.get_int("DOCUMENTS_MAX_UPLOAD_BYTES", 25 * 1024 * 1024)
DOCUMENTS_ALLOWED_EXTENSIONS = env.get_list(
    "DOCUMENTS_ALLOWED_EXTENSIONS",
    ["pdf", "png", "jpg", "jpeg", "svg", "ai", "pdf", "xlsx", "docx", "csv", "txt", "zip"],
)

# --- Celery / Redis --------------------------------------------------------
CELERY_BROKER_URL = env.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CELERY_TASK_ALWAYS_EAGER = env.get_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_TRACK_STARTED = True
CELERY_TIMEZONE = TIME_ZONE

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.get("REDIS_CACHE_URL", "redis://localhost:6379/2"),
    }
}

# --- CORS ------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.get_list("CORS_ALLOWED_ORIGINS", ["http://localhost:5173"])

# --- Logging (structured, correlation-id aware) ---------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "correlation_id": {"()": "apps.core.middleware.CorrelationIdLogFilter"},
    },
    "formatters": {
        "structured": {
            "format": (
                "%(asctime)s level=%(levelname)s logger=%(name)s "
                "correlation_id=%(correlation_id)s %(message)s"
            )
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["correlation_id"],
            "formatter": "structured",
        },
    },
    "root": {"handlers": ["console"], "level": env.get("LOG_LEVEL", "INFO")},
}

API_VERSION = "v1"
