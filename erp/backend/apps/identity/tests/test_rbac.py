"""RBAC / permission-enforcement tests."""

from __future__ import annotations

from django.test import TestCase

from apps.core.tests.factories import auth_client, grant, make_superuser, make_user


class RBACTests(TestCase):
    def test_permission_code_derives_module(self):
        from apps.identity.models import Permission

        perm = Permission.objects.create(code="sales.order.approve")
        self.assertEqual(perm.module, "sales")

    def test_user_without_permission_is_forbidden(self):
        user = make_user()
        resp = auth_client(user).post(
            "/api/v1/organization/companies/",
            {"code": "C1", "name_en": "A", "name_fa": "الف"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()["error"]["type"], "AuthorizationError")

    def test_user_with_permission_allowed(self):
        user = make_user()
        grant(user, "organization.company.manage", "organization.company.view")
        resp = auth_client(user).post(
            "/api/v1/organization/companies/",
            {"code": "C1", "name_en": "A", "name_fa": "الف"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)

    def test_superuser_bypasses_rbac(self):
        admin = make_superuser()
        resp = auth_client(admin).post(
            "/api/v1/organization/companies/",
            {"code": "C9", "name_en": "Z", "name_fa": "ز"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)

    def test_permission_codes_collected_from_roles(self):
        user = make_user()
        grant(user, "audit.log.view")
        self.assertIn("audit.log.view", user.permission_codes())
        self.assertTrue(user.has_permission_code("audit.log.view"))
        self.assertFalse(user.has_permission_code("audit.log.delete"))
