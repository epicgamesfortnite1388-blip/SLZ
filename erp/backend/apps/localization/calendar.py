"""Jalali (Solar Hijri) <-> Gregorian calendar utilities.

Backed by the mature ``jdatetime`` library — no hand-rolled calendar math. The
canonical storage form is always a timezone-aware Gregorian ``datetime`` in the
database; Jalali is a *presentation* concern produced here. Persian date strings
are never stored.
"""

from __future__ import annotations

import datetime as _dt
from typing import Optional

import jdatetime

from apps.localization.numbers import to_persian_digits


def gregorian_to_jalali(value: _dt.date) -> jdatetime.date:
    if isinstance(value, _dt.datetime):
        return jdatetime.datetime.fromgregorian(datetime=value).date()
    return jdatetime.date.fromgregorian(date=value)


def jalali_to_gregorian(jyear: int, jmonth: int, jday: int) -> _dt.date:
    return jdatetime.date(jyear, jmonth, jday).togregorian()


def format_jalali(value: _dt.date, fmt: str = "%Y/%m/%d", persian_digits: bool = True) -> str:
    """Format a Gregorian date/datetime as a Jalali string."""
    jdate = gregorian_to_jalali(value)
    text = jdate.strftime(fmt)
    return to_persian_digits(text) if persian_digits else text


def parse_jalali(text: str, fmt: str = "%Y/%m/%d") -> _dt.date:
    """Parse a Jalali date string (Latin digits) into a Gregorian date."""
    normalized = _to_latin_digits(text)
    jdate = jdatetime.datetime.strptime(normalized, fmt)
    return jdate.togregorian().date()


def is_jalali_leap_year(jyear: int) -> bool:
    return jdatetime.date(jyear, 1, 1).isleap()


_PERSIAN_TO_LATIN = {ord(p): str(i) for i, p in enumerate("۰۱۲۳۴۵۶۷۸۹")}
_ARABIC_TO_LATIN = {ord(a): str(i) for i, a in enumerate("٠١٢٣٤٥٦٧٨٩")}


def _to_latin_digits(text: str) -> str:
    return text.translate(_PERSIAN_TO_LATIN).translate(_ARABIC_TO_LATIN)


def dual_calendar(value: Optional[_dt.date]) -> dict:
    """Return both representations for API responses."""
    if value is None:
        return {"gregorian": None, "jalali": None}
    return {
        "gregorian": value.isoformat(),
        "jalali": format_jalali(value, persian_digits=False),
    }
