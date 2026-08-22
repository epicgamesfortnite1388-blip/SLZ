"""Regression tests for error-envelope quality in the standardized handler.

``AuthenticationFailed`` raised with a dict detail (SimpleJWT's shape for an
invalid/expired refresh token) used to leak a Python repr into the
client-facing ``message`` — e.g. ``"{'detail': ErrorDetail('Token is invalid
or expired', code='token_not_valid'), …}"``. These tests pin the flattened,
readable message and the documented envelope shape.
"""

from __future__ import annotations

from django.test import TestCase


class RefreshErrorEnvelopeTests(TestCase):
    def _refresh(self, token="not-a-real-token"):
        return self.client.post(
            "/api/v1/auth/refresh/",
            {"refresh": token},
            content_type="application/json",
        )

    def test_invalid_refresh_token_message_is_readable(self):
        resp = self._refresh()
        self.assertEqual(resp.status_code, 401)
        envelope = resp.json()["error"]
        self.assertEqual(envelope["type"], "AuthenticationError")
        message = envelope["message"]
        self.assertNotIn("ErrorDetail", message)
        self.assertNotIn("{'", message)
        self.assertIn("Token is invalid or expired", message)

    def test_missing_body_still_returns_standard_envelope(self):
        resp = self.client.post(
            "/api/v1/auth/refresh/",
            {},
            content_type="application/json",
        )
        # A missing `refresh` field is a shape error, not an auth failure.
        self.assertEqual(resp.status_code, 400)
        envelope = resp.json()["error"]
        self.assertEqual(envelope["type"], "ValidationError")
