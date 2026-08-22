"""Sales tests: sales-order document, status state machine, DRAFT-only
editability, RBAC.

Covers the CONFIRMED commercial-document layer only — manual document numbers,
the guarded status transitions (confirm/close/cancel), line-editable-only-while-
DRAFT, and permission gating. NO pricing / ATP / allocation / shipment / invoice
layer exists to test, by design (gated on R-14, SR-12, Q-046 and later phases).
"""

from __future__ import annotations

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.catalog.models import (
    ProductClass,
    ProductFamily,
    ProductGroup,
    ProductType,
    UnitOfMeasure,
    UomDimension,
)
from apps.core.tests.factories import auth_client, grant, make_company, make_user
from apps.engineering.models import CustomerProduct
from apps.partners.models import Customer, Partner
from apps.sales.models import SalesOrder


def build_prereqs(company):
    """Minimal customer + customer-product + uom prerequisites."""
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
    return {"uom": uom, "customer": customer, "product": product}


class SalesOrderTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)
        self.user = make_user()
        grant(self.user, "sales.order.view", "sales.order.manage")
        self.client = auth_client(self.user)

    def _create_so(self, number="SO-1"):
        return self.client.post(
            "/api/v1/sales/orders/",
            {
                "company": str(self.company.id),
                "number": number,
                "customer": str(self.p["customer"].id),
            },
            format="json",
        )

    def test_create_order_defaults_currency_and_audits(self):
        resp = self._create_so()
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["status"], "DRAFT")
        self.assertEqual(resp.data["currency"], "IRR")
        so = SalesOrder.objects.get(number="SO-1")
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="sales.SalesOrder",
                entity_id=str(so.id),
            ).exists()
        )

    def test_duplicate_number_per_company_rejected(self):
        self._create_so()
        dup = self._create_so()
        self.assertEqual(dup.status_code, 400, dup.content)

    def test_status_is_read_only_on_create(self):
        resp = self.client.post(
            "/api/v1/sales/orders/",
            {
                "company": str(self.company.id),
                "number": "SO-9",
                "customer": str(self.p["customer"].id),
                "status": "CONFIRMED",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["status"], "DRAFT")

    def test_lifecycle_confirm_then_close_audits(self):
        pid = self._create_so().data["id"]
        c = self.client.post(f"/api/v1/sales/orders/{pid}/confirm/")
        self.assertEqual(c.status_code, 200, c.content)
        self.assertEqual(c.data["status"], "CONFIRMED")
        cl = self.client.post(f"/api/v1/sales/orders/{pid}/close/")
        self.assertEqual(cl.status_code, 200, cl.content)
        self.assertEqual(cl.data["status"], "CLOSED")
        self.assertTrue(
            AuditLog.objects.filter(
                action="UPDATE",
                entity_type="sales.SalesOrder",
                entity_id=pid,
            ).exists()
        )

    def test_invalid_transition_rejected(self):
        pid = self._create_so().data["id"]
        # Cannot close straight from DRAFT (must be CONFIRMED).
        cl = self.client.post(f"/api/v1/sales/orders/{pid}/close/")
        self.assertEqual(cl.status_code, 409, cl.content)

    def test_cancel_from_draft(self):
        pid = self._create_so().data["id"]
        c = self.client.post(f"/api/v1/sales/orders/{pid}/cancel/")
        self.assertEqual(c.status_code, 200, c.content)
        self.assertEqual(c.data["status"], "CANCELLED")

    def test_line_unit_price_optional_and_editable_only_while_draft(self):
        pid = self._create_so().data["id"]
        line = {
            "order": pid,
            "sequence": 1,
            "customer_product": str(self.p["product"].id),
            "quantity": "1000.000000",
            "uom": str(self.p["uom"].id),
        }
        ok = self.client.post("/api/v1/sales/order-lines/", line, format="json")
        self.assertEqual(ok.status_code, 201, ok.content)
        self.assertIsNone(ok.data["unit_price"])
        self.client.post(f"/api/v1/sales/orders/{pid}/confirm/")
        blocked = self.client.post(
            "/api/v1/sales/order-lines/",
            {**line, "sequence": 2},
            format="json",
        )
        self.assertEqual(blocked.status_code, 409, blocked.content)

    def test_header_not_editable_after_confirm(self):
        pid = self._create_so().data["id"]
        self.client.post(f"/api/v1/sales/orders/{pid}/confirm/")
        patched = self.client.patch(
            f"/api/v1/sales/orders/{pid}/",
            {"notes": "late edit"},
            format="json",
        )
        self.assertEqual(patched.status_code, 409, patched.content)

    def test_line_customer_product_must_belong_to_order_customer(self):
        # A product tied to a *different* customer (same company) is rejected.
        other_partner = Partner.objects.create(
            company=self.company,
            code="C-002",
            name_fa="مشتری دیگر",
            is_customer=True,
        )
        Customer.objects.create(partner=other_partner)
        other_product = CustomerProduct.objects.create(
            company=self.company,
            customer=other_partner,
            code="CP-OTHER",
            name_fa="محصول مشتری دیگر",
            product_group=self.p["product"].product_group,
            family=self.p["product"].family,
            base_uom=self.p["uom"],
        )
        pid = self._create_so().data["id"]
        resp = self.client.post(
            "/api/v1/sales/order-lines/",
            {
                "order": pid,
                "sequence": 1,
                "customer_product": str(other_product.id),
                "quantity": "10.000000",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("customer_product", resp.data["error"]["details"])

    def test_line_customer_product_must_belong_to_order_company(self):
        # A product from another company must never leak onto this order.
        other_company = make_company(code="OTHERCO")
        other_partner = Partner.objects.create(
            company=other_company,
            code="XC-001",
            name_fa="مشتری شرکت دیگر",
            is_customer=True,
        )
        other_product = CustomerProduct.objects.create(
            company=other_company,
            customer=other_partner,
            code="CP-XCO",
            name_fa="محصول شرکت دیگر",
            product_group=self.p["product"].product_group,
            family=self.p["product"].family,
            base_uom=self.p["uom"],
        )
        pid = self._create_so().data["id"]
        resp = self.client.post(
            "/api/v1/sales/order-lines/",
            {
                "order": pid,
                "sequence": 1,
                "customer_product": str(other_product.id),
                "quantity": "10.000000",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("customer_product", resp.data["error"]["details"])

    def test_line_matching_customer_and_company_is_accepted(self):
        # The consistent (happy-path) case must still succeed.
        pid = self._create_so().data["id"]
        resp = self.client.post(
            "/api/v1/sales/order-lines/",
            {
                "order": pid,
                "sequence": 1,
                "customer_product": str(self.p["product"].id),
                "quantity": "10.000000",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)


class SalesPermissionTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)

    def test_view_only_cannot_create_order(self):
        user = make_user(email="viewer@slz.test")
        grant(user, "sales.order.view")
        client = auth_client(user)
        resp = client.post(
            "/api/v1/sales/orders/",
            {
                "company": str(self.company.id),
                "number": "SO-X",
                "customer": str(self.p["customer"].id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_unpermitted_user_cannot_list_orders(self):
        client = auth_client(make_user(email="nobody@slz.test"))
        resp = client.get("/api/v1/sales/orders/")
        self.assertEqual(resp.status_code, 403, resp.content)
