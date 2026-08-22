"""Jalali/Gregorian calendar conversion tests (incl. leap years & boundaries)."""

from __future__ import annotations

import datetime as _dt

from django.test import TestCase

from apps.localization.calendar import (
    format_jalali,
    gregorian_to_jalali,
    is_jalali_leap_year,
    jalali_to_gregorian,
    parse_jalali,
)


class CalendarTests(TestCase):
    def test_known_conversion_nowruz(self):
        # 1 Farvardin 1403 == 20 March 2024 (Nowruz).
        greg = jalali_to_gregorian(1403, 1, 1)
        self.assertEqual(greg, _dt.date(2024, 3, 20))

    def test_round_trip(self):
        original = _dt.date(2026, 8, 21)
        jd = gregorian_to_jalali(original)
        back = jalali_to_gregorian(jd.year, jd.month, jd.day)
        self.assertEqual(back, original)

    def test_format_latin_digits(self):
        text = format_jalali(_dt.date(2024, 3, 20), persian_digits=False)
        self.assertEqual(text, "1403/01/01")

    def test_format_persian_digits(self):
        text = format_jalali(_dt.date(2024, 3, 20), persian_digits=True)
        self.assertEqual(text, "۱۴۰۳/۰۱/۰۱")

    def test_parse_accepts_persian_digits(self):
        self.assertEqual(parse_jalali("۱۴۰۳/۰۱/۰۱"), _dt.date(2024, 3, 20))

    def test_leap_year(self):
        # 1403 is a Jalali leap year (Esfand has 30 days).
        self.assertTrue(is_jalali_leap_year(1403))
        self.assertEqual(jalali_to_gregorian(1403, 12, 30), _dt.date(2025, 3, 20))
