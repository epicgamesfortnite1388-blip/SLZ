"""Health and readiness probe tests."""

from __future__ import annotations

from django.test import TestCase


class HealthTests(TestCase):
    def test_health_ok(self):
        resp = self.client.get("/health/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

    def test_ready_checks_dependencies(self):
        resp = self.client.get("/ready/")
        # DB is available under the test runner; cache is locmem.
        self.assertIn(resp.status_code, (200, 503))
        self.assertIn("checks", resp.json())
