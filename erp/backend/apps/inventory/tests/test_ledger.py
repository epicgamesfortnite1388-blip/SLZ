"""Stock-ledger semantics tests (Q-046/Q-049 execution foundation).

Pins the append-only ledger contract enforced by ``apps.inventory.services``:

* balances/kardex are always derived from movements, never stored;
* an OUT that would drive stock negative is rejected (no partial posting);
* quarantined stock cannot be issued;
* every accepted posting emits exactly one audit row.
"""

from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.catalog.models import Material, UnitOfMeasure, UomDimension
from apps.core.tests.factories import make_company, make_site, make_user
from apps.inventory import services
from apps.inventory.models import (
    StockMovement,
    StockMovementDirection,
    TraceabilityUnit,
    TraceabilityUnitType,
    Warehouse,
    WarehouseStoreType,
)


class LedgerTestBase(TestCase):
    def setUp(self):
        self.company = make_company()
        self.site = make_site(company=self.company)
        self.user = make_user()
        self.uom = UnitOfMeasure.objects.create(
            code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS
        )
        self.material = Material.objects.create(
            company=self.company, code="RM-PE", name_fa="پلی‌اتیلن", base_uom=self.uom
        )
        self.wh = Warehouse.objects.create(
            company=self.company,
            site=self.site,
            code="RM-01",
            name_fa="انبار مواد",
            store_type=WarehouseStoreType.RAW_MATERIAL,
        )

    def _receipt(self, qty, warehouse=None, unit=None):
        return services.post_movement(
            company=self.company,
            warehouse=warehouse or self.wh,
            direction=StockMovementDirection.IN,
            quantity=Decimal(str(qty)),
            uom=self.uom,
            material=self.material,
            traceability_unit=unit,
            reference_type="test.receipt",
            actor=self.user,
        )


class BalanceTests(LedgerTestBase):
    def test_receipt_then_issue_yields_exact_balance(self):
        self._receipt(100)
        services.post_movement(
            company=self.company,
            warehouse=self.wh,
            direction=StockMovementDirection.OUT,
            quantity=Decimal("37.5"),
            uom=self.uom,
            material=self.material,
            reference_type="test.issue",
            actor=self.user,
        )
        rows = services.balances(self.company)
        self.assertEqual(len(rows), 1)
        self.assertEqual(Decimal(rows[0]["on_hand"]), Decimal("62.5"))

    def test_negative_stock_is_rejected_and_nothing_posts(self):
        self._receipt(10)
        before = StockMovement.objects.count()
        with self.assertRaises(Exception) as ctx:
            services.post_movement(
                company=self.company,
                warehouse=self.wh,
                direction=StockMovementDirection.OUT,
                quantity=Decimal("11"),
                uom=self.uom,
                material=self.material,
                actor=self.user,
            )
        self.assertIn("insufficient", str(ctx.exception.message).lower())
        self.assertEqual(StockMovement.objects.count(), before)

    def test_quarantine_store_cannot_issue(self):
        quarantine = Warehouse.objects.create(
            company=self.company,
            site=self.site,
            code="QUA-01",
            name_fa="قرنطینه",
            store_type=WarehouseStoreType.QUARANTINE,
        )
        self._receipt(5, warehouse=quarantine)
        with self.assertRaises(Exception) as ctx:
            services.post_movement(
                company=self.company,
                warehouse=quarantine,
                direction=StockMovementDirection.OUT,
                quantity=Decimal("1"),
                uom=self.uom,
                material=self.material,
                actor=self.user,
            )
        self.assertIn("quarantine", str(ctx.exception.message).lower())

    def test_kardex_running_balance_is_chronological(self):
        self._receipt(50)
        services.post_movement(
            company=self.company,
            warehouse=self.wh,
            direction=StockMovementDirection.OUT,
            quantity=Decimal("20"),
            uom=self.uom,
            material=self.material,
            actor=self.user,
        )
        history = services.kardex(company=self.company)
        self.assertEqual([row["balance_after"] for row in history], ["50", "30"])


class SerializedUnitLedgerTests(LedgerTestBase):
    """Q-046: rolls are serialized; per-unit balances come from the same ledger."""

    def setUp(self):
        super().setUp()
        self.roll = TraceabilityUnit.objects.create(
            company=self.company,
            material=self.material,
            unit_type=TraceabilityUnitType.ROLL,
            identifier="ROLL-0001",
            quantity=Decimal("500"),
            uom=self.uom,
            weight=Decimal("71"),
            length=Decimal("1169"),
            width=Decimal("500"),
        )

    def test_per_unit_balance_tracks_the_serialized_roll(self):
        self._receipt(500, unit=self.roll)
        balance = services.on_hand_quantity(company=self.company, traceability_unit=self.roll)
        self.assertEqual(balance, Decimal("500"))

        services.post_movement(
            company=self.company,
            warehouse=self.wh,
            direction=StockMovementDirection.OUT,
            quantity=Decimal("120"),
            uom=self.uom,
            material=self.material,
            traceability_unit=self.roll,
            reference_type="production.MaterialIssue",
            actor=self.user,
        )
        self.assertEqual(
            services.on_hand_quantity(company=self.company, traceability_unit=self.roll),
            Decimal("380"),
        )

    def test_every_accepted_posting_writes_an_audit_row(self):
        before = AuditLog.objects.filter(entity_type="inventory.StockMovement").count()
        self._receipt(7)
        self.assertEqual(
            AuditLog.objects.filter(entity_type="inventory.StockMovement").count(),
            before + 1,
        )
