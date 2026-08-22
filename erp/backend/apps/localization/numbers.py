"""Number, digit and currency formatting.

Numbers are always stored as numeric types (never formatted strings). These
helpers format for display only. Persian and Latin digit systems are both
supported; the currency is configurable (defaults to IRR).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Union

Number = Union[int, float, Decimal, str]

_LATIN_TO_PERSIAN = {ord(str(i)): p for i, p in enumerate("۰۱۲۳۴۵۶۷۸۹")}
_PERSIAN_TO_LATIN = {ord(p): str(i) for i, p in enumerate("۰۱۲۳۴۵۶۷۸۹")}


def to_persian_digits(text: str) -> str:
    return str(text).translate(_LATIN_TO_PERSIAN)


def to_latin_digits(text: str) -> str:
    return str(text).translate(_PERSIAN_TO_LATIN)


def group_thousands(value: Number, sep: str = ",", decimals: int | None = None) -> str:
    dec = Decimal(str(value))
    if decimals is not None:
        dec = dec.quantize(Decimal(10) ** -decimals)
    text = f"{dec:,f}" if decimals is None else f"{dec:,.{decimals}f}"
    if sep != ",":
        text = text.replace(",", sep)
    return text


def format_number(
    value: Number, *, persian_digits: bool = False, decimals: int | None = None
) -> str:
    text = group_thousands(value, decimals=decimals)
    return to_persian_digits(text) if persian_digits else text


def format_currency(
    value: Number,
    *,
    currency: str = "IRR",
    persian_digits: bool = False,
    decimals: int = 0,
) -> str:
    amount = format_number(value, persian_digits=persian_digits, decimals=decimals)
    return f"{amount} {currency}"
