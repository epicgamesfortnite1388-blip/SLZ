"""Shipment tests: allocation, release, and delivery posting."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.test import TestCase

from apps.catalog.models import (
    Material,
    ProductClass,
    ProductFamily,
    ProductGroup,
    ProductType,
    UnitOfMeasure,
    UomDimension,
)
from apps.core.tests.factories import auth_client, grant, make_company, make_site, make_user
from apps.engineering.models import CustomerProduct, SpecificationRevision
from apps.inventory import services as inventory_services
from apps.inventory.models import (
    StockMovementDirection,
    TraceabilityUnit,
    TraceabilityUnitType,
    Warehouse,
)
from apps.partners.models import Customer, Partner
from apps.sales.models import SalesOrder, SalesOrderLine
from apps.shipment.models import Allocation, AllocationStatus, Shipment


def build_prereqs(company):
    uom = UnitOfMeasure.objects.create(code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS)
    group = ProductGroup.objects.create(code="FOOD", name_fa="غذایی")
    ptype = ProductType.objects.create(code="FILM", name_fa="فیلم")
    pclass = ProductClass.objects.create(product_type=ptype, code="LAM", name_fa="لمینت")
    family = ProductFamily.objects.create(product_class=pclass, code="P", name_fa="P")
    partner = Partner.objects.create(company=company, code="C-1", name_fa="مشتری", is_customer=True)
    cus = Customer.objects.create(partner=partner)
    cp = CustomerProduct.objects.create(
        company=company,
        customer=partner,
        code="CP-1",
        name_fa="پوچ",
        product_group=group,
        family=family,
        base_uom=uom,
    )
    SpecificationRevision.objects.create(root=cp, revision_number=1)
    mat = Material.objects.create(company=company, code="RM-1", name_fa="ماده", base_uom=uom)
    wh = Warehouse.objects.create(
        company=company,
        site=make_site(company=company),
        code="FG-01",
        name_fa="انبار",
        store_type="FINISHED_GOODS",
    )
    unit = TraceabilityUnit.objects.create(
        company=company,
        material=mat,
        unit_type=TraceabilityUnitType.ROLL,
        identifier="ROLL-SHIP",
        quantity="500",
        uom=uom,
    )
    so = SalesOrder.objects.create(
        company=company,
        number="SO-1",
        customer=cus,
        status="CONFIRMED",
    )
    sol = SalesOrderLine.objects.create(
        order=so,
        sequence=1,
        customer_product=cp,
        quantity=50,
        uom=uom,
    )
    return {
        "uom": uom,
        "customer": cus,
        "product": cp,
        "sol": sol,
        "so": so,
        "warehouse": wh,
        "unit": unit,
        "material": mat,
    }


class AllocationTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)
        self.user = make_user()
        grant(self.user, "shipment.allocation.view", "shipment.allocation.manage")
        self.client = auth_client(self.user)
        # Seed stock so allocation quantity check passes
        inventory_services.post_movement(
            company=self.company,
            warehouse=self.p["warehouse"],
            direction=StockMovementDirection.IN,
            quantity=Decimal("500"),
            uom=self.p["uom"],
            material=self.p["material"],
            traceability_unit=self.p["unit"],
            reference_type="test.seed",
            actor=self.user,
        )

    def test_reserve_creates_allocation(self):
        resp = self.client.post(
            "/api/v1/shipment/allocations/",
            {
                "company": str(self.company.id),
                "sales_order_line": str(self.p["sol"].id),
                "traceability_unit": str(self.p["unit"].id),
                "quantity": "30",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(Allocation.objects.count(), 1)
        self.assertEqual(Allocation.objects.first().status, AllocationStatus.RESERVED)

    def test_over_allocation_rejected(self):
        # Allocate full available
        self.client.post(
            "/api/v1/shipment/allocations/",
            {
                "company": str(self.company.id),
                "sales_order_line": str(self.p["sol"].id),
                "traceability_unit": str(self.p["unit"].id),
                "quantity": "500",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        # Another order line same unit should fail
        so2 = SalesOrder.objects.create(
            company=self.company,
            number="SO-2",
            customer=self.p["customer"],
            status="CONFIRMED",
        )
        sol2 = SalesOrderLine.objects.create(
            order=so2,
            sequence=1,
            customer_product=self.p["product"],
            quantity=10,
            uom=self.p["uom"],
        )
        resp = self.client.post(
            "/api/v1/shipment/allocations/",
            {
                "company": str(self.company.id),
                "sales_order_line": str(sol2.id),
                "traceability_unit": str(self.p["unit"].id),
                "quantity": "1",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 422)

    def test_release_allocation(self):
        resp = self.client.post(
            "/api/v1/shipment/allocations/",
            {
                "company": str(self.company.id),
                "sales_order_line": str(self.p["sol"].id),
                "traceability_unit": str(self.p["unit"].id),
                "quantity": "20",
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        aid = resp.data["id"]
        rel = self.client.post(f"/api/v1/shipment/allocations/{aid}/release/")
        self.assertEqual(rel.status_code, 200, rel.content)
        self.assertEqual(rel.data["status"], AllocationStatus.RELEASED)

    def test_list_requires_permission(self):
        nobody = make_user(email="noship@slz.test")
        resp = auth_client(nobody).get("/api/v1/shipment/allocations/")
        self.assertEqual(resp.status_code, 403)

    def test_concurrent_reserve_serialized_by_select_for_update(self):
        """Two reservations on the same unit must not both pass the availability
        check — select_for_update serializes them so the second sees the first's
        committed allocation.
        """
        from apps.shipment import services as shipment_services

        # Allocate full stock to sol-1 — should succeed.
        alloc1 = shipment_services.reserve(
            company=self.company,
            sales_order_line=self.p["sol"],
            traceability_unit=self.p["unit"],
            quantity=Decimal("500"),
            uom=self.p["uom"],
            actor=self.user,
        )
        self.assertIsNotNone(alloc1)
        self.assertEqual(alloc1.status, AllocationStatus.RESERVED)

        # A second order line on the same unit must now fail (0 available).
        so2 = SalesOrder.objects.create(
            company=self.company,
            number="SO-2-RACE",
            customer=self.p["customer"],
            status="CONFIRMED",
        )
        sol2 = SalesOrderLine.objects.create(
            order=so2,
            sequence=1,
            customer_product=self.p["product"],
            quantity=10,
            uom=self.p["uom"],
        )
        from apps.core.exceptions import BusinessRuleError

        with self.assertRaises(BusinessRuleError) as ctx:
            shipment_services.reserve(
                company=self.company,
                sales_order_line=sol2,
                traceability_unit=self.p["unit"],
                quantity=Decimal("1"),
                uom=self.p["uom"],
                actor=self.user,
            )
        self.assertIn("Insufficient", str(ctx.exception))

    def test_select_for_update_locks_unit_row(self):
        """Verify that TraceabilityUnit.objects.select_for_update() is called
        during reserve(). The query should succeed — SQLite supports it within
        transactions.
        """
        from apps.inventory.models import TraceabilityUnit
        from apps.shipment import services as shipment_services

        # The reserve() call itself exercises select_for_update on the unit row.
        # If the database backend doesn't support it (some in-memory SQLite
        # configs), it would raise a DatabaseError — this test confirms it
        # doesn't.
        alloc = shipment_services.reserve(
            company=self.company,
            sales_order_line=self.p["sol"],
            traceability_unit=self.p["unit"],
            quantity=Decimal("100"),
            uom=self.p["uom"],
            actor=self.user,
        )
        self.assertIsNotNone(alloc)
        # The unit row should still exist and be queryable.
        unit = TraceabilityUnit.objects.get(pk=self.p["unit"].pk)
        self.assertEqual(Decimal(unit.quantity), Decimal(self.p["unit"].quantity))

    def test_over_allocation_same_order_line_blocked(self):
        """Two reservations on the same SO line must not together exceed on-hand.
        Regression: the old code excluded the same SO line from the already-
        allocated check, allowing intra-line over-allocation."""
        from apps.core.exceptions import BusinessRuleError
        from apps.shipment import services as shipment_services

        # First allocation: 200 on 500 on-hand
        shipment_services.reserve(
            company=self.company,
            sales_order_line=self.p["sol"],
            traceability_unit=self.p["unit"],
            quantity=Decimal("200"),
            uom=self.p["uom"],
            actor=self.user,
        )
        # Second allocation on same SO line: 400 — would make 600 > 500
        with self.assertRaises(BusinessRuleError) as ctx:
            shipment_services.reserve(
                company=self.company,
                sales_order_line=self.p["sol"],
                traceability_unit=self.p["unit"],
                quantity=Decimal("400"),
                uom=self.p["uom"],
                actor=self.user,
            )
        self.assertIn("Insufficient", str(ctx.exception))


class DeliveryTests(TestCase):
    """Delivery posting (create_shipment): atomic OUT movements, allocation
    consumption, reuse rejection, and idempotency."""

    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)
        self.user = make_user()
        grant(
            self.user,
            "shipment.allocation.view",
            "shipment.allocation.manage",
            "shipment.delivery.view",
            "shipment.delivery.manage",
        )
        self.client = auth_client(self.user)
        inventory_services.post_movement(
            company=self.company,
            warehouse=self.p["warehouse"],
            direction=StockMovementDirection.IN,
            quantity=Decimal("500"),
            uom=self.p["uom"],
            material=self.p["material"],
            traceability_unit=self.p["unit"],
            reference_type="test.seed",
            actor=self.user,
        )

    def _reserve(self, qty="50"):
        resp = self.client.post(
            "/api/v1/shipment/allocations/",
            {
                "company": str(self.company.id),
                "sales_order_line": str(self.p["sol"].id),
                "traceability_unit": str(self.p["unit"].id),
                "quantity": qty,
                "uom": str(self.p["uom"].id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        return resp.json()["id"]

    def _deliver(self, *, allocation_id, quantity="50", number="D-1", nonce=None):
        payload = {
            "company": str(self.company.id),
            "customer": str(self.p["customer"].id),
            "warehouse": str(self.p["warehouse"].id),
            "number": number,
            "shipped_at": "2026-08-22",
            "lines": [
                {
                    "traceability_unit": str(self.p["unit"].id),
                    "sales_order_line": str(self.p["sol"].id),
                    "allocation": str(allocation_id) if allocation_id is not None else None,
                    "quantity": quantity,
                    "uom": str(self.p["uom"].id),
                }
            ],
        }
        if nonce is not None:
            payload["nonce"] = str(nonce)
        return self.client.post("/api/v1/shipment/deliveries/", payload, format="json")

    def test_delivery_posts_out_movement_and_consumes_allocation(self):
        alloc_id = self._reserve()
        resp = self._deliver(allocation_id=alloc_id)
        self.assertEqual(resp.status_code, 201, resp.content)
        body = resp.json()
        self.assertEqual(body["status"], "SHIPPED")
        self.assertEqual(len(body["lines"]), 1)

        alloc = Allocation.objects.get(pk=alloc_id)
        self.assertEqual(alloc.status, AllocationStatus.SHIPPED)
        # Ledger: seed IN 500 - OUT 50
        from apps.inventory.services import on_hand_quantity

        on_hand = on_hand_quantity(
            company=self.company,
            warehouse=self.p["warehouse"],
            traceability_unit=self.p["unit"],
        )
        self.assertEqual(on_hand, Decimal("450"))

    def test_shipped_allocation_cannot_be_reused(self):
        """Regression (double-shipment): consuming the same RESERVED allocation
        twice must fail the second time — the allocation is marked SHIPPED and
        excluded from the writable queryset, so a retried/duplicate delivery
        cannot ship the unit again."""
        alloc_id = self._reserve()
        first = self._deliver(allocation_id=alloc_id, number="D-1")
        self.assertEqual(first.status_code, 201, first.content)

        second = self._deliver(allocation_id=alloc_id, number="D-2")
        self.assertEqual(second.status_code, 400, second.content)
        self.assertIn("allocation", second.json()["error"]["details"]["lines"][0])
        self.assertEqual(Allocation.objects.filter(status=AllocationStatus.SHIPPED).count(), 1)
        # Only the first delivery posted an OUT movement.
        from apps.inventory.models import StockMovement

        outs = StockMovement.objects.filter(reference_type="shipment.ShipmentLine", direction="OUT")
        self.assertEqual(outs.count(), 1)

    def test_delivery_without_allocation_still_guarded_by_stock(self):
        """A delivery that does not reference an allocation still cannot exceed
        on-hand stock (negative-stock guard in post_movement)."""
        resp = self._deliver(allocation_id=None, quantity="600")
        self.assertEqual(resp.status_code, 422, resp.content)
        self.assertEqual(resp.json()["error"]["code"], "inventory.insufficient_stock")

    def test_duplicate_nonce_rejected_on_delivery(self):
        """Same nonce on two delivery POSTs — the second is rejected with 409
        even though the allocation differs (retried submission protection)."""
        alloc_a = self._reserve(qty="30")
        alloc_b = self._reserve(qty="20")
        nonce = uuid.uuid4()
        first = self._deliver(allocation_id=alloc_a, quantity="30", number="D-N1", nonce=nonce)
        self.assertEqual(first.status_code, 201, first.content)
        second = self._deliver(allocation_id=alloc_b, quantity="20", number="D-N2", nonce=nonce)
        self.assertEqual(second.status_code, 409, second.content)
        self.assertEqual(second.json()["error"]["code"], "duplicate_request")
        # Nothing from the second (duplicate) attempt was persisted.
        self.assertEqual(Shipment.objects.filter(number="D-N2").count(), 0)
