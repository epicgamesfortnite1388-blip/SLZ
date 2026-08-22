"""Correlation-id middleware, request context and logging filter.

Every request is tagged with a correlation id (from the ``X-Correlation-ID``
header if the client supplies one, otherwise generated). It is stored in a
thread/async-local so any layer — audit, events, logging — can read it without
threading the request object through every call. It is echoed back on the
response and injected into every log record.
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
