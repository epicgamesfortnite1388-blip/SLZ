"""Partners master-data tests: API CRUD, RBAC, DB constraints, audit."""

from __future__ import annotations

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.core.tests.factories import auth_client, grant, make_company, make_user
from apps.partners.models import Partner


class PartnerApiTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.user = make_user()
        grant(self.user, "partners.partner.view", "partners.partner.manage")
        self.client = auth_client(self.user)

    def _payload(self, **overrides):
        data = {
            "company": str(self.company.id),
            "code": "CUST-001",
            "name_fa": "مشتری یک",
            "name_en": "Customer One",
            "is_customer": True,
        }
        data.update(overrides)
        return data

    def test_create_partner_persists_and_audits(self):
        resp = self.client.post("/api/v1/partners/partners/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        partner = Partner.objects.get(code="CUST-001")
        # created_by is populated by the audited service layer.
        self.assertEqual(partner.created_by_id, self.user.id)
        # The write emitted an EntityCreated -> audit CREATE row.
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="partners.Partner",
                entity_id=str(partner.id),
            ).exists()
        )

    def test_partner_requires_at_least_one_role(self):
        resp = self.client.post(
            "/api/v1/partners/partners/",
            self._payload(is_customer=False, is_supplier=False),
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_partner_code_unique_per_company(self):
        self.client.post("/api/v1/partners/partners/", self._payload(), format="json")
        dup = self.client.post("/api/v1/partners/partners/", self._payload(), format="json")
        self.assertEqual(dup.status_code, 400, dup.content)

    def test_delete_is_soft_and_audited(self):
        create = self.client.post("/api/v1/partners/partners/", self._payload(), format="json")
        pk = create.json()["id"]
        resp = self.client.delete(f"/api/v1/partners/partners/{pk}/")
        self.assertEqual(resp.status_code, 204, resp.content)
        # Hidden from the default manager but retained in all_objects (soft delete).
        self.assertFalse(Partner.objects.filter(id=pk).exists())
        self.assertTrue(Partner.all_objects.filter(id=pk).exists())
        self.assertTrue(AuditLog.objects.filter(action="DELETE", entity_id=str(pk)).exists())

    def test_partial_update_persists_and_audits(self):
        """The UI edit flow PATCHes name/roles; the change must persist and land
        in the audit trail with before/after snapshots."""
        create = self.client.post("/api/v1/partners/partners/", self._payload(), format="json")
        pk = create.json()["id"]
        resp = self.client.patch(
            f"/api/v1/partners/partners/{pk}/",
            {"name_en": "Renamed Partner", "is_supplier": True},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        partner = Partner.objects.get(id=pk)
        self.assertEqual(partner.name_en, "Renamed Partner")
        self.assertTrue(partner.is_customer and partner.is_supplier)
        update_row = (
            AuditLog.objects.filter(action="UPDATE", entity_type="partners.Partner", entity_id=pk)
            .order_by("-timestamp")
            .first()
        )
        self.assertIsNotNone(update_row)
        self.assertIsNotNone(update_row.after_state)

    def test_update_cannot_drop_the_last_role(self):
        """PATCHing both role flags off would orphan the partner — same rule as
        create must hold on the update path."""
        create = self.client.post("/api/v1/partners/partners/", self._payload(), format="json")
        pk = create.json()["id"]
        resp = self.client.patch(
            f"/api/v1/partners/partners/{pk}/",
            {"is_customer": False},
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertFalse(Partner.objects.get(id=pk).is_supplier)


class PartnerPermissionTests(TestCase):
    def setUp(self):
        self.company = make_company()

    def test_view_only_user_cannot_create(self):
        user = make_user(email="viewer@slz.test")
        grant(user, "partners.partner.view")
        client = auth_client(user)
        resp = client.post(
            "/api/v1/partners/partners/",
            {
                "company": str(self.company.id),
                "code": "X1",
                "name_fa": "الف",
                "is_supplier": True,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_unpermitted_user_cannot_list(self):
        user = make_user(email="nobody@slz.test")
        client = auth_client(user)
        resp = client.get("/api/v1/partners/partners/")
        self.assertEqual(resp.status_code, 403, resp.content)
