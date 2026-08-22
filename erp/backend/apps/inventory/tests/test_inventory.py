"""Inventory tests for warehouse masters and confirmed traceability records.

The traceability tests cover serialized rolls, batches, carton/pallet handling
units, and the append-only movement/genealogy foundation. Receipt, valuation,
reservation, QC release, and recall workflows remain outside this slice.
"""

from __future__ import annotations

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.catalog.models import Material, MaterialSubtype, UnitOfMeasure, UomDimension
from apps.core.tests.factories import auth_client, grant, make_company, make_superuser, make_user
from apps.inventory.models import (
    TraceabilityUnit,
    TraceabilityUnitType,
    Warehouse,
    WarehouseAccess,
    WarehouseStoreType,
)


class WarehouseApiTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.user = make_user()
        grant(self.user, "inventory.warehouse.view", "inventory.warehouse.manage")
        self.client = auth_client(self.user)

    def test_create_warehouse_persists_and_audits(self):
        resp = self.client.post(
            "/api/v1/inventory/warehouses/",
            {
                "company": str(self.company.id),
                "code": "WH-RM",
                "name_fa": "انبار مواد اولیه",
                "store_type": WarehouseStoreType.RAW_MATERIAL,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        wh = Warehouse.objects.get(code="WH-RM")
        self.assertEqual(wh.store_type, WarehouseStoreType.RAW_MATERIAL)
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="inventory.Warehouse",
                entity_id=str(wh.id),
            ).exists()
        )

    def test_store_type_defaults_to_general(self):
        resp = self.client.post(
            "/api/v1/inventory/warehouses/",
            {"company": str(self.company.id), "code": "WH-1", "name_fa": "انبار"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["store_type"], WarehouseStoreType.GENERAL)

    def test_special_store_type_accepted(self):
        resp = self.client.post(
            "/api/v1/inventory/warehouses/",
            {
                "company": str(self.company.id),
                "code": "WH-CLICHE",
                "name_fa": "انبار کلیشه",
                "store_type": WarehouseStoreType.CLICHE,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["store_type"], WarehouseStoreType.CLICHE)

    def test_invalid_store_type_rejected(self):
        resp = self.client.post(
            "/api/v1/inventory/warehouses/",
            {
                "company": str(self.company.id),
                "code": "WH-X",
                "name_fa": "انبار",
                "store_type": "NOT_A_TYPE",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_duplicate_code_per_company_rejected(self):
        payload = {
            "company": str(self.company.id),
            "code": "WH-DUP",
            "name_fa": "انبار",
        }
        self.client.post("/api/v1/inventory/warehouses/", payload, format="json")
        dup = self.client.post("/api/v1/inventory/warehouses/", payload, format="json")
        self.assertEqual(dup.status_code, 400, dup.content)


class WarehouseAccessApiTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.admin = make_user()
        grant(
            self.admin,
            "inventory.warehouseaccess.view",
            "inventory.warehouseaccess.manage",
        )
        self.client = auth_client(self.admin)
        self.warehouse = Warehouse.objects.create(
            company=self.company, code="WH-A", name_fa="انبار الف"
        )
        self.member = make_user(email="member@slz.test")

    def test_grant_access_persists_and_audits(self):
        resp = self.client.post(
            "/api/v1/inventory/warehouse-access/",
            {
                "warehouse": str(self.warehouse.id),
                "user": str(self.member.id),
                "access_level": "OPERATE",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        grant_row = WarehouseAccess.objects.get(warehouse=self.warehouse, user=self.member)
        self.assertEqual(grant_row.access_level, "OPERATE")
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="inventory.WarehouseAccess",
                entity_id=str(grant_row.id),
            ).exists()
        )

    def test_duplicate_grant_rejected(self):
        payload = {
            "warehouse": str(self.warehouse.id),
            "user": str(self.member.id),
        }
        self.client.post("/api/v1/inventory/warehouse-access/", payload, format="json")
        dup = self.client.post("/api/v1/inventory/warehouse-access/", payload, format="json")
        self.assertEqual(dup.status_code, 400, dup.content)

    def test_access_level_defaults_to_view(self):
        resp = self.client.post(
            "/api/v1/inventory/warehouse-access/",
            {"warehouse": str(self.warehouse.id), "user": str(self.member.id)},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["access_level"], "VIEW")


class InventoryPermissionTests(TestCase):
    def setUp(self):
        self.company = make_company()

    def test_view_only_cannot_create_warehouse(self):
        user = make_user(email="viewer@slz.test")
        grant(user, "inventory.warehouse.view")
        client = auth_client(user)
        resp = client.post(
            "/api/v1/inventory/warehouses/",
            {"company": str(self.company.id), "code": "X", "name_fa": "x"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_unpermitted_user_cannot_list_warehouses(self):
        client = auth_client(make_user(email="nobody@slz.test"))
        resp = client.get("/api/v1/inventory/warehouses/")
        self.assertEqual(resp.status_code, 403, resp.content)


class TraceabilityUnitApiTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.user = make_superuser(email="traceability-admin@slz.test")
        self.client = auth_client(self.user)
        self.uom = UnitOfMeasure.objects.create(
            code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS
        )
        self.resin = Material.objects.create(
            company=self.company,
            code="PE-001",
            name_fa="گرانول PE",
            subtype=MaterialSubtype.RESIN_MASTERBATCH,
            traceability_mode="BATCH",
            base_uom=self.uom,
        )
        self.film = Material.objects.create(
            company=self.company,
            code="FILM-001",
            name_fa="فیلم تولیدی",
            subtype=MaterialSubtype.SEMI_FINISHED,
            traceability_mode="SERIALIZED_ROLL",
            base_uom=self.uom,
        )

    def test_material_mode_requires_matching_unit_type(self):
        ok = self.client.post(
            "/api/v1/inventory/traceability-units/",
            {
                "company": str(self.company.id),
                "material": str(self.resin.id),
                "unit_type": TraceabilityUnitType.BATCH,
                "identifier": "BATCH-001",
                "quantity": "100.000000",
                "uom": str(self.uom.id),
            },
            format="json",
        )
        self.assertEqual(ok.status_code, 201, ok.content)
        bad = self.client.post(
            "/api/v1/inventory/traceability-units/",
            {
                "company": str(self.company.id),
                "material": str(self.film.id),
                "unit_type": TraceabilityUnitType.BATCH,
                "identifier": "WRONG-001",
                "quantity": "10.000000",
                "uom": str(self.uom.id),
            },
            format="json",
        )
        self.assertEqual(bad.status_code, 400, bad.content)

    def test_pallet_parent_and_serialized_roll_are_preserved(self):
        roll = self.client.post(
            "/api/v1/inventory/traceability-units/",
            {
                "company": str(self.company.id),
                "material": str(self.film.id),
                "unit_type": TraceabilityUnitType.ROLL,
                "identifier": "ROLL-001",
                "quantity": "50.000000",
                "uom": str(self.uom.id),
                "weight": "52.500000",
                "length": "500.000000",
                "width": "500.000000",
                "core": "76.000000",
            },
            format="json",
        )
        self.assertEqual(roll.status_code, 201, roll.content)
        pallet = self.client.post(
            "/api/v1/inventory/traceability-units/",
            {
                "company": str(self.company.id),
                "parent": roll.data["id"],
                "unit_type": TraceabilityUnitType.PALLET,
                "identifier": "PALLET-001",
            },
            format="json",
        )
        self.assertEqual(pallet.status_code, 201, pallet.content)
        self.assertEqual(
            str(TraceabilityUnit.objects.get(identifier="PALLET-001").parent_id),
            roll.data["id"],
        )
