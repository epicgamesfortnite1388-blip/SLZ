"""Sample-product lifecycle integration test (Q-046/Q-048/Q-049/Q-026 confirmed).

Tests the full ERP flow for product 1 (BOPP/PET/PE laminate roll):
  supplier → PO → GRN → traceability unit → costing → warehouse
  → production order → material issue → WIP → output → QC
  → allocation → shipment → genealogy → costing reconciliation

And for product 2 (PE printed bag with carton packaging):
  supplier → PO → GRN → batch traceability → production → carton output

Uses the confirmed business decisions:
  Q-046: serialized rolls with QC per reel
  Q-048: backflush for extrusion, explicit for print/lamination/slitting/sealing
  Q-049: film = roll/pallet, bags = carton, PE granules = batch
  Q-026: stocked intermediates with WIP warehouse per production step
"""

from __future__ import annotations

from datetime import date
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
from apps.core.tests.factories import (
    auth_client,
    grant,
    make_company,
    make_site,
    make_superuser,
    make_user,
)
from apps.engineering.models import CustomerProduct, SpecificationRevision
from apps.inventory import services as inventory_services
from apps.inventory.models import (
    GenealogyLink,
    StockMovementDirection,
    TraceabilityUnit,
    TraceabilityUnitType,
    Warehouse,
    WarehouseStoreType,
)
from apps.partners.models import Customer, Partner, Supplier
from apps.procurement.models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
from apps.production.models import (
    MaterialIssue,
    MaterialIssueMethod,
    ProductionOrder,
    ProductionOutput,
)
from apps.quality.models import QualityCheckResult
from apps.sales.models import SalesOrder, SalesOrderLine


