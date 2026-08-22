"""Number/currency/timezone formatting tests."""

from __future__ import annotations

import datetime as _dt

from django.test import TestCase

from apps.localization.numbers import (
    format_currency,
    format_number,
    to_latin_digits,
    to_persian_digits,
)
from apps.localization.timezone import ensure_aware, to_timezone


class NumberTests(TestCase):
    def test_group_thousands(self):
        self.assertEqual(format_number(1234567), "1,234,567")

    def test_persian_digits(self):
        self.assertEqual(to_persian_digits("123"), "۱۲۳")
        self.assertEqual(to_latin_digits("۱۲۳"), "123")

    def test_decimals(self):
        self.assertEqual(format_number(1234.5, decimals=2), "1,234.50")

    def test_currency(self):
        self.assertEqual(format_currency(50000, currency="IRR"), "50,000 IRR")


class TimezoneTests(TestCase):
    def test_ensure_aware(self):
        naive = _dt.datetime(2026, 8, 21, 12, 0, 0)
        aware = ensure_aware(naive, "UTC")
        self.assertIsNotNone(aware.tzinfo)

    def test_to_timezone_shifts(self):
        utc = ensure_aware(_dt.datetime(2026, 8, 21, 12, 0, 0), "UTC")
        tehran = to_timezone(utc, "Asia/Tehran")
        # Asia/Tehran is UTC+3:30.
        self.assertEqual((tehran.hour, tehran.minute), (15, 30))
