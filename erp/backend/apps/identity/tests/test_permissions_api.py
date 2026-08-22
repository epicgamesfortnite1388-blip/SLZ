"""RBAC platform tests: the permissions catalogue endpoint and seed_rbac.

The permission list is platform configuration and is explicitly gated by
``identity.permission.view``; these tests pin that gate plus the idempotency
of the ``seed_rbac`` command that provisions the catalogue.
"""

from __future__ import annotations

from django.core.management import call_command
from django.test import TestCase

from apps.core.tests.factories import auth_client, grant, make_superuser, make_user
from apps.identity.models import Permission, Role, RolePermission


class PermissionsEndpointTests(TestCase):
    URL = "/api/v1/auth/permissions/"

    def setUp(self):
        self.viewer = make_user(email="viewer@slz.test")
        grant(self.viewer, "identity.permission.view")
        self.plain = make_user(email="plain@slz.test")
        Permission.objects.get_or_create(code="sales.order.view", defaults={"module": "sales"})
        Permission.objects.get_or_create(code="sales.order.manage", defaults={"module": "sales"})

    def test_requires_the_permission_view_code(self):
        resp = auth_client(self.plain).get(self.URL)
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_granted_user_can_list_and_filter_by_module(self):
        resp = auth_client(self.viewer).get(self.URL, {"module": "sales"})
        self.assertEqual(resp.status_code, 200, resp.content)
        codes = {row["code"] for row in resp.data["results"]}
        self.assertEqual(codes, {"sales.order.view", "sales.order.manage"})

    def test_superuser_bypasses_the_gate(self):
        resp = auth_client(make_superuser()).get(self.URL)
        self.assertEqual(resp.status_code, 200, resp.content)


class SeedRbacCommandTests(TestCase):
    def test_seeds_catalogue_admin_role_and_is_idempotent(self):
        call_command("seed_rbac", verbosity=0)
        expected_codes = {
            "identity.user.view",
            "identity.permission.view",
            "audit.log.view",
            "sales.order.view",
            "production.order.manage",
        }
        for code in expected_codes:
            self.assertTrue(Permission.objects.filter(code=code).exists(), code)

        admin_role = Role.objects.get(code="platform_admin")
        self.assertTrue(admin_role.is_system)
        role_perm_count = RolePermission.objects.filter(role=admin_role).count()
        self.assertEqual(role_perm_count, Permission.objects.count())

        # A second run must not duplicate anything.
        call_command("seed_rbac", verbosity=0)
        self.assertEqual(Permission.objects.filter(code="identity.user.view").count(), 1)
        self.assertEqual(Role.objects.filter(code="platform_admin").count(), 1)
        self.assertEqual(
            RolePermission.objects.filter(role=admin_role).count(),
            Permission.objects.count(),
        )

    def test_no_superuser_created_without_env(self):
        call_command("seed_rbac", verbosity=0)
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.assertFalse(User.objects.filter(is_superuser=True).exists())
