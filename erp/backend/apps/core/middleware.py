"""Correlation-id middleware, request context and logging filter.

Every request is tagged with a correlation id (from the ``X-Correlation-ID``
header if the client supplies one, otherwise generated). It is stored in a
thread/async-local so any layer — audit, events, logging — can read it without
threading the request object through every call. It is echoed back on the
response and injected into every log record.

The ``CompanyContextMiddleware`` reads the ``X-SLZ-Company`` header, validates
that the authenticated user is a member of that company, and sets
``request.company_id`` for downstream permission checks (Q-055).
"""

from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from typing import Optional

_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
_current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)

HEADER = "HTTP_X_CORRELATION_ID"
RESPONSE_HEADER = "X-Correlation-ID"
COMPANY_HEADER = "HTTP_X_SLZ_COMPANY"


def get_correlation_id() -> Optional[str]:
    return _correlation_id.get()


def set_correlation_id(value: Optional[str]) -> None:
    _correlation_id.set(value)


def get_current_user_id() -> Optional[str]:
    return _current_user_id.get()


def set_current_user_id(value: Optional[str]) -> None:
    _current_user_id.set(value)


class CorrelationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cid = request.META.get(HEADER) or uuid.uuid4().hex
        token = _correlation_id.set(cid)
        user = getattr(request, "user", None)
        user_token = _current_user_id.set(
            str(user.pk) if getattr(user, "is_authenticated", False) else None
        )
        try:
            response = self.get_response(request)
        finally:
            _correlation_id.reset(token)
            _current_user_id.reset(user_token)
        response[RESPONSE_HEADER] = cid
        return response


class CorrelationIdLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id() or "-"
        return True


class CompanyContextMiddleware:
    """Read ``X-SLZ-Company`` header and validate membership.

    Sets ``request.company_id`` (a str UUID) when the user is a member of the
    company named by the header.  Does *not* fail the request when the header
    is absent or invalid — downstream permission checks decide whether an
    operation is allowed without a company context (global roles may still
    grant access, and superusers bypass).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.company_id: str | None = None
        if hasattr(request, "user") and request.user.is_authenticated:
            raw = request.META.get(COMPANY_HEADER, "").strip()
            if raw:
                # Validate the user is a member of this company.
                is_member = request.user.company_memberships.filter(
                    company_id=raw,
                ).exists()
                if is_member:
                    request.company_id = raw
        return self.get_response(request)
