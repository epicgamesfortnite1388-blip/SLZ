"""Direct POST /inventory/movements/ must respect ledger guards.

Regression for a critical integration bug: the viewset inherited a raw
``create_from_serializer`` save that bypassed ``post_movement`` entirely,
allowing phantom IN stock and negative balances to any holder of
``inventory.movement.manage``. The endpoint is now an explicit manual
**adjustment** path routed through the sanctioned service.
"""

from __future__ import annotations

from django.test import TestCase

from apps.catalog.models import Material, UnitOfMeasure, UomDimension
from apps.core.tests.factories import auth_client, grant, make_company, make_site, make_user
from apps.inventory.models import StockMovement, Warehouse, WarehouseStoreType


class DirectMovementPostingGuardTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.site = make_site(company=self.company)
        self.user = make_user()
        grant(self.user, "inventory.movement.view", "inventory.movement.manage")
        self.client = auth_client(self.user)
        self.uom = UnitOfMeasure.objects.create(
            code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS
        )
        self.material = Material.objects.create(
            company=self.company, code="RM-X", name_fa="ماده", base_uom=self.uom
        )
        self.warehouse = Warehouse.objects.create(
            company=self.company,
            site=self.site,
            code="RM-D",
            name_fa="انبار",
            store_type=WarehouseStoreType.RAW_MATERIAL,
        )
        self.quarantine = Warehouse.objects.create(
            company=self.company,
            site=self.site,
            code="QUA-D",
            name_fa="قرنطینه",
            store_type=WarehouseStoreType.QUARANTINE,
        )

    def _payload(self, **overrides):
        payload = {
            "company": str(self.company.id),
            "warehouse": str(self.warehouse.id),
            "material": str(self.material.id),
            "direction": "OUT",
            "quantity": "5",
            "uom": str(self.uom.id),
        }
        payload.update(overrides)
        return payload

    def test_out_without_stock_is_rejected_via_api(self):
        resp = self.client.post("/api/v1/inventory/movements/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "inventory.insufficient_stock")
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_issue_from_quarantine_store_is_rejected_via_api(self):
        resp = self.client.post(
            "/api/v1/inventory/movements/",
            self._payload(warehouse=str(self.quarantine.id)),
            format="json",
        )
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["code"], "inventory.quarantine_issue")

    def test_valid_adjustment_posts_with_server_reference_type(self):
        resp = self.client.post(
            "/api/v1/inventory/movements/", self._payload(direction="IN"), format="json"
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        movement = StockMovement.objects.get()
        # Spoofing protection: clients cannot claim a domain-document reference.
        self.assertEqual(movement.reference_type, "inventory.Adjustment")
        self.assertIsNone(movement.reference_id)

    def test_zero_and_negative_quantities_rejected(self):
        for qty in ("0", "-3"):
            with self.subTest(qty=qty):
                resp = self.client.post(
                    "/api/v1/inventory/movements/", self._payload(quantity=qty), format="json"
                )
                self.assertEqual(resp.status_code, 422)
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_raw_transfer_direction_rejected_via_api(self):
        """A direct POST with direction=TRANSFER must fail: transfers are an
        atomic OUT+IN pair via the dedicated transfer action."""
        resp = self.client.post(
            "/api/v1/inventory/movements/",
            self._payload(direction="TRANSFER"),
            format="json",
        )
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_transfer_action_moves_stock_between_warehouses(self):
        from apps.inventory import services as inventory_services
        from apps.inventory.models import StockMovementDirection

        target = Warehouse.objects.create(
            company=self.company,
            site=self.site,
            code="FG-T",
            name_fa="مقصد",
            store_type=WarehouseStoreType.FINISHED_GOODS,
        )
        inventory_services.post_movement(
            company=self.company,
            warehouse=self.warehouse,
            direction=StockMovementDirection.IN,
            quantity=10,
            uom=self.uom,
            material=self.material,
            reference_type="test.seed",
            actor=self.user,
        )
        resp = self.client.post(
            "/api/v1/inventory/movements/transfer/",
            {
                "company": str(self.company.id),
                "from_warehouse": str(self.warehouse.id),
                "to_warehouse": str(target.id),
                "material": str(self.material.id),
                "quantity": "4",
                "uom": str(self.uom.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(StockMovement.objects.filter(direction="OUT").count(), 1)
        self.assertEqual(StockMovement.objects.filter(direction="IN").count(), 2)  # seed + transfer
        self.assertEqual(
            StockMovement.objects.filter(reference_type="inventory.Transfer").count(), 2
        )

    def test_transfer_action_rejects_foreign_company_warehouse(self):
        from apps.core.tests.factories import make_company, make_site

        foreign = make_company(code="FGN")
        foreign_site = make_site(company=foreign)
        foreign_wh = Warehouse.objects.create(
            company=foreign,
            site=foreign_site,
            code="FG-F",
            name_fa="خارجی",
            store_type=WarehouseStoreType.FINISHED_GOODS,
        )
        resp = self.client.post(
            "/api/v1/inventory/movements/transfer/",
            {
                "company": str(self.company.id),
                "from_warehouse": str(self.warehouse.id),
                "to_warehouse": str(foreign_wh.id),
                "material": str(self.material.id),
                "quantity": "1",
                "uom": str(self.uom.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("to_warehouse", resp.json()["error"]["details"])
        self.assertEqual(StockMovement.objects.count(), 0)
