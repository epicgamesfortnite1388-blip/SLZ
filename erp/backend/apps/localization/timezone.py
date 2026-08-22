"""Timezone helpers.

Rule: no naive datetimes anywhere. Everything is stored timezone-aware in UTC
(``USE_TZ = True``) and converted to a site/user timezone only for display.
"""

from __future__ import annotations

import datetime as _dt
from zoneinfo import ZoneInfo

from django.utils import timezone


def now_utc() -> _dt.datetime:
    return timezone.now()


def to_timezone(value: _dt.datetime, tz_name: str) -> _dt.datetime:
    if value is None:
        return None
    if timezone.is_naive(value):
        value = timezone.make_aware(value, ZoneInfo("UTC"))
    return value.astimezone(ZoneInfo(tz_name))


def ensure_aware(value: _dt.datetime, tz_name: str = "UTC") -> _dt.datetime:
    if value is not None and timezone.is_naive(value):
        return timezone.make_aware(value, ZoneInfo(tz_name))
    return value
