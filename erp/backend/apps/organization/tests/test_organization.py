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
from apps.organization.models import Company, Site


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
