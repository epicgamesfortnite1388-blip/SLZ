"""Goods receipt tests (SR-09 execution slice; Q-049 unit-type policy).

Pins the posting contract of ``create_goods_receipt``:

* atomic creation of receipt + lines + traceability units + IN movements;
* over-receipt protection per PO line;
* material/PO consistency;
* receivable PO statuses (APPROVED / SENT only);
* quarantine destinations rejected;
* company isolation on the receive path.
"""

from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from apps.catalog.models import Material, UnitOfMeasure, UomDimension
from apps.core.tests.factories import auth_client, grant, make_company, make_site, make_user
from apps.inventory.models import (
    StockMovement,
    StockMovementDirection,
    TraceabilityUnit,
    Warehouse,
    WarehouseStoreType,
)
from apps.partners.models import Supplier
from apps.procurement.models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus


class GrnTestBase(TestCase):
    def setUp(self):
        self.company = make_company()
        self.site = make_site(company=self.company)
        self.user = make_user()
        self.uom = UnitOfMeasure.objects.create(
            code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS
        )
        self.material = Material.objects.create(
            company=self.company, code="RM-BOPP", name_fa="BOPP", base_uom=self.uom
        )
        self.warehouse = Warehouse.objects.create(
            company=self.company,
            site=self.site,
            code="RM-01",
            name_fa="انبار مواد",
            store_type=WarehouseStoreType.RAW_MATERIAL,
        )
        from apps.partners.models import Partner

        partner = Partner.objects.create(
            company=self.company, code="SUP-1", name_fa="تأمین‌کننده", is_supplier=True
        )
        self.supplier = Supplier.objects.create(partner=partner, is_approved=True)

    def _make_po(self, status=PurchaseOrderStatus.APPROVED, quantity=Decimal("10")):
        po = PurchaseOrder.objects.create(
            company=self.company,
            site=self.site,
            supplier=self.supplier,
            number="PO-GRN-1",
            status=status,
        )
        line = PurchaseOrderLine.objects.create(
            order=po,
            sequence=1,
            material=self.material,
            quantity=quantity,
            uom=self.uom,
        )
        return po, line

    def _client_with(self, *codes):
        grant(self.user, *codes)
        return auth_client(self.user)

    def _post_grn(
        self,
        client,
        *,
        po=None,
        po_line=None,
        quantity="10",
        warehouse=None,
        number="GRN-1",
        unit_type="BATCH",
        material=None,
        quarantine=False,
    ):
        wh = self._quarantine_wh() if quarantine else (warehouse or self.warehouse)
        payload = {
            "company": str(self.company.id),
            "number": number,
            "received_at": "2026-08-22",
            "warehouse": str(wh.id),
        }
        if po:
            payload["purchase_order"] = str(po.id)
        lines = [
            {
                "material": str((material or self.material).id),
                "quantity": quantity,
                "uom": str(self.uom.id),
                "traceability_unit_type": unit_type,
            }
        ]
        if po_line:
            lines[0]["po_line"] = str(po_line.id)
        payload["lines"] = lines
        return client.post("/api/v1/procurement/goods-receipts/", payload, format="json")

    def _quarantine_wh(self):
        if not hasattr(self, "_quarantine"):
            self._quarantine = Warehouse.objects.create(
                company=self.company,
                site=self.site,
                code="QUA-01",
                name_fa="قرنطینه",
                store_type=WarehouseStoreType.QUARANTINE,
            )
        return self._quarantine


