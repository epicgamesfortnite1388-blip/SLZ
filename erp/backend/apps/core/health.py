"""Liveness and readiness probes.

``/health/`` is a cheap liveness signal (process is up). ``/ready/`` verifies
critical dependencies (database, cache) so orchestrators only route traffic
when the service can actually serve it.
"""

from __future__ import annotations

from django.core.cache import cache
from django.db import connections
from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})


def ready(request):
    checks = {}
    ok = True

    try:
        connections["default"].cursor().execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as exc:  # pragma: no cover - depends on live DB
        checks["database"] = f"error: {exc.__class__.__name__}"
        ok = False

    try:
        cache.set("__ready_probe__", "1", 5)
        checks["cache"] = "ok" if cache.get("__ready_probe__") == "1" else "error"
        ok = ok and checks["cache"] == "ok"
    except Exception as exc:  # pragma: no cover - depends on live cache
        checks["cache"] = f"error: {exc.__class__.__name__}"
        ok = False

    return JsonResponse(
        {"status": "ready" if ok else "not-ready", "checks": checks},
        status=200 if ok else 503,
    )
