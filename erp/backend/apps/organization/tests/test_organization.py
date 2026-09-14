"""Organization structural master tests (Company / Site).

Company / Site / Department were migrated from a plain ``ModelViewSet`` to the
platform ``AuditedModelViewSet`` so their master-data writes are transactional
and land in the audit trail like every other master-data module. These tests
lock that behavior in: a create must persist, stamp ``created_by`` and emit a
CREATE audit row; a delete must be soft and audited; uniqueness and RBAC hold.
"""

from __future__ import annotations

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.core.tests.factories import auth_client, grant, make_company, make_user
from apps.organization.models import Company, Department, Site


class CompanyApiTests(TestCase):
    def setUp(self):
        self.user = make_user()
        grant(self.user, "organization.company.view", "organization.company.manage")
        self.client = auth_client(self.user)

    def _payload(self, **overrides):
        data = {"code": "ACME", "name_en": "Acme Co", "name_fa": "شرکت آکمه"}
        data.update(overrides)
        return data

    def test_create_company_persists_and_audits(self):
        resp = self.client.post("/api/v1/organization/companies/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        company = Company.objects.get(code="ACME")
        # created_by is populated only by the audited service layer.
        self.assertEqual(company.created_by_id, self.user.id)
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="organization.Company",
                entity_id=str(company.id),
            ).exists()
        )

    def test_company_code_is_unique(self):
        self.client.post("/api/v1/organization/companies/", self._payload(), format="json")
        dup = self.client.post("/api/v1/organization/companies/", self._payload(), format="json")
        self.assertEqual(dup.status_code, 400, dup.content)

    def test_delete_is_soft_and_audited(self):
        create = self.client.post("/api/v1/organization/companies/", self._payload(), format="json")
        pk = create.json()["id"]
        resp = self.client.delete(f"/api/v1/organization/companies/{pk}/")
        self.assertEqual(resp.status_code, 204, resp.content)
        self.assertFalse(Company.objects.filter(id=pk).exists())
        self.assertTrue(Company.all_objects.filter(id=pk).exists())
        self.assertTrue(AuditLog.objects.filter(action="DELETE", entity_id=str(pk)).exists())


class SiteApiTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.user = make_user()
        grant(self.user, "organization.site.view", "organization.site.manage")
        self.client = auth_client(self.user)

    def _payload(self, **overrides):
        data = {
            "company": str(self.company.id),
            "code": "PLANT-1",
            "name_en": "Plant One",
            "name_fa": "کارخانه یک",
        }
        data.update(overrides)
        return data

    def test_create_site_persists_and_audits(self):
        resp = self.client.post("/api/v1/organization/sites/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        site = Site.objects.get(code="PLANT-1")
        self.assertEqual(site.created_by_id, self.user.id)
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="organization.Site",
                entity_id=str(site.id),
            ).exists()
        )

    def test_site_code_unique_per_company(self):
        self.client.post("/api/v1/organization/sites/", self._payload(), format="json")
        dup = self.client.post("/api/v1/organization/sites/", self._payload(), format="json")
        self.assertEqual(dup.status_code, 400, dup.content)


class OrganizationPermissionTests(TestCase):
    def test_view_only_user_cannot_create_company(self):
        user = make_user(email="viewer@slz.test")
        grant(user, "organization.company.view")
        client = auth_client(user)
        resp = client.post(
            "/api/v1/organization/companies/",
            {"code": "X", "name_en": "X", "name_fa": "X"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)


class DepartmentHierarchyValidationTests(TestCase):
    """Hierarchy integrity on create AND update (parent edit flow, 2026-09-14):
    the parent must live on the same site and must never form a cycle — the
    edit UI makes reparenting a routine, user-reachable operation."""

    def setUp(self):
        self.company = make_company()
        self.user = make_user()
        grant(self.user, "organization.department.view", "organization.department.manage")
        self.client = auth_client(self.user)
        self.site_a = Site.objects.create(
            company=self.company, code="SITE-A", name_fa="الف", name_en="A"
        )
        self.site_b = Site.objects.create(
            company=self.company, code="SITE-B", name_fa="ب", name_en="B"
        )

    def _create_department(self, site, code):
        resp = self.client.post(
            "/api/v1/organization/departments/",
            {"site": str(site.id), "code": code, "name_fa": code, "name_en": code},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        return Department.objects.get(code=code, site=site)

    def _details(self, resp):
        """Field-level errors out of the standardized error envelope."""
        return resp.json()["error"]["details"]

    def test_parent_must_belong_to_same_site(self):
        parent = self._create_department(self.site_a, "PROD-A")
        resp = self.client.post(
            "/api/v1/organization/departments/",
            {
                "site": str(self.site_b.id),
                "code": "PACK-B",
                "name_fa": "بسته‌بندی",
                "name_en": "Pack",
                "parent": str(parent.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("parent", self._details(resp))

    def test_department_cannot_be_its_own_parent(self):
        dept = self._create_department(self.site_a, "SELF")
        resp = self.client.patch(
            f"/api/v1/organization/departments/{dept.id}/",
            {"parent": str(dept.id)},
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("parent", self._details(resp))

    def test_two_level_cycle_is_rejected(self):
        a = self._create_department(self.site_a, "CYC-A")
        b = self._create_department(self.site_a, "CYC-B")
        # b.parent = a first (legal), then a.parent = b must fail (A→B→A).
        ok = self.client.patch(
            f"/api/v1/organization/departments/{b.id}/", {"parent": str(a.id)}, format="json"
        )
        self.assertEqual(ok.status_code, 200, ok.content)
        cycle = self.client.patch(
            f"/api/v1/organization/departments/{a.id}/", {"parent": str(b.id)}, format="json"
        )
        self.assertEqual(cycle.status_code, 400, cycle.content)
        self.assertIn("cycle", str(self._details(cycle)))

    def test_legal_deep_chain_builds_and_illegal_reparents_fail(self):
        root = self._create_department(self.site_a, "ROOT")
        mid = self._create_department(self.site_a, "MID")
        leaf = self._create_department(self.site_a, "LEAF")
        # Build a legal chain LEAF→MID→ROOT step by step.
        self.assertEqual(
            self.client.patch(
                f"/api/v1/organization/departments/{mid.id}/",
                {"parent": str(root.id)},
                format="json",
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.patch(
                f"/api/v1/organization/departments/{leaf.id}/",
                {"parent": str(mid.id)},
                format="json",
            ).status_code,
            200,
        )
        # ILLEGAL: ROOT under LEAF would close ROOT→LEAF→MID→ROOT.
        bad = self.client.patch(
            f"/api/v1/organization/departments/{root.id}/", {"parent": str(leaf.id)}, format="json"
        )
        self.assertEqual(bad.status_code, 400, bad.content)
        # ILLEGAL: MID under LEAF would close LEAF→MID→LEAF.
        bad2 = self.client.patch(
            f"/api/v1/organization/departments/{mid.id}/", {"parent": str(leaf.id)}, format="json"
        )
        self.assertEqual(bad2.status_code, 400, bad2.content)
        # LEGAL: clearing a parent (explicit null) still works.
        cleared = self.client.patch(
            f"/api/v1/organization/departments/{leaf.id}/", {"parent": None}, format="json"
        )
        self.assertEqual(cleared.status_code, 200, cleared.content)
        leaf.refresh_from_db()
        self.assertIsNone(leaf.parent_id)
