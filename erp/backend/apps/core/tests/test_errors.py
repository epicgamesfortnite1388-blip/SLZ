"""Error-envelope / exception-handler tests."""

from __future__ import annotations

from django.test import TestCase
from rest_framework.test import APIClient

from apps.core.tests.factories import grant, make_user


class ErrorEnvelopeTests(TestCase):
    def test_unauthenticated_returns_authentication_error(self):
        client = APIClient()
        resp = client.get("/api/v1/organization/companies/")
        self.assertEqual(resp.status_code, 401)
        body = resp.json()
        self.assertEqual(body["error"]["type"], "AuthenticationError")
        self.assertIn("correlation_id", body["error"])

    def test_not_found_envelope(self):
        user = make_user()
        grant(user, "organization.company.view")
        client = APIClient()
        client.force_authenticate(user)
        resp = client.get("/api/v1/organization/companies/00000000-0000-0000-0000-000000000000/")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"]["type"], "NotFoundError")

    def test_correlation_id_header_echoed(self):
        client = APIClient()
        resp = client.get("/health/", HTTP_X_CORRELATION_ID="abc123")
        self.assertEqual(resp["X-Correlation-ID"], "abc123")
