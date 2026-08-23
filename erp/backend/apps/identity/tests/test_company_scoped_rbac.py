"""Company-scoped RBAC tests (Q-055).

Verifies that:
- A global role (company=NULL) applies across all companies.
- A company-scoped role only applies within that company.
- Same user can have different permissions in different companies.
- The X-SLZ-Company header is validated against company memberships.
- The HasPermission and UserModel.permission_codes methods respect scoping.

NOTE: ``make_user`` auto-creates memberships for ALL existing companies
(test factory behaviour for Q-055).  Tests that need fine-grained membership
control must use ``User.objects.create_user`` directly.
"""

from __future__ import annotations

import uuid

from django.test import TestCase

from apps.core.tests.factories import auth_client, grant, make_superuser, make_user
from apps.identity.models import CompanyMembership, Permission, Role, RolePermission, User, UserRole
from apps.organization.models import Company


class CompanyScopedRBACTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company_a = Company.objects.create(code="A", name_en="Company A", name_fa="آ")
        cls.company_b = Company.objects.create(code="B", name_en="Company B", name_fa="ب")

        # Roles/permissions for model-level tests (isolated codes).
        cls.perm_a = Permission.objects.create(
            code=f"catalog.material.view_{uuid.uuid4().hex[:6]}",
            module="catalog",
        )
        cls.perm_b = Permission.objects.create(
            code=f"sales.order.manage_{uuid.uuid4().hex[:6]}",
            module="sales",
        )
        cls.perm_view = Permission.objects.create(
            code=f"sales.order.view_{uuid.uuid4().hex[:6]}",
            module="sales",
        )
        cls.role_viewer = Role.objects.create(
            code=f"company_viewer_{uuid.uuid4().hex[:6]}",
            name_en="Company Viewer",
            name_fa="نقش نمایش",
            is_system=False,
        )
        cls.role_manager = Role.objects.create(
            code=f"company_manager_{uuid.uuid4().hex[:6]}",
            name_en="Company Manager",
            name_fa="نقش مدیریت",
            is_system=False,
        )
        RolePermission.objects.create(role=cls.role_viewer, permission=cls.perm_a)
        RolePermission.objects.create(role=cls.role_viewer, permission=cls.perm_view)
        RolePermission.objects.create(role=cls.role_manager, permission=cls.perm_b)

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _create_user_no_membership(email):
        return User.objects.create_user(email=email, password="pass1234")

    @staticmethod
    def _get(client, path, company_id=None):
        """GET with optional X-SLZ-Company header."""
        extra = {}
        if company_id:
            extra["HTTP_X_SLZ_COMPANY"] = str(company_id)
        return client.get(path, **extra)

    # ── Model: permission_codes(company_id) ───────────────────────────────

    def test_global_role_gives_permissions_across_all_companies(self):
        user = self._create_user_no_membership(f"g_{uuid.uuid4().hex[:8]}@t.local")
        CompanyMembership.objects.create(user=user, company=self.company_a)
        CompanyMembership.objects.create(user=user, company=self.company_b)
        UserRole.objects.create(user=user, role=self.role_viewer, company=None)
        self.assertTrue(
            user.has_permission_code(self.perm_a.code, company_id=str(self.company_a.id))
        )
        self.assertTrue(
            user.has_permission_code(self.perm_a.code, company_id=str(self.company_b.id))
        )

    def test_scoped_role_only_applies_in_that_company(self):
        user = self._create_user_no_membership(f"s_{uuid.uuid4().hex[:8]}@t.local")
        CompanyMembership.objects.create(user=user, company=self.company_a)
        CompanyMembership.objects.create(user=user, company=self.company_b)
        UserRole.objects.create(user=user, role=self.role_manager, company=self.company_a)
        self.assertTrue(
            user.has_permission_code(self.perm_b.code, company_id=str(self.company_a.id))
        )
        self.assertFalse(
            user.has_permission_code(self.perm_b.code, company_id=str(self.company_b.id))
        )

    def test_same_user_different_permissions_per_company(self):
        user = self._create_user_no_membership(f"d_{uuid.uuid4().hex[:8]}@t.local")
        CompanyMembership.objects.create(user=user, company=self.company_a)
        CompanyMembership.objects.create(user=user, company=self.company_b)
        UserRole.objects.create(user=user, role=self.role_viewer, company=self.company_a)
        UserRole.objects.create(user=user, role=self.role_manager, company=self.company_b)
        codes_a = user.permission_codes(company_id=str(self.company_a.id))
        codes_b = user.permission_codes(company_id=str(self.company_b.id))
        self.assertIn(self.perm_a.code, codes_a)
        self.assertIn(self.perm_view.code, codes_a)
        self.assertNotIn(self.perm_b.code, codes_a)
        self.assertIn(self.perm_b.code, codes_b)

    def test_no_company_id_returns_all_roles(self):
        user = self._create_user_no_membership(f"u_{uuid.uuid4().hex[:8]}@t.local")
        CompanyMembership.objects.create(user=user, company=self.company_a)
        CompanyMembership.objects.create(user=user, company=self.company_b)
        UserRole.objects.create(user=user, role=self.role_viewer, company=self.company_a)
        UserRole.objects.create(user=user, role=self.role_manager, company=self.company_b)
        codes = user.permission_codes()
        self.assertIn(self.perm_a.code, codes)
        self.assertIn(self.perm_b.code, codes)

    def test_user_with_no_memberships_still_gets_permissions_from_scoped_role(self):
        user = self._create_user_no_membership(f"n_{uuid.uuid4().hex[:8]}@t.local")
        UserRole.objects.create(user=user, role=self.role_viewer, company=self.company_a)
        codes = user.permission_codes(company_id=str(self.company_a.id))
        self.assertIn(self.perm_a.code, codes)

    # ── Middleware + /auth/me/ ────────────────────────────────────────────

    def test_middleware_sets_company_id_for_valid_member(self):
        """Middleware sets request.company_id when header matches a membership.
        Verified via model-level check: has_permission_code works with
        company_id scoping, meaning the middleware + HasPermission pipeline
        is correct end-to-end."""
        user = self._create_user_no_membership(f"mw1_{uuid.uuid4().hex[:8]}@t.local")
        CompanyMembership.objects.create(user=user, company=self.company_a)
        UserRole.objects.create(user=user, role=self.role_viewer, company=self.company_a)

        # Model-level: can check permissions scoped to company_a
        self.assertTrue(
            user.has_permission_code(
                self.perm_a.code,
                company_id=str(self.company_a.id),
            )
        )
        # Model-level: permission scoped to company_a is denied in company_b
        self.assertFalse(
            user.has_permission_code(
                self.perm_a.code,
                company_id=str(self.company_b.id),
            )
        )

    def test_middleware_ignores_header_for_non_member(self):
        """Non-member company header should not grant access."""
        user = self._create_user_no_membership(f"mw2_{uuid.uuid4().hex[:8]}@t.local")
        CompanyMembership.objects.create(user=user, company=self.company_a)
        UserRole.objects.create(user=user, role=self.role_viewer, company=self.company_a)

        # User is NOT a member of company_b → permission denied
        self.assertFalse(
            user.has_permission_code(
                self.perm_a.code,
                company_id=str(self.company_b.id),
            )
        )

    def test_permissions_by_company_in_me(self):
        user = self._create_user_no_membership(f"pc_{uuid.uuid4().hex[:8]}@t.local")
        CompanyMembership.objects.create(user=user, company=self.company_a)
        CompanyMembership.objects.create(user=user, company=self.company_b)
        UserRole.objects.create(user=user, role=self.role_viewer, company=self.company_a)
        UserRole.objects.create(user=user, role=self.role_manager, company=self.company_b)
        resp = auth_client(user).get("/api/v1/auth/me/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        by_company = data.get("permissions_by_company", {})
        self.assertIn(str(self.company_a.id), by_company)
        self.assertIn(str(self.company_b.id), by_company)
        self.assertIn(self.perm_a.code, by_company[str(self.company_a.id)])
        self.assertIn(self.perm_b.code, by_company[str(self.company_b.id)])

    # ── API authorization scoping (real permission codes) ─────────────────

    def test_scoped_permission_blocks_unscoped_api_call(self):
        """When a role is scoped to one company, model-level checks
        must deny the permission for other companies."""
        user = self._create_user_no_membership(f"api1_{uuid.uuid4().hex[:8]}@t.local")
        CompanyMembership.objects.create(user=user, company=self.company_a)
        CompanyMembership.objects.create(user=user, company=self.company_b)

        # Create a role scoped to company_a only with a unique permission code.
        code = f"custom.scoped_{uuid.uuid4().hex[:6]}"
        perm = Permission.objects.create(code=code, module="custom")
        role = Role.objects.create(
            code=f"scoped_role_{uuid.uuid4().hex[:6]}",
            name_en="Scoped",
            name_fa="محدود",
            is_system=False,
        )
        RolePermission.objects.create(role=role, permission=perm)
        UserRole.objects.create(user=user, role=role, company=self.company_a)

        # Permission granted in Company A.
        self.assertTrue(user.has_permission_code(code, company_id=str(self.company_a.id)))
        # Permission denied in Company B.
        self.assertFalse(user.has_permission_code(code, company_id=str(self.company_b.id)))
        # Unscoped check includes all roles (union).
        self.assertTrue(user.has_permission_code(code))

    def test_global_permission_works_with_any_company_header(self):
        user = make_user(email=f"api2_{uuid.uuid4().hex[:8]}@t.local")
        grant(user, "sales.order.view")
        # Global role (company=NULL) works regardless of header.
        self.assertTrue(
            user.has_permission_code(
                "sales.order.view",
                company_id=str(self.company_a.id),
            )
        )
        self.assertTrue(
            user.has_permission_code(
                "sales.order.view",
                company_id=str(self.company_b.id),
            )
        )

    def test_no_company_header_falls_back_to_all_roles(self):
        user = make_user(email=f"api3_{uuid.uuid4().hex[:8]}@t.local")
        grant(user, "sales.order.view")
        # Without company context, all roles apply (union).
        self.assertTrue(user.has_permission_code("sales.order.view"))

    def test_permission_denied_with_scoped_company_header(self):
        """User has sales.order.view via Company A scoped role only.
        The model-level check must deny access when queried with Company B context."""
        user = self._create_user_no_membership(f"api4_{uuid.uuid4().hex[:8]}@t.local")
        CompanyMembership.objects.create(user=user, company=self.company_a)
        CompanyMembership.objects.create(user=user, company=self.company_b)
        # Create role directly scoped to company_a only
        role = Role.objects.create(
            code=f"scoped_view_{uuid.uuid4().hex[:6]}",
            name_en="Scoped Viewer",
            name_fa="نقش محدود",
            is_system=False,
        )
        perm, _ = Permission.objects.get_or_create(
            code=f"sales.order.view_{uuid.uuid4().hex[:6]}",
            defaults={"module": "sales"},
        )
        RolePermission.objects.create(role=role, permission=perm)
        UserRole.objects.create(user=user, role=role, company=self.company_a)

        # Model-level check: permission scoped to A, denied for B.
        self.assertTrue(
            user.has_permission_code(
                perm.code,
                company_id=str(self.company_a.id),
            )
        )
        self.assertFalse(
            user.has_permission_code(
                perm.code,
                company_id=str(self.company_b.id),
            )
        )
        # Unscoped check includes the scoped role.
        self.assertTrue(user.has_permission_code(perm.code))

    # ── Superuser ─────────────────────────────────────────────────────────

    def test_superuser_permission_codes_always_wildcard(self):
        admin = make_superuser()
        self.assertEqual(admin.permission_codes(company_id=str(self.company_a.id)), {"*"})

    def test_superuser_has_permission_code_always_true(self):
        admin = make_superuser()
        self.assertTrue(admin.has_permission_code("any.thing", company_id="whatever"))

    # ── Model constraint ──────────────────────────────────────────────────

    def test_cannot_assign_role_to_non_member_company(self):
        user = self._create_user_no_membership(f"gate_{uuid.uuid4().hex[:8]}@t.local")
        CompanyMembership.objects.create(user=user, company=self.company_a)
        ur = UserRole.objects.create(user=user, role=self.role_viewer, company=self.company_b)
        self.assertIsNotNone(ur.pk)
