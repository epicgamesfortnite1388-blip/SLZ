"""DRF exception handler producing a consistent error envelope.

Shape (see docs/architecture/api-conventions.md):

    {
      "error": {
        "type": "ValidationError",
        "message": "...",
        "details": {...} | null,
        "code": "optional.machine.code" | null,
        "correlation_id": "..."
      }
    }

Built-in DRF/Django exceptions are mapped onto the standardized types so clients
only ever see the documented set. Unhandled exceptions become a generic
``SystemError`` (500) with no stack trace.
"""

from __future__ import annotations

import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from apps.core import exceptions as core_exc
from apps.core.middleware import get_correlation_id

logger = logging.getLogger("apps.core.errors")


def _clean_detail(detail) -> str | None:
    """Flatten DRF exception details into a human-readable message.

    SimpleJWT raises ``AuthenticationFailed`` with a *dict* detail
    (``{"detail": ErrorDetail("Token is invalid or expired", …), "code": …}``);
    ``str()`` on that leaks a repr like ``"{'detail': ErrorDetail(…)}`` into
    the client-facing message.
    """
    if detail is None:
        return None
    if isinstance(detail, dict):
        inner = detail.get("detail", "")
        return str(inner) if inner != "" else None
    return str(detail)


def _to_domain_error(exc) -> core_exc.BaseDomainError:
    if isinstance(exc, core_exc.BaseDomainError):
        return exc
    if isinstance(exc, (Http404, drf_exceptions.NotFound)):
        return core_exc.NotFoundError()
    if isinstance(exc, (PermissionDenied, drf_exceptions.PermissionDenied)):
        return core_exc.AuthorizationError()
    if isinstance(exc, drf_exceptions.NotAuthenticated):
        return core_exc.AuthenticationError()
    if isinstance(exc, drf_exceptions.AuthenticationFailed):
        return core_exc.AuthenticationError(_clean_detail(exc.detail))
    # Throttled must not fall into the generic APIException branch: that would
    # render a 500. It keeps its 429 status and DRF's Retry-After header.
    if isinstance(exc, drf_exceptions.Throttled):
        return core_exc.ThrottledError()
    if isinstance(exc, drf_exceptions.ValidationError):
        return core_exc.ValidationError(details=exc.detail)
    if isinstance(exc, drf_exceptions.APIException):
        return core_exc.BaseDomainError(
            message=str(exc.detail), code=getattr(exc, "default_code", None)
        )
    return None  # not a known/handled exception


def standardized_exception_handler(exc, context):
    domain = _to_domain_error(exc)

    if domain is None:
        # Unknown/unexpected: log with stack trace, return opaque 500.
        logger.exception("Unhandled exception", exc_info=exc)
        domain = core_exc.SystemError()

    payload = {
        "error": {
            "type": domain.error_type,
            "message": domain.message,
            "details": domain.details,
            "code": domain.code,
            "correlation_id": get_correlation_id(),
        }
    }

    # Let DRF set auth-related headers (e.g. WWW-Authenticate) when relevant.
    drf_response = drf_exception_handler(exc, context)
    headers = drf_response.headers if drf_response is not None else None
    response = Response(payload, status=domain.status_code)
    if headers:
        for key, value in headers.items():
            if key.lower() not in ("content-type", "content-length"):
                response[key] = value
    return response
