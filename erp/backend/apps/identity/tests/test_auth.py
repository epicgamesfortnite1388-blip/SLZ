"""Authentication flow tests: login, me, logout."""

from __future__ import annotations

from django.test import TestCase
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.core.tests.factories import make_user


class AuthTests(TestCase):
    def setUp(self):
        self.password = "s3cret-pass"
        self.user = make_user(email="alice@slz.test", password=self.password)
        self.client = APIClient()

    def test_login_returns_tokens_and_user(self):
        resp = self.client.post(
            "/api/v1/auth/login/",
            {"email": "alice@slz.test", "password": self.password},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertIn("access", body)
        self.assertIn("refresh", body)
        self.assertEqual(body["user"]["email"], "alice@slz.test")
        self.assertTrue(
            AuditLog.objects.filter(action="LOGIN", entity_id=str(self.user.pk)).exists()
        )

    def test_login_bad_credentials(self):
        resp = self.client.post(
            "/api/v1/auth/login/",
            {"email": "alice@slz.test", "password": "wrong"},
            format="json",
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["error"]["type"], "AuthenticationError")

    def test_me_requires_auth(self):
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)

    def test_me_returns_profile(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/v1/auth/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["email"], "alice@slz.test")

    def test_me_patch_updates_locale(self):
        self.client.force_authenticate(self.user)
        resp = self.client.patch("/api/v1/auth/me/", {"language": "en"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["language"], "en")