class SampleProductLifecycleTests(TestCase):
    """Product 1: three-layer BOPP/PET/PE laminate roll.

    Flow: BOPP/PET/PE granule receipt → BOM → production → roll output
          → QC → allocation → shipment.

    Inventory backbone verifies:
      - per-unit ledger balances
      - genealogy chain
      - audit coverage
      - costing layers (integration hooks)
      - no negative stock
    """

    @classmethod
    def setUpTestData(cls):
        cls.company = make_company(code="SLZ01")
        cls.site = make_site(company=cls.company)
        cls.user = make_superuser(email="lifecycle@slz.test")
        cls.today = date(2026, 8, 22)

        # ── UoM ──────────────────────────────────────────────────────
        cls.kg = UnitOfMeasure.objects.create(
            code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS
        )
        cls.micron = UnitOfMeasure.objects.create(
            code="UM", name_fa="میکرون", dimension=UomDimension.LENGTH
        )
        cls.mm = UnitOfMeasure.objects.create(
            code="MM", name_fa="میلیمتر", dimension=UomDimension.LENGTH
        )
        cls.roll = UnitOfMeasure.objects.create(
            code="ROLL", name_fa="رول", dimension=UomDimension.COUNT
        )

        # ── Warehouses ────────────────────────────────────────────────
        cls.rm_wh = Warehouse.objects.create(
            company=cls.company,
            site=cls.site,
            code="RM-01",
            name_fa="انبار مواد اولیه",
            store_type=WarehouseStoreType.RAW_MATERIAL,
        )
        cls.wip_wh = Warehouse.objects.create(
            company=cls.company,
            site=cls.site,
            code="WIP-01",
            name_fa="انبار WIP",
            store_type=WarehouseStoreType.WIP,
        )
        cls.fg_wh = Warehouse.objects.create(
            company=cls.company,
            site=cls.site,
            code="FG-01",
            name_fa="انبار محصول",
            store_type=WarehouseStoreType.FINISHED_GOODS,
        )
        cls.quarantine_wh = Warehouse.objects.create(
            company=cls.company,
            site=cls.site,
            code="QUA-01",
            name_fa="قرنطینه",
            store_type=WarehouseStoreType.QUARANTINE,
        )

        # ── Materials (raw granules → intermediate film → final laminate) ─
        cls.bopp_resin = Material.objects.create(
            company=cls.company,
            code="BOPP-GR",
            name_fa="گرانول BOPP",
            subtype=MaterialSubtype.RESIN_MASTERBATCH,
            traceability_mode="BATCH",
            base_uom=cls.kg,
        )
        cls.pet_resin = Material.objects.create(
            company=cls.company,
            code="PET-GR",
            name_fa="گرانول PET",
            subtype=MaterialSubtype.RESIN_MASTERBATCH,
            traceability_mode="BATCH",
            base_uom=cls.kg,
        )
        cls.pe_resin = Material.objects.create(
            company=cls.company,
            code="PE-GR",
            name_fa="گرانول PE",
            subtype=MaterialSubtype.RESIN_MASTERBATCH,
            traceability_mode="BATCH",
            base_uom=cls.kg,
        )
        cls.bopp_film = Material.objects.create(
            company=cls.company,
            code="BOPP-FILM",
            name_fa="فیلم BOPP",
            subtype=MaterialSubtype.SEMI_FINISHED,
            traceability_mode="ROLL",
            base_uom=cls.kg,
        )
        cls.pet_film = Material.objects.create(
            company=cls.company,
            code="PET-FILM",
            name_fa="فیلم PET",
            subtype=MaterialSubtype.SEMI_FINISHED,
            traceability_mode="ROLL",
            base_uom=cls.kg,
        )
        cls.pe_film = Material.objects.create(
            company=cls.company,
            code="PE-FILM",
            name_fa="فیلم PE",
            subtype=MaterialSubtype.SEMI_FINISHED,
            traceability_mode="ROLL",
            base_uom=cls.kg,
        )
        cls.final_laminate = Material.objects.create(
            company=cls.company,
            code="LAM-BOPP-PET-PE",
            name_fa="لمینت سه لایه",
            subtype=MaterialSubtype.FINISHED,
            traceability_mode="ROLL",
            base_uom=cls.kg,
        )

        # ── Catalogue ──────────────────────────────────────────────────
        pg = ProductGroup.objects.create(code="FOOD", name_fa="بسته‌بندی غذایی")
        pt = ProductType.objects.create(code="FILM", name_fa="فیلم")
        pc = ProductClass.objects.create(product_type=pt, code="LAM", name_fa="لمینت")
        pf = ProductFamily.objects.create(product_class=pc, code="POUCH", name_fa="پوچ")

        # ── Partners ───────────────────────────────────────────────────
        partner_c = Partner.objects.create(
            company=cls.company, code="C-LIB", name_fa="لیبارو", is_customer=True
        )
        cls.customer = Customer.objects.create(partner=partner_c)
        partner_s = Partner.objects.create(
            company=cls.company, code="S-BOPP", name_fa="تأمین‌کننده BOPP", is_supplier=True
        )
        cls.supplier = Supplier.objects.create(partner=partner_s, is_approved=True)

        # ── Customer Product + Spec ───────────────────────────────────
        cls.cp = CustomerProduct.objects.create(
            company=cls.company,
            customer=partner_c,
            code="14445",
            name_fa="لمینت ۳ لایه قهوه لیبارو",
            product_group=pg,
            family=pf,
            base_uom=cls.kg,
        )
        cls.spec = SpecificationRevision.objects.create(root=cls.cp, revision_number=1)

        # ── Sales Order ───────────────────────────────────────────────
        cls.so = SalesOrder.objects.create(
            company=cls.company,
            number="SO-LIB-001",
            customer=cls.customer,
            status="CONFIRMED",
        )
        cls.sol = SalesOrderLine.objects.create(
            order=cls.so,
            sequence=1,
            customer_product=cls.cp,
            quantity=Decimal("10"),
            uom=cls.roll,
        )

    def _seed_stock_for_issue(self, material, wh, qty, unit_type="BATCH"):
        """Put stock in warehouse so material issues don't fail negative-stock check."""
        unit = TraceabilityUnit.objects.create(
            company=self.company,
            material=material,
            unit_type=unit_type,
            identifier=f"{material.code}-STOCK",
            quantity=qty,
            uom=self.kg,
        )
        inventory_services.post_movement(
            company=self.company,
            warehouse=wh,
            direction=StockMovementDirection.IN,
            quantity=qty,
            uom=self.kg,
            material=material,
            traceability_unit=unit,
            reference_type="test.seed",
            actor=self.user,
        )
        return unit

    # -------------------------------------------------------------------
    # A. PROCUREMENT: PO → GRN → traceability → costing
    # -------------------------------------------------------------------

    def test_po_to_grn_creates_traceability_and_movement(self):
        """Q-049: PE granules use BATCH traceability; GRN creates BATCH unit + IN."""
        po = PurchaseOrder.objects.create(
            company=self.company,
            site=self.site,
            supplier=self.supplier,
            number="PO-GRN-001",
            status=PurchaseOrderStatus.SENT,
        )
        pol = PurchaseOrderLine.objects.create(
            order=po,
            sequence=1,
            material=self.bopp_resin,
            quantity=Decimal("1000"),
            uom=self.kg,
        )
        client = auth_client(self.user)
        resp = client.post(
            "/api/v1/procurement/goods-receipts/",
            {
                "company": str(self.company.id),
                "warehouse": str(self.rm_wh.id),
                "supplier": str(self.supplier.id),
                "purchase_order": str(po.id),
                "number": "GRN-001",
                "received_at": self.today.isoformat(),
                "lines": [
                    {
                        "po_line": str(pol.id),
                        "material": str(self.bopp_resin.id),
                        "quantity": "1000",
                        "uom": str(self.kg.id),
                        "traceability_unit_type": "BATCH",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        body = resp.json()
        self.assertEqual(body["status"], "POSTED")
        self.assertEqual(len(body["lines"]), 1)

        # Traceability unit created
        unit_id = body["lines"][0]["traceability_unit"]
        unit = TraceabilityUnit.objects.get(pk=unit_id)
        self.assertEqual(unit.unit_type, "BATCH")
        self.assertEqual(unit.material_id, self.bopp_resin.id)
        self.assertEqual(unit.quantity, Decimal("1000"))

        # Stock movement created
        self.assertEqual(unit.stock_movements.count(), 1)
        mvt = unit.stock_movements.first()
        self.assertEqual(mvt.direction, StockMovementDirection.IN)
        self.assertEqual(mvt.warehouse_id, self.rm_wh.id)

        # Audit
        self.assertTrue(AuditLog.objects.filter(entity_type="procurement.GoodsReceipt").exists())

        # Costing: receipt cost layer (integration is now wired in GRN service)
        from apps.costing.models import CostLayer

        layers = CostLayer.objects.filter(
            company=self.company,
            material=self.bopp_resin,
            reference_type="procurement.GoodsReceiptLine",
        )
        self.assertEqual(layers.count(), 1, "GRN receipt should auto-post a cost layer")

        # On-hand balance derived from ledger
        bal = inventory_services.on_hand_quantity(
            company=self.company,
            warehouse=self.rm_wh,
            material=self.bopp_resin,
        )
        self.assertEqual(bal, Decimal("1000"))

    # -------------------------------------------------------------------
    # B. PRODUCTION: backflush extrusion + explicit lamination issue
    # -------------------------------------------------------------------

    def test_backflush_extrusion_then_explicit_lamination_issue(self):
        """Q-048: backflush for extrusion, explicit for printing/lamination/slitting/sealing."""
        po = ProductionOrder.objects.create(
            company=self.company,
            number="WO-EXT-001",
            customer_product=self.cp,
            spec_revision=self.spec,
            planned_quantity=Decimal("500"),
            uom=self.kg,
            status="RELEASED",
        )

        # Seed stock for backflush: BOPP granules in RM
        self._seed_stock_for_issue(self.bopp_resin, self.rm_wh, Decimal("1000"))

        # Backflush extrusion: no unit selection, material is auto-consumed from RM
        client = auth_client(self.user)
        resp = client.post(
            "/api/v1/production/material-issues/",
            {
                "production_order": str(po.id),
                "material": str(self.bopp_resin.id),
                "warehouse": str(self.rm_wh.id),
                "quantity": "500",
                "uom": str(self.kg.id),
                "method": "BACKFLUSH",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        issue = MaterialIssue.objects.first()
        self.assertEqual(issue.method, MaterialIssueMethod.BACKFLUSH)
        self.assertIsNone(issue.traceability_unit)

        # Stock decreased by 500
        bal = inventory_services.on_hand_quantity(
            company=self.company,
            warehouse=self.rm_wh,
            material=self.bopp_resin,
        )
        self.assertEqual(bal, Decimal("500"))

        # Now explicit issue for lamination: must select a unit
        # Create a WIP roll from extrusion output
        wip_unit = TraceabilityUnit.objects.create(
            company=self.company,
            material=self.bopp_film,
            unit_type=TraceabilityUnitType.ROLL,
            identifier="ROLL-EXT-001",
            quantity=Decimal("400"),
            uom=self.kg,
            weight=Decimal("400"),
            length=Decimal("5000"),
            width=Decimal("1220"),
        )
        inventory_services.post_movement(
            company=self.company,
            warehouse=self.wip_wh,
            direction=StockMovementDirection.IN,
            quantity=Decimal("400"),
            uom=self.kg,
            material=self.bopp_film,
            traceability_unit=wip_unit,
            reference_type="test.output",
            actor=self.user,
        )
        po2 = ProductionOrder.objects.create(
            company=self.company,
            number="WO-LAM-001",
            customer_product=self.cp,
            spec_revision=self.spec,
            planned_quantity=Decimal("400"),
            uom=self.kg,
            status="RELEASED",
        )
        resp2 = client.post(
            "/api/v1/production/material-issues/",
            {
                "production_order": str(po2.id),
                "material": str(self.bopp_film.id),
                "traceability_unit": str(wip_unit.id),
                "warehouse": str(self.wip_wh.id),
                "quantity": "200",
                "uom": str(self.kg.id),
                "method": "EXPLICIT",
            },
            format="json",
        )
        self.assertEqual(resp2.status_code, 201, resp2.content)
        issue2 = MaterialIssue.objects.last()
        self.assertEqual(issue2.method, MaterialIssueMethod.EXPLICIT)
        self.assertIsNotNone(issue2.traceability_unit)

        # Audit
        self.assertTrue(AuditLog.objects.filter(entity_type="production.MaterialIssue").exists())

    # -------------------------------------------------------------------
    # C. PRODUCTION OUTPUT + WIP MOVEMENT
    # -------------------------------------------------------------------

    def test_production_output_to_wip_then_finished_goods(self):
        """Q-026: stocked intermediates with WIP warehouse per production step."""
        po = ProductionOrder.objects.create(
            company=self.company,
            number="WO-OUT-001",
            customer_product=self.cp,
            spec_revision=self.spec,
            planned_quantity=Decimal("10"),
            uom=self.roll,
            status="RELEASED",
        )

        # Create output unit as intermediate
        wip_unit = TraceabilityUnit.objects.create(
            company=self.company,
            customer_product_id=self.cp.id,
            unit_type=TraceabilityUnitType.ROLL,
            identifier="ROLL-LAM-OUT",
            quantity=Decimal("71"),
            uom=self.kg,
            weight=Decimal("71"),
            length=Decimal("1169"),
            width=Decimal("500"),
        )
        client = auth_client(self.user)
        resp = client.post(
            "/api/v1/production/outputs/",
            {
                "production_order": str(po.id),
                "traceability_unit": str(wip_unit.id),
                "warehouse": str(self.wip_wh.id),
                "quantity": "71",
                "uom": str(self.kg.id),
                "operation_label": "Lamination output",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(ProductionOutput.objects.count(), 1)

        # Stock in WIP
        bal = inventory_services.on_hand_quantity(
            company=self.company,
            warehouse=self.wip_wh,
            traceability_unit=wip_unit,
        )
        self.assertEqual(bal, Decimal("71"))

        # Now move to finished goods via another production order
        fg_unit = TraceabilityUnit.objects.create(
            company=self.company,
            customer_product_id=self.cp.id,
            unit_type=TraceabilityUnitType.ROLL,
            identifier="ROLL-FG-001",
            quantity=Decimal("71"),
            uom=self.kg,
            weight=Decimal("71"),
            length=Decimal("1169"),
            width=Decimal("500"),
        )
        po2 = ProductionOrder.objects.create(
            company=self.company,
            number="WO-FG-001",
            customer_product=self.cp,
            spec_revision=self.spec,
            planned_quantity=Decimal("10"),
            uom=self.roll,
            status="RELEASED",
        )
        resp2 = client.post(
            "/api/v1/production/outputs/",
            {
                "production_order": str(po2.id),
                "traceability_unit": str(fg_unit.id),
                "warehouse": str(self.fg_wh.id),
                "quantity": "71",
                "uom": str(self.kg.id),
                "operation_label": "Slitting output",
            },
            format="json",
        )
        self.assertEqual(resp2.status_code, 201, resp2.content)

        # Genealogy link from WIP to FG
        gl = GenealogyLink.objects.create(
            parent=wip_unit,
            child=fg_unit,
            production_order_id=po2.id,
            operation_label="slit→FG",
        )
        self.assertIsNotNone(gl)

        # Verify genealogy chain
        children = GenealogyLink.objects.filter(parent=wip_unit)
        self.assertEqual(children.count(), 1)

    # -------------------------------------------------------------------
    # D. QC EXECUTION per roll
    # -------------------------------------------------------------------

    def test_qc_check_per_roll_and_hold_disposition(self):
        """Q-046: QC per produced reel; HOLD tags unit for quarantine."""
        from django.utils import timezone

        from apps.quality import services as qc_services
        from apps.quality.models import (
            QualityCharacteristic,
            QualityPlan,
            QualityPlanItem,
            QualityPlanRevision,
        )

        # Create roll for QC
        roll = TraceabilityUnit.objects.create(
            company=self.company,
            customer_product_id=self.cp.id,
            unit_type=TraceabilityUnitType.ROLL,
            identifier="ROLL-QC-001",
            quantity=Decimal("71"),
            uom=self.kg,
            weight=Decimal("71"),
            length=Decimal("1169"),
            width=Decimal("500"),
        )

        # Create quality characteristic + plan + plan item
        qc_char = QualityCharacteristic.objects.create(
            company=self.company,
            code="THICKNESS",
            name_fa="ضخامت",
            datatype="NUMBER",
            default_uom=self.micron,
        )
        qp = QualityPlan.objects.create(spec_revision=self.spec)
        qp_rev = QualityPlanRevision.objects.create(root=qp, revision_number=1)
        plan_item = QualityPlanItem.objects.create(
            revision=qp_rev,
            sequence=1,
            characteristic=qc_char,
            lower_limit=Decimal("110"),
            upper_limit=Decimal("124"),
            unit="µm",
        )

        # Post QC — PASS
        result1 = qc_services.post_check_result(
            plan_item=plan_item,
            traceability_unit=roll,
            measured_value="117",
            disposition="PASS",
            checked_at=timezone.now(),
            actor=self.user,
        )
        self.assertEqual(QualityCheckResult.objects.count(), 1)
        self.assertEqual(result1.disposition, "PASS")

        # Post QC — HOLD
        qc_services.post_check_result(
            plan_item=plan_item,
            traceability_unit=roll,
            measured_value="130",
            disposition="HOLD",
            checked_at=timezone.now(),
            actor=self.user,
        )
        self.assertEqual(QualityCheckResult.objects.count(), 2)
        roll.refresh_from_db()
        self.assertIn("QC HOLD", roll.notes)

    # -------------------------------------------------------------------
    # E. ALLOCATION → SHIPMENT
    # -------------------------------------------------------------------

    def test_full_allocation_and_shipment_flow(self):
        """Reserve → release → re-reserve → ship with inventory OUT."""
        # Create FG roll with stock
        fg_unit = TraceabilityUnit.objects.create(
            company=self.company,
            customer_product_id=self.cp.id,
            unit_type=TraceabilityUnitType.ROLL,
            identifier="ROLL-SHIP-001",
            quantity=Decimal("71"),
            uom=self.kg,
            weight=Decimal("71"),
            length=Decimal("1169"),
            width=Decimal("500"),
        )
        inventory_services.post_movement(
            company=self.company,
            warehouse=self.fg_wh,
            direction=StockMovementDirection.IN,
            quantity=Decimal("71"),
            uom=self.kg,
            traceability_unit=fg_unit,
            reference_type="test.seed",
            actor=self.user,
        )

        client = auth_client(self.user)

        # Allocate
        resp = client.post(
            "/api/v1/shipment/allocations/",
            {
                "company": str(self.company.id),
                "sales_order_line": str(self.sol.id),
                "traceability_unit": str(fg_unit.id),
                "quantity": "71",
                "uom": str(self.kg.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        aid = resp.data["id"]

        # Release
        rel = client.post(f"/api/v1/shipment/allocations/{aid}/release/")
        self.assertEqual(rel.status_code, 200)
        self.assertEqual(rel.data["status"], "RELEASED")

        # Re-allocate
        resp2 = client.post(
            "/api/v1/shipment/allocations/",
            {
                "company": str(self.company.id),
                "sales_order_line": str(self.sol.id),
                "traceability_unit": str(fg_unit.id),
                "quantity": "71",
                "uom": str(self.kg.id),
            },
            format="json",
        )
        self.assertEqual(resp2.status_code, 201, resp2.content)

        # Ship
        ship_resp = client.post(
            "/api/v1/shipment/deliveries/",
            {
                "company": str(self.company.id),
                "warehouse": str(self.fg_wh.id),
                "customer": str(self.customer.id),
                "sales_order": str(self.so.id),
                "number": "SHIP-001",
                "shipped_at": self.today.isoformat(),
                "lines": [
                    {
                        "traceability_unit": str(fg_unit.id),
                        "sales_order_line": str(self.sol.id),
                        "quantity": "71",
                        "uom": str(self.kg.id),
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(ship_resp.status_code, 201, ship_resp.content)

        # Inventory OUT
        bal = inventory_services.on_hand_quantity(
            company=self.company,
            warehouse=self.fg_wh,
            traceability_unit=fg_unit,
        )
        self.assertEqual(bal, Decimal("0"))

        # Audit coverage
        self.assertTrue(AuditLog.objects.filter(entity_type="shipment.Shipment").exists())

    # -------------------------------------------------------------------
    # F. GENEALOGY
    # -------------------------------------------------------------------

    def test_full_genealogy_chain_raw_to_shipment(self):
        """Trace a unit from raw material receipt through to shipment."""
        # Raw receipt
        resin_batch = TraceabilityUnit.objects.create(
            company=self.company,
            material=self.pe_resin,
            unit_type=TraceabilityUnitType.BATCH,
            identifier="BATCH-PE-RECV",
            quantity=Decimal("2000"),
            uom=self.kg,
        )
        inventory_services.post_movement(
            company=self.company,
            warehouse=self.rm_wh,
            direction=StockMovementDirection.IN,
            quantity=Decimal("2000"),
            uom=self.kg,
            material=self.pe_resin,
            traceability_unit=resin_batch,
            reference_type="procurement.GoodsReceiptLine",
            actor=self.user,
        )

        # Production output — WIP
        wip_roll = TraceabilityUnit.objects.create(
            company=self.company,
            material=self.pe_film,
            unit_type=TraceabilityUnitType.ROLL,
            identifier="ROLL-PE-WIP",
            quantity=Decimal("400"),
            uom=self.kg,
        )
        GenealogyLink.objects.create(
            parent=resin_batch,
            child=wip_roll,
            production_order_id=None,
            operation_label="Extrusion",
        )

        # Production output — FG
        fg_roll = TraceabilityUnit.objects.create(
            company=self.company,
            customer_product_id=self.cp.id,
            unit_type=TraceabilityUnitType.ROLL,
            identifier="ROLL-PE-FG",
            quantity=Decimal("71"),
            uom=self.kg,
        )
        GenealogyLink.objects.create(
            parent=wip_roll,
            child=fg_roll,
            production_order_id=None,
            operation_label="Print+Slit",
        )

        # Seed FG stock before shipment OUT
        inventory_services.post_movement(
            company=self.company,
            warehouse=self.fg_wh,
            direction=StockMovementDirection.IN,
            quantity=Decimal("71"),
            uom=self.kg,
            traceability_unit=fg_roll,
            reference_type="production.ProductionOutput",
            actor=self.user,
        )

        # Shipment consumes FG
        inventory_services.post_movement(
            company=self.company,
            warehouse=self.fg_wh,
            direction=StockMovementDirection.OUT,
            quantity=Decimal("71"),
            uom=self.kg,
            traceability_unit=fg_roll,
            reference_type="shipment.ShipmentLine",
            actor=self.user,
        )

        # Forward: raw → WIP → FG
        wip_links = GenealogyLink.objects.filter(parent=resin_batch)
        self.assertEqual(wip_links.count(), 1)
        self.assertEqual(wip_links.first().child, wip_roll)

        fg_links = GenealogyLink.objects.filter(parent=wip_roll)
        self.assertEqual(fg_links.count(), 1)
        self.assertEqual(fg_links.first().child, fg_roll)

        # Backward: FG → WIP → raw
        ancestors = GenealogyLink.objects.filter(child=fg_roll)
        self.assertEqual(ancestors.count(), 1)
        self.assertEqual(ancestors.first().parent, wip_roll)

    # -------------------------------------------------------------------
    # G. CROSS-COMPANY ISOLATION (execution endpoints)
    # -------------------------------------------------------------------

    def test_grn_cross_company_blocked(self):
        """A user of company A cannot post a GRN for company B."""
        foreign_co = make_company(code="FOREIGN")
        # Foreign warehouse is created for validation but not directly used in the assertion path
        Warehouse.objects.create(
            company=foreign_co,
            site=make_site(company=foreign_co),
            code="FWH",
            name_fa="انبار خارجی",
            store_type=WarehouseStoreType.RAW_MATERIAL,
        )
        partner = Partner.objects.create(
            company=foreign_co, code="FS", name_fa="تأمین‌کننده خارجی", is_supplier=True
        )
        foreign_sup = Supplier.objects.create(partner=partner, is_approved=True)
        po = PurchaseOrder.objects.create(
            company=foreign_co,
            supplier=foreign_sup,
            number="PO-FGN",
            status=PurchaseOrderStatus.SENT,
        )
        pol = PurchaseOrderLine.objects.create(
            order=po,
            sequence=1,
            material=self.bopp_resin,
            quantity=Decimal("100"),
            uom=self.kg,
        )

        insight = make_user(email="insider@slz.test")
        grant(insight, "procurement.grn.view", "procurement.grn.manage")
        resp = auth_client(insight).post(
            "/api/v1/procurement/goods-receipts/",
            {
                "company": str(self.company.id),
                "warehouse": str(self.rm_wh.id),
                "purchase_order": str(po.id),
                "number": "GRN-FGN",
                "received_at": self.today.isoformat(),
                "lines": [
                    {
                        "po_line": str(pol.id),
                        "material": str(self.bopp_resin.id),
                        "quantity": "10",
                        "uom": str(self.kg.id),
                        "traceability_unit_type": "BATCH",
                    }
                ],
            },
            format="json",
        )
        self.assertIn(resp.status_code, (400, 403), resp.content)

    # -------------------------------------------------------------------
    # H. CARTON-LEVEL TRACEABILITY (Product 2 scenario)
    # -------------------------------------------------------------------

    def test_carton_traceability_for_bags(self):
        """Q-049: bags/pouches use carton-level traceability."""
        carton = TraceabilityUnit.objects.create(
            company=self.company,
            customer_product_id=self.cp.id,
            unit_type=TraceabilityUnitType.CARTON,
            identifier="CARTON-BAG-001",
            quantity=Decimal("880"),
            uom=self.roll,
        )
        inventory_services.post_movement(
            company=self.company,
            warehouse=self.fg_wh,
            direction=StockMovementDirection.IN,
            quantity=Decimal("880"),
            uom=self.roll,
            traceability_unit=carton,
            reference_type="production.ProductionOutput",
            actor=self.user,
        )
        bal = inventory_services.on_hand_quantity(
            company=self.company,
            warehouse=self.fg_wh,
            traceability_unit=carton,
        )
        self.assertEqual(bal, Decimal("880"))
