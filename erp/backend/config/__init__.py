"""Config package init — ensures the Celery app is loaded with Django."""

from __future__ import annotations

try:
    from config.celery import app as celery_app  # noqa: F401

    __all__ = ("celery_app",)
except Exception:  # pragma: no cover - celery optional at import time
    __all__ = ()
