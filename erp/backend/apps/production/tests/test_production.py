"""Production tests for work orders and confirmed execution postings.

Covers lifecycle integrity, RBAC, explicit and backflush material issues,
produced outputs, atomic stock movements, and append-only execution records.
Confirmation detail, QC results, receipts, valuation, and recall remain out of
scope for this slice.
"""

from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.catalog.models import (
    Material,
    MaterialSubtype,
    ProductClass,
    ProductFamily,
    ProductGroup,
    ProductType,
    UnitOfMeasure,
    UomDimension,
)
from apps.core.tests.factories import auth_client, grant, make_company, make_superuser, make_user
from apps.engineering.models import CustomerProduct, SpecificationRevision
from apps.inventory.models import TraceabilityUnit, TraceabilityUnitType, Warehouse
from apps.partners.models import Customer, Partner
from apps.production.models import MaterialIssue, ProductionOrder, ProductionOutput


def build_prereqs(company):
    """Minimal customer + customer-product + spec-revision + uom prerequisites."""
    uom = UnitOfMeasure.objects.create(code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS)
    group = ProductGroup.objects.create(code="FOOD", name_fa="بسته‌بندی غذایی")
    ptype = ProductType.objects.create(code="FILM", name_fa="فیلم")
    pclass = ProductClass.objects.create(product_type=ptype, code="LAM", name_fa="لمینت")
    family = ProductFamily.objects.create(product_class=pclass, code="POUCH", name_fa="پوچ")
    partner = Partner.objects.create(
        company=company, code="C-001", name_fa="مشتری", is_customer=True
    )
    customer = Customer.objects.create(partner=partner)
    product = CustomerProduct.objects.create(
        company=company,
        customer=partner,
        code="CP-001",
        name_fa="پوچ ۱ کیلویی",
        product_group=group,
        family=family,
        base_uom=uom,
    )
    spec = SpecificationRevision.objects.create(root=product, revision_number=1)
    return {"uom": uom, "customer": customer, "product": product, "spec": spec}


class ProductionOrderTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)
        self.user = make_user()
        grant(self.user, "production.order.view", "production.order.manage")
        self.client = auth_client(self.user)

    def _create_po(self, number="WO-1"):
        return self.client.post(
            "/api/v1/production/orders/",
            {
                "company": str(self.company.id),
                "number": number,
                "customer_product": str(self.p["product"].id),
                "spec_revision": str(self.p["spec"].id),
                "planned_quantity": "1000.000000",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )

    def test_create_order_defaults_status_and_audits(self):
        resp = self._create_po()
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["status"], "DRAFT")
        po = ProductionOrder.objects.get(number="WO-1")
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="production.ProductionOrder",
                entity_id=str(po.id),
            ).exists()
        )

    def test_duplicate_number_per_company_rejected(self):
        self._create_po()
        dup = self._create_po()
        self.assertEqual(dup.status_code, 400, dup.content)

    def test_spec_revision_must_belong_to_customer_product(self):
        # A specification revision of a *different* product must be rejected.
        other_product = CustomerProduct.objects.create(
            company=self.company,
            customer=self.p["customer"].partner,
            code="CP-OTHER",
            name_fa="محصول دیگر",
            product_group=self.p["product"].product_group,
            family=self.p["product"].family,
            base_uom=self.p["uom"],
        )
        other_spec = SpecificationRevision.objects.create(root=other_product, revision_number=1)
        resp = self.client.post(
            "/api/v1/production/orders/",
            {
                "company": str(self.company.id),
                "number": "WO-MISMATCH",
                "customer_product": str(self.p["product"].id),
                "spec_revision": str(other_spec.id),
                "planned_quantity": "10.000000",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("spec_revision", resp.data["error"]["details"])

    def test_customer_product_must_belong_to_order_company(self):
        other_company = make_company(code="OTHERCO")
        resp = self.client.post(
            "/api/v1/production/orders/",
            {
                "company": str(other_company.id),
                "number": "WO-XCO",
                "customer_product": str(self.p["product"].id),
                "spec_revision": str(self.p["spec"].id),
                "planned_quantity": "10.000000",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("customer_product", resp.data["error"]["details"])

    def test_status_is_read_only_on_create(self):
        resp = self.client.post(
            "/api/v1/production/orders/",
            {
                "company": str(self.company.id),
                "number": "WO-9",
                "customer_product": str(self.p["product"].id),
                "spec_revision": str(self.p["spec"].id),
                "planned_quantity": "500.000000",
                "uom": str(self.p["uom"].id),
                "status": "RELEASED",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["status"], "DRAFT")

    def test_lifecycle_release_complete_close_audits(self):
        pid = self._create_po().data["id"]
        r = self.client.post(f"/api/v1/production/orders/{pid}/release/")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["status"], "RELEASED")
        c = self.client.post(f"/api/v1/production/orders/{pid}/complete/")
        self.assertEqual(c.status_code, 200, c.content)
        self.assertEqual(c.data["status"], "COMPLETED")
        cl = self.client.post(f"/api/v1/production/orders/{pid}/close/")
        self.assertEqual(cl.status_code, 200, cl.content)
        self.assertEqual(cl.data["status"], "CLOSED")
        self.assertTrue(
            AuditLog.objects.filter(
                action="UPDATE",
                entity_type="production.ProductionOrder",
                entity_id=pid,
            ).exists()
        )

    def test_invalid_transition_rejected(self):
        pid = self._create_po().data["id"]
        # Cannot complete straight from DRAFT (must be RELEASED first).
        c = self.client.post(f"/api/v1/production/orders/{pid}/complete/")
        self.assertEqual(c.status_code, 409, c.content)
        # Cannot close straight from DRAFT either.
        cl = self.client.post(f"/api/v1/production/orders/{pid}/close/")
        self.assertEqual(cl.status_code, 409, cl.content)

    def test_cancel_from_draft(self):
        pid = self._create_po().data["id"]
        c = self.client.post(f"/api/v1/production/orders/{pid}/cancel/")
        self.assertEqual(c.status_code, 200, c.content)
        self.assertEqual(c.data["status"], "CANCELLED")

    def test_header_not_editable_after_release(self):
        pid = self._create_po().data["id"]
        self.client.post(f"/api/v1/production/orders/{pid}/release/")
        patched = self.client.patch(
            f"/api/v1/production/orders/{pid}/",
            {"notes": "late edit"},
            format="json",
        )
        self.assertEqual(patched.status_code, 409, patched.content)


class ProductionOrderPermissionTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)

    def test_view_only_cannot_create_order(self):
        user = make_user(email="viewer@slz.test")
        grant(user, "production.order.view")
        client = auth_client(user)
        resp = client.post(
            "/api/v1/production/orders/",
            {
                "company": str(self.company.id),
                "number": "WO-X",
                "customer_product": str(self.p["product"].id),
                "spec_revision": str(self.p["spec"].id),
                "planned_quantity": "100.000000",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_unpermitted_user_cannot_list_orders(self):
        client = auth_client(make_user(email="nobody@slz.test"))
        resp = client.get("/api/v1/production/orders/")
        self.assertEqual(resp.status_code, 403, resp.content)


class ProductionExecutionTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)
        self.user = make_superuser(email="execution-admin@slz.test")
        self.client = auth_client(self.user)
        self.warehouse = Warehouse.objects.create(
            company=self.company, code="WIP-01", name_fa="انبار WIP", store_type="WIP"
        )
        self.resin = Material.objects.create(
            company=self.company,
            code="RESIN-EXEC",
            name_fa="گرانول اجرا",
            subtype=MaterialSubtype.RESIN_MASTERBATCH,
            traceability_mode="BATCH",
            base_uom=self.p["uom"],
        )
        self.unit = TraceabilityUnit.objects.create(
            company=self.company,
            material=self.resin,
            unit_type=TraceabilityUnitType.BATCH,
            identifier="BATCH-EXEC",
            quantity="1000.000000",
            uom=self.p["uom"],
        )
        self.order = ProductionOrder.objects.create(
            company=self.company,
            number="WO-EXEC",
            customer_product=self.p["product"],
            spec_revision=self.p["spec"],
            planned_quantity="1000.000000",
            uom=self.p["uom"],
            status="RELEASED",
        )

    def test_explicit_issue_requires_unit_and_posts_movement(self):
        # Q-048/Q-055 execution guard: stock must exist before an issue can
        # post — seed one receipt so the negative-stock check passes.
        from apps.inventory import services as inventory_services
        from apps.inventory.models import StockMovementDirection

        inventory_services.post_movement(
            company=self.company,
            warehouse=self.warehouse,
            direction=StockMovementDirection.IN,
            quantity=Decimal("25"),
            uom=self.p["uom"],
            material=self.resin,
            traceability_unit=self.unit,
            reference_type="test.seed",
            actor=self.user,
        )
        response = self.client.post(
            "/api/v1/production/material-issues/",
            {
                "production_order": str(self.order.id),
                "material": str(self.resin.id),
                "traceability_unit": str(self.unit.id),
                "warehouse": str(self.warehouse.id),
                "quantity": "10.000000",
                "uom": str(self.p["uom"].id),
                "method": "EXPLICIT",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(MaterialIssue.objects.count(), 1)
        # Seed receipt (IN) + issue (OUT) both land on the serialized unit's
        # ledger — the append-only history is exactly these two rows.
        self.assertEqual(self.unit.stock_movements.count(), 2)

    def test_backflush_does_not_accept_selected_unit(self):
        response = self.client.post(
            "/api/v1/production/material-issues/",
            {
                "production_order": str(self.order.id),
                "material": str(self.resin.id),
                "traceability_unit": str(self.unit.id),
                "warehouse": str(self.warehouse.id),
                "quantity": "10.000000",
                "uom": str(self.p["uom"].id),
                "method": "BACKFLUSH",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_output_posts_in_movement_and_is_append_only(self):
        output_unit = TraceabilityUnit.objects.create(
            company=self.company,
            customer_product_id=self.p["product"].id,
            unit_type=TraceabilityUnitType.BATCH,
            identifier="OUTPUT-001",
            quantity="25.000000",
            uom=self.p["uom"],
        )
        response = self.client.post(
            "/api/v1/production/outputs/",
            {
                "production_order": str(self.order.id),
                "traceability_unit": str(output_unit.id),
                "warehouse": str(self.warehouse.id),
                "quantity": "25.000000",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(ProductionOutput.objects.count(), 1)
        self.assertEqual(output_unit.stock_movements.count(), 1)
        patched = self.client.patch(
            f"/api/v1/production/outputs/{response.data['id']}/",
            {"notes": "no"},
            format="json",
        )
        self.assertEqual(patched.status_code, 409, patched.content)
