"""Procurement tests: requisition & purchase-order documents, status state
machine, DRAFT-only editability, RBAC.

Covers the CONFIRMED commercial-document layer only — manual document numbers,
the guarded status transitions (submit/approve/reject/cancel for requisitions;
approve/send/close/cancel for orders), line-editable-only-while-DRAFT, and
permission gating. NO goods receipt / MRP / FX / valuation / invoice layer
exists to test, by design (gated on Q-046 and later phases).
"""

from __future__ import annotations

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.catalog.models import Material, MaterialSubtype, UnitOfMeasure, UomDimension
from apps.core.tests.factories import auth_client, grant, make_company, make_user
from apps.partners.models import Partner, Supplier
from apps.procurement.models import PurchaseOrder, PurchaseRequisition


def build_prereqs(company):
    """Minimal supplier + material + uom prerequisites."""
    uom = UnitOfMeasure.objects.create(code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS)
    material = Material.objects.create(
        company=company,
        code="RESIN-1",
        name_fa="گرانول",
        subtype=MaterialSubtype.RESIN_MASTERBATCH,
        base_uom=uom,
    )
    partner = Partner.objects.create(
        company=company, code="S-001", name_fa="تأمین‌کننده", is_supplier=True
    )
    supplier = Supplier.objects.create(partner=partner, is_approved=True)
    return {"uom": uom, "material": material, "supplier": supplier}


class PurchaseRequisitionTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)
        self.user = make_user()
        grant(
            self.user,
            "procurement.requisition.view",
            "procurement.requisition.manage",
        )
        self.client = auth_client(self.user)

    def _create_pr(self, number="PR-1"):
        return self.client.post(
            "/api/v1/procurement/requisitions/",
            {"company": str(self.company.id), "number": number},
            format="json",
        )

    def test_create_requisition_persists_and_audits(self):
        resp = self._create_pr()
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["status"], "DRAFT")
        pr = PurchaseRequisition.objects.get(number="PR-1")
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="procurement.PurchaseRequisition",
                entity_id=str(pr.id),
            ).exists()
        )

    def test_duplicate_number_per_company_rejected(self):
        self._create_pr()
        dup = self._create_pr()
        self.assertEqual(dup.status_code, 400, dup.content)

    def test_status_is_read_only_on_create(self):
        resp = self.client.post(
            "/api/v1/procurement/requisitions/",
            {"company": str(self.company.id), "number": "PR-9", "status": "APPROVED"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["status"], "DRAFT")

    def test_lifecycle_submit_then_approve_audits(self):
        pid = self._create_pr().data["id"]
        s = self.client.post(f"/api/v1/procurement/requisitions/{pid}/submit/")
        self.assertEqual(s.status_code, 200, s.content)
        self.assertEqual(s.data["status"], "SUBMITTED")
        a = self.client.post(f"/api/v1/procurement/requisitions/{pid}/approve/")
        self.assertEqual(a.status_code, 200, a.content)
        self.assertEqual(a.data["status"], "APPROVED")
        self.assertTrue(
            AuditLog.objects.filter(
                action="UPDATE",
                entity_type="procurement.PurchaseRequisition",
                entity_id=pid,
            ).exists()
        )

    def test_invalid_transition_rejected(self):
        pid = self._create_pr().data["id"]
        # Cannot approve straight from DRAFT (must be SUBMITTED).
        a = self.client.post(f"/api/v1/procurement/requisitions/{pid}/approve/")
        self.assertEqual(a.status_code, 409, a.content)

    def test_line_editable_only_while_draft(self):
        pid = self._create_pr().data["id"]
        line = {
            "requisition": pid,
            "sequence": 1,
            "material": str(self.p["material"].id),
            "quantity": "100.000000",
            "uom": str(self.p["uom"].id),
        }
        ok = self.client.post("/api/v1/procurement/requisition-lines/", line, format="json")
        self.assertEqual(ok.status_code, 201, ok.content)
        self.client.post(f"/api/v1/procurement/requisitions/{pid}/submit/")
        blocked = self.client.post(
            "/api/v1/procurement/requisition-lines/",
            {**line, "sequence": 2},
            format="json",
        )
        self.assertEqual(blocked.status_code, 409, blocked.content)

    def test_header_not_editable_after_submit(self):
        pid = self._create_pr().data["id"]
        self.client.post(f"/api/v1/procurement/requisitions/{pid}/submit/")
        patched = self.client.patch(
            f"/api/v1/procurement/requisitions/{pid}/",
            {"notes": "late edit"},
            format="json",
        )
        self.assertEqual(patched.status_code, 409, patched.content)

    def test_line_material_must_belong_to_requisition_company(self):
        # A material from another company must never leak onto this requisition.
        other_company = make_company(code="OTHERCO")
        other_material = Material.objects.create(
            company=other_company,
            code="RESIN-X",
            name_fa="گرانول دیگر",
            subtype=MaterialSubtype.RESIN_MASTERBATCH,
            base_uom=self.p["uom"],
        )
        pid = self._create_pr().data["id"]
        resp = self.client.post(
            "/api/v1/procurement/requisition-lines/",
            {
                "requisition": pid,
                "sequence": 1,
                "material": str(other_material.id),
                "quantity": "100.000000",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("material", resp.data["error"]["details"])


class PurchaseOrderTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)
        self.user = make_user()
        grant(self.user, "procurement.order.view", "procurement.order.manage")
        self.client = auth_client(self.user)

    def _create_po(self, number="PO-1"):
        return self.client.post(
            "/api/v1/procurement/orders/",
            {
                "company": str(self.company.id),
                "number": number,
                "supplier": str(self.p["supplier"].id),
            },
            format="json",
        )

    def test_create_order_defaults_currency_and_audits(self):
        resp = self._create_po()
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["status"], "DRAFT")
        self.assertEqual(resp.data["currency"], "IRR")
        po = PurchaseOrder.objects.get(number="PO-1")
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="procurement.PurchaseOrder",
                entity_id=str(po.id),
            ).exists()
        )

    def test_duplicate_number_per_company_rejected(self):
        self._create_po()
        dup = self._create_po()
        self.assertEqual(dup.status_code, 400, dup.content)

    def test_lifecycle_approve_send_close(self):
        pid = self._create_po().data["id"]
        a = self.client.post(f"/api/v1/procurement/orders/{pid}/approve/")
        self.assertEqual(a.data["status"], "APPROVED", a.content)
        s = self.client.post(f"/api/v1/procurement/orders/{pid}/send/")
        self.assertEqual(s.data["status"], "SENT", s.content)
        c = self.client.post(f"/api/v1/procurement/orders/{pid}/close/")
        self.assertEqual(c.data["status"], "CLOSED", c.content)

    def test_cannot_send_before_approve(self):
        pid = self._create_po().data["id"]
        s = self.client.post(f"/api/v1/procurement/orders/{pid}/send/")
        self.assertEqual(s.status_code, 409, s.content)

    def test_cancel_from_draft(self):
        pid = self._create_po().data["id"]
        c = self.client.post(f"/api/v1/procurement/orders/{pid}/cancel/")
        self.assertEqual(c.status_code, 200, c.content)
        self.assertEqual(c.data["status"], "CANCELLED")

    def test_order_line_unit_price_optional_and_editable_only_while_draft(self):
        pid = self._create_po().data["id"]
        line = {
            "order": pid,
            "sequence": 1,
            "material": str(self.p["material"].id),
            "quantity": "500.000000",
            "uom": str(self.p["uom"].id),
        }
        ok = self.client.post("/api/v1/procurement/order-lines/", line, format="json")
        self.assertEqual(ok.status_code, 201, ok.content)
        self.assertIsNone(ok.data["unit_price"])
        self.client.post(f"/api/v1/procurement/orders/{pid}/approve/")
        blocked = self.client.post(
            "/api/v1/procurement/order-lines/",
            {**line, "sequence": 2},
            format="json",
        )
        self.assertEqual(blocked.status_code, 409, blocked.content)

    def test_order_line_material_must_belong_to_order_company(self):
        other_company = make_company(code="OTHERCO")
        other_material = Material.objects.create(
            company=other_company,
            code="RESIN-X",
            name_fa="گرانول دیگر",
            subtype=MaterialSubtype.RESIN_MASTERBATCH,
            base_uom=self.p["uom"],
        )
        pid = self._create_po().data["id"]
        resp = self.client.post(
            "/api/v1/procurement/order-lines/",
            {
                "order": pid,
                "sequence": 1,
                "material": str(other_material.id),
                "quantity": "500.000000",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("material", resp.data["error"]["details"])


class ProcurementPermissionTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)

    def test_view_only_cannot_create_requisition(self):
        user = make_user(email="viewer@slz.test")
        grant(user, "procurement.requisition.view")
        client = auth_client(user)
        resp = client.post(
            "/api/v1/procurement/requisitions/",
            {"company": str(self.company.id), "number": "PR-X"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_unpermitted_user_cannot_list_orders(self):
        client = auth_client(make_user(email="nobody@slz.test"))
        resp = client.get("/api/v1/procurement/orders/")
        self.assertEqual(resp.status_code, 403, resp.content)
