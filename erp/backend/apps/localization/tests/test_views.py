"""Tests for the localization info endpoint (``GET /api/v1/localization/info/``).

The view is intentionally ``AllowAny`` (a client needs locale defaults before
it can log in). These tests pin the response contract the frontend relies on:
supported languages with direction, defaults, and dual-calendar server time.
"""

from __future__ import annotations

from django.test import TestCase
from rest_framework.test import APIClient


class LocaleInfoViewTests(TestCase):
    def test_anonymous_access_allowed_and_payload_complete(self):
        resp = APIClient().get("/api/v1/localization/info/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(
            set(resp.data.keys()),
            {"languages", "default_language", "default_timezone", "server_time"},
        )

    def test_languages_include_fa_rtl_and_en_ltr(self):
        resp = APIClient().get("/api/v1/localization/info/")
        by_code = {entry["code"]: entry for entry in resp.data["languages"]}
        self.assertIn("fa", by_code)
        self.assertIn("en", by_code)
        self.assertEqual(by_code["fa"]["direction"], "rtl")
        self.assertEqual(by_code["en"]["direction"], "ltr")

    def test_server_time_has_dual_calendar_and_iso(self):
        resp = APIClient().get("/api/v1/localization/info/")
        server_time = resp.data["server_time"]
        self.assertEqual(
            set(server_time.keys()),
            {"gregorian", "jalali", "iso", "jalali_datetime"},
        )
        # Jalali date is rendered with Latin digits here (persian_digits=False).
        self.assertTrue(server_time["jalali"].replace("/", "").isdigit())
        self.assertIn("T", server_time["iso"])