class GoodsReceiptFlowTests(GrnTestBase):
    def test_receipt_creates_unit_movement_and_audit(self):
        po, line = self._make_po()
        client = self._client_with("procurement.grn.view", "procurement.grn.manage")

        resp = client.post(
            "/api/v1/procurement/goods-receipts/",
            {
                "company": str(self.company.id),
                "warehouse": str(self.warehouse.id),
                "supplier": str(self.supplier.id),
                "purchase_order": str(po.id),
                "number": "GRN-100",
                "received_at": "2026-08-22",
                "lines": [
                    {
                        "po_line": str(line.id),
                        "material": str(self.material.id),
                        "quantity": "10",
                        "uom": str(self.uom.id),
                        "traceability_unit_type": "ROLL",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        body = resp.json()
        self.assertEqual(body["status"], "POSTED")
        self.assertEqual(len(body["lines"]), 1)

        # Q-046/Q-049: serialized roll created for film materials.
        unit = TraceabilityUnit.objects.get(pk=body["lines"][0]["traceability_unit"])
        self.assertEqual(unit.unit_type, "ROLL")
        self.assertEqual(unit.quantity, Decimal("10"))

        movement = StockMovement.objects.get(traceability_unit=unit)
        self.assertEqual(movement.direction, StockMovementDirection.IN)
        self.assertEqual(movement.warehouse_id, self.warehouse.id)

        from apps.audit.models import AuditLog

        self.assertTrue(AuditLog.objects.filter(entity_type="procurement.GoodsReceipt").exists())

    def test_over_receipt_is_blocked(self):
        po, line = self._make_po(quantity=Decimal("10"))
        client = self._client_with("procurement.grn.manage")
        first = client.post(
            "/api/v1/procurement/goods-receipts/",
            {
                "company": str(self.company.id),
                "warehouse": str(self.warehouse.id),
                "number": "GRN-A",
                "received_at": "2026-08-22",
                "lines": [
                    {
                        "po_line": str(line.id),
                        "material": str(self.material.id),
                        "quantity": "10",
                        "uom": str(self.uom.id),
                        "traceability_unit_type": "ROLL",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(first.status_code, 201, first.content)

        second = client.post(
            "/api/v1/procurement/goods-receipts/",
            {
                "company": str(self.company.id),
                "warehouse": str(self.warehouse.id),
                "number": "GRN-B",
                "received_at": "2026-08-22",
                "lines": [
                    {
                        "po_line": str(line.id),
                        "material": str(self.material.id),
                        "quantity": "1",
                        "uom": str(self.uom.id),
                        "traceability_unit_type": "ROLL",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(second.status_code, 422)
        self.assertIn("over_receipt", second.json()["error"].get("code", ""))

    def test_partial_receipts_across_multiple_grns_are_allowed(self):
        po, line = self._make_po(quantity=Decimal("10"))
        client = self._client_with("procurement.grn.manage")
        for idx, qty in enumerate(("4", "6")):
            resp = client.post(
                "/api/v1/procurement/goods-receipts/",
                {
                    "company": str(self.company.id),
                    "warehouse": str(self.warehouse.id),
                    "number": f"GRN-P{idx}",
                    "received_at": "2026-08-22",
                    "lines": [
                        {
                            "po_line": str(line.id),
                            "material": str(self.material.id),
                            "quantity": qty,
                            "uom": str(self.uom.id),
                            "traceability_unit_type": "ROLL",
                        }
                    ],
                },
                format="json",
            )
            self.assertEqual(resp.status_code, 201, resp.content)

    def test_material_mismatch_with_po_line_rejected(self):
        other = Material.objects.create(
            company=self.company, code="RM-OTHER", name_fa="دیگر", base_uom=self.uom
        )
        po, line = self._make_po()
        client = self._client_with("procurement.grn.manage")
        resp = client.post(
            "/api/v1/procurement/goods-receipts/",
            {
                "company": str(self.company.id),
                "warehouse": str(self.warehouse.id),
                "purchase_order": str(po.id),
                "number": "GRN-M",
                "received_at": "2026-08-22",
                "lines": [
                    {
                        "po_line": str(line.id),
                        "material": str(other.id),
                        "quantity": "5",
                        "uom": str(self.uom.id),
                        "traceability_unit_type": "ROLL",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 422)

    def test_draft_po_is_not_receivable(self):
        po, line = self._make_po(status=PurchaseOrderStatus.DRAFT)
        client = self._client_with("procurement.grn.manage")
        resp = client.post(
            "/api/v1/procurement/goods-receipts/",
            {
                "company": str(self.company.id),
                "warehouse": str(self.warehouse.id),
                "purchase_order": str(po.id),
                "number": "GRN-D",
                "received_at": "2026-08-22",
                "lines": [
                    {
                        "po_line": str(line.id),
                        "material": str(self.material.id),
                        "quantity": "5",
                        "uom": str(self.uom.id),
                        "traceability_unit_type": "BATCH",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 409)

    def test_quarantine_destination_rejected(self):
        client = self._client_with("procurement.grn.manage")
        resp = self._post_grn(client, quarantine=True)
        self.assertEqual(resp.status_code, 422)

    def test_view_requires_permission_and_manage_gates_posting(self):
        viewer = make_user(email="grn-view@slz.test")
        grant(viewer, "procurement.grn.view")
        poster = make_user(email="grn-post@slz.test")
        grant(poster, "procurement.grn.view", "procurement.grn.manage")

        view_resp = auth_client(viewer).get("/api/v1/procurement/goods-receipts/")
        self.assertEqual(view_resp.status_code, 200)

        post_resp = auth_client(viewer).post(
            "/api/v1/procurement/goods-receipts/", {}, format="json"
        )
        self.assertEqual(post_resp.status_code, 403)

        ok_post = auth_client(poster).get("/api/v1/procurement/goods-receipts/")
        self.assertEqual(ok_post.status_code, 200)


class GrnCompanyIsolationTests(GrnTestBase):
    def test_receive_against_foreign_po_is_blocked(self):
        """A user must not receive against another company's purchase order."""
        foreign_company = make_company(code="BBBB")
        foreign_site = make_site(company=foreign_company)
        foreign_po = PurchaseOrder.objects.create(
            company=foreign_company,
            site=foreign_site,
            supplier=self.supplier,
            number="PO-FGN",
            status=PurchaseOrderStatus.SENT,
        )
        foreign_line = PurchaseOrderLine.objects.create(
            order=foreign_po,
            sequence=1,
            material=self.material,
            quantity=Decimal("50"),
            uom=self.uom,
        )
        # Insider: member of THIS company only.
        insider = make_user(email="iso@slz.test")
        grant(insider, "procurement.grn.view", "procurement.grn.manage")
        from apps.identity.models import CompanyMembership

        CompanyMembership.objects.filter(user=insider).exclude(company=self.company).delete()

        resp = auth_client(insider).post(
            "/api/v1/procurement/goods-receipts/",
            {
                "company": str(self.company.id),
                "warehouse": str(self.warehouse.id),
                "number": "GRN-ISO",
                "received_at": "2026-08-22",
                "purchase_order": str(foreign_po.id),
                "lines": [
                    {
                        "po_line": str(foreign_line.id),
                        "material": str(self.material.id),
                        "quantity": "5",
                        "uom": str(self.uom.id),
                        "traceability_unit_type": "BATCH",
                    }
                ],
            },
            format="json",
        )
        self.assertIn(resp.status_code, (400, 403))
