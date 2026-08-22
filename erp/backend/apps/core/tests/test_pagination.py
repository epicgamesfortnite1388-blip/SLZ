"""Tests for the standard pagination envelope and page-size cap.

Every list endpoint in the platform uses ``StandardPagination``; these tests
pin the envelope contract the frontend depends on (``count`` / ``total_pages``
/ ``page`` / ``page_size`` / next / previous / ``results``) and the
``page_size`` clamp. The permission catalogue endpoint is used as the fixture
surface because it is public to superusers and cheap to seed.
"""

from __future__ import annotations

from django.test import TestCase

from apps.core.pagination import StandardPagination
from apps.core.tests.factories import auth_client, make_superuser
from apps.identity.models import Permission


class StandardPaginationTests(TestCase):
    URL = "/api/v1/auth/permissions/"

    def setUp(self):
        self.client = auth_client(make_superuser())

    def _seed(self, n):
        for i in range(n):
            Permission.objects.create(code=f"m.res{i}.view", module="m")

    def test_envelope_shape_and_counts(self):
        self._seed(5)
        resp = self.client.get(self.URL, {"page_size": 2})
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(
            set(resp.data.keys()),
            {"count", "total_pages", "page", "page_size", "next", "previous", "results"},
        )
        self.assertEqual(resp.data["count"], 5)
        self.assertEqual(resp.data["total_pages"], 3)
        self.assertEqual(resp.data["page"], 1)
        self.assertEqual(resp.data["page_size"], 2)
        self.assertIsNotNone(resp.data["next"])
        self.assertIsNone(resp.data["previous"])
        self.assertEqual(len(resp.data["results"]), 2)

    def test_second_page_navigation(self):
        self._seed(3)
        resp = self.client.get(self.URL, {"page": 2, "page_size": 2})
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["page"], 2)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertIsNone(resp.data["next"])
        self.assertIsNotNone(resp.data["previous"])

    def test_oversize_page_size_never_bypasses_the_cap(self):
        """A huge page_size must never return more than max_page_size rows."""
        self._seed(StandardPagination.max_page_size + 50)
        resp = self.client.get(self.URL, {"page_size": StandardPagination.max_page_size * 10})
        if resp.status_code == 200:
            self.assertLessEqual(len(resp.data["results"]), StandardPagination.max_page_size)
        else:
            # Some configurations reject instead of clamping.
            self.assertIn(resp.status_code, (400, 404))
