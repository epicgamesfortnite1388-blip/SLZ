"""Regression tests for the brute-force throttle on unauthenticated auth
endpoints (login / token refresh).

Before this guard the endpoints accepted unlimited attempts per IP. These tests
pin that: after the configured number of attempts within the window, further
attempts get a standardized 429 envelope (``ThrottledError``) with DRF's
``Retry-After`` header preserved.

The rate is pinned by a test-local throttle subclass with an explicit class
``rate`` (bypassing the settings lookup), so the test is deterministic and does
not depend on ``override_settings`` propagating into DRF's api_settings cache.
"""

from __future__ import annotations

from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from apps.core.tests.factories import make_user
from apps.identity.views import AuthAnonThrottle, LoginView, RefreshView


class TwoPerMinute(AuthAnonThrottle):
    rate = "2/min"


class AuthThrottleTests(TestCase):
    """Runs every test with both auth views throttled to 2 requests/minute."""

    def setUp(self):
        # Throttle history lives in the (locmem) cache; isolate each test.
        cache.clear()
        self.user = make_user(email="victim@slz.test")
        self.user.set_password("correct-horse")
        self.user.save()

    def run(self, result=None):
        with (
            patch.object(LoginView, "throttle_classes", [TwoPerMinute]),
            patch.object(RefreshView, "throttle_classes", [TwoPerMinute]),
        ):
            return super().run(result)

    def _login(self, password):
        return self.client.post(
            "/api/v1/auth/login/",
            {"email": self.user.email, "password": password},
            content_type="application/json",
        )

    def test_attempts_within_rate_succeed_or_401_normally(self):
        first = self._login("wrong")
        second = self._login("wrong")
        self.assertEqual(first.status_code, 401)
        self.assertEqual(second.status_code, 401)

    def test_third_attempt_is_throttled_with_envelope_and_header(self):
        self._login("wrong")
        self._login("wrong")
        third = self._login("wrong")

        self.assertEqual(third.status_code, 429, third.content)
        payload = third.json()
        self.assertEqual(payload["error"]["type"], "ThrottledError")
        self.assertIn("Retry-After", third)

    def test_correct_credentials_are_also_throttled(self):
        """Throttling is per-IP before authentication: a valid login beyond the
        rate is rejected too — credential correctness cannot bypass it."""
        ok = self._login("correct-horse")
        self.assertEqual(ok.status_code, 200)
        self._login("wrong")
        throttled = self._login("correct-horse")
        self.assertEqual(throttled.status_code, 429)

    def test_refresh_endpoint_is_throttled_under_the_same_scope(self):
        for _ in range(2):
            resp = self.client.post(
                "/api/v1/auth/refresh/",
                {"refresh": "not-a-real-token"},
                content_type="application/json",
            )
            self.assertEqual(resp.status_code, 401)
        third = self.client.post(
            "/api/v1/auth/refresh/",
            {"refresh": "not-a-real-token"},
            content_type="application/json",
        )
        self.assertEqual(third.status_code, 429, third.content)


class ThrottleWiringTests(TestCase):
    """The 'auth' scope must stay wired to a configured rate: an unconfigured
    scope would raise ImproperlyConfigured on the first real login request."""

    def test_production_scope_resolves_to_a_rate(self):
        # Runs outside the per-test patching above; reads real settings.
        throttle = AuthAnonThrottle()
        num_requests, duration = throttle.parse_rate(throttle.get_rate())
        self.assertGreaterEqual(num_requests, 1)
        self.assertGreater(duration, 0)
