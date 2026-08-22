"""Regression tests for the self-profile (``PATCH /auth/me/``) endpoint.

Historically the endpoint applied raw ``setattr`` without validation, so an
over-long ``full_name`` surfaced as a 500 (DB DataError) and an unknown
language code was silently persisted, breaking locale rendering afterwards.
These tests pin the validated behavior: bad values are clean 400s.
"""

from __future__ import annotations

from django.test import TestCase

from apps.core.tests.factories import auth_client, make_user


class MeProfileUpdateTests(TestCase):
    def setUp(self):
        self.user = make_user(email="me@slz.test")
        self.client = auth_client(self.user)

    def _patch(self, **payload):
        return self.client.patch("/api/v1/auth/me/", payload, format="json")

    def test_valid_update_persists(self):
        resp = self._patch(full_name="Zarrin Operator", language="en", timezone="Europe/Berlin")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Zarrin Operator")
        self.assertEqual(self.user.language, "en")
        self.assertEqual(self.user.timezone, "Europe/Berlin")

    def test_unsupported_language_is_a_clean_400(self):
        resp = self._patch(language="zz")
        self.assertEqual(resp.status_code, 400)
        details = resp.json()["error"]["details"]
        self.assertIn("language", details)

    def test_over_long_full_name_is_a_clean_400_not_500(self):
        resp = self._patch(full_name="x" * 256)
        self.assertEqual(resp.status_code, 400)
        details = resp.json()["error"]["details"]
        self.assertIn("full_name", details)

    def test_invalid_timezone_is_rejected(self):
        resp = self._patch(timezone="Mars/Olympus")
        self.assertEqual(resp.status_code, 400)
        details = resp.json()["error"]["details"]
        self.assertIn("timezone", details)

    def test_disallowed_fields_are_ignored(self):
        """The endpoint must never let a user flip auth-relevant flags."""
        resp = self._patch(is_superuser=True, language="en")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_superuser)
