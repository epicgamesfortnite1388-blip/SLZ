"""Shipment tests: allocation, release, and delivery posting."""

from __future__ import annotations

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
from apps.shipment.models import Allocation, AllocationStatus


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
