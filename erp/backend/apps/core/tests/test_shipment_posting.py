"""Shipment-posting guard regressions (Q-055 + over-shipment).

Pins the integrity guards around `apps.shipment.services.create_shipment`:

* happy path posts exactly one OUT movement and audits shipment + lines;
* shipping another company's traceability unit is rejected (Q-055);
* shipping more than the allocated quantity is rejected (over-shipment);
* quarantined warehouses cannot ship.

Lives under core to stay collision-free with concurrent edits to the shipment
test module; it exercises the shipment app purely through its API.
"""

from __future__ import annotations

import uuid as uuid_module
from decimal import Decimal

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.core.tests.factories import auth_client, grant, make_company, make_user
from apps.inventory import services as inventory_services
from apps.inventory.models import (
    StockMovement,
    StockMovementDirection,
    TraceabilityUnit,
    WarehouseStoreType,
)
from apps.shipment.tests.test_shipment import build_prereqs


class ShipmentPostingGuardTests(TestCase):
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

    def _allocate(self, qty="30"):
        return self.client.post(
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

    def _ship(self, *, unit=None, allocation_id=None, qty="30", warehouse=None):
        line = {
            "traceability_unit": str((unit or self.p["unit"]).id),
            "quantity": qty,
            "uom": str(self.p["uom"].id),
            "sales_order_line": str(self.p["sol"].id),
        }
        if allocation_id:
            line["allocation"] = allocation_id
        wh = warehouse or self.p["warehouse"]
        return self.client.post(
            "/api/v1/shipment/deliveries/",
            {
                "company": str(self.company.id),
                "customer": str(self.p["customer"].id),
                "warehouse": str(wh.id),
                "number": "SHIP-" + uuid_module.uuid4().hex[:8].upper(),
                "shipped_at": "2026-08-22",
                "lines": [line],
            },
            format="json",
        )

    def _outs_for(self, unit):
        return StockMovement.objects.filter(
            traceability_unit=unit, direction=StockMovementDirection.OUT
        )

    def test_happy_path_posts_out_and_audits(self):
        alloc_resp = self._allocate("30")
        self.assertEqual(alloc_resp.status_code, 201, alloc_resp.content)
        before = self._outs_for(self.p["unit"]).count()

        resp = self._ship(allocation_id=alloc_resp.json()["id"])
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(self._outs_for(self.p["unit"]).count(), before + 1)
        self.assertTrue(AuditLog.objects.filter(entity_type="shipment.Shipment").exists())
        self.assertTrue(
            AuditLog.objects.filter(entity_type="shipment.ShipmentLine").exists()
        )

    def test_over_shipment_vs_allocation_rejected(self):
        alloc_resp = self._allocate("10")
        self.assertEqual(alloc_resp.status_code, 201)

        resp = self._ship(allocation_id=alloc_resp.json()["id"], qty="11")
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "shipment.over_shipped")
        self.assertEqual(self._outs_for(self.p["unit"]).count(), 0)

    def test_foreign_unit_rejected(self):
        """A company-B unit can never ship under a company-A shipment."""
        from apps.inventory.models import TraceabilityUnitType

        foreign_company = make_company(code="BBBB")
        foreign_unit = TraceabilityUnit.objects.create(
            company=foreign_company,
            material=self.p["material"],
            unit_type=TraceabilityUnitType.ROLL,
            identifier="ROLL-FOREIGN",
            quantity=Decimal("100"),
            uom=self.p["uom"],
        )

        resp = self._ship(unit=foreign_unit, qty="5")
        self.assertIn(resp.status_code, (400, 422))
        self.assertEqual(self._outs_for(foreign_unit).count(), 0)

    def test_quarantine_warehouse_cannot_ship(self):
        quarantine = Warehouse.objects.create(
            company=self.company,
            code="QUA-SHIP",
            name_fa="قرنطینه",
            store_type=WarehouseStoreType.QUARANTINE,
        )
        resp = self._ship(warehouse=quarantine)
        self.assertEqual(resp.status_code, 422)
