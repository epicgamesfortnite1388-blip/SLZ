"""Inventory-foundation tests: warehouses, store types, per-user access, RBAC.

Covers only the CONFIRMED master-data slice that is implemented (SR-10 special
store types + per-user warehouse access). No gated behaviour (stock movements,
lots/rolls, genealogy, kardex, two-stage receipt) is tested because none is
implemented — those are blocked on Q-046 (roll serialization) and related gates.
"""

from __future__ import annotations

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.core.tests.factories import auth_client, grant, make_company, make_user
from apps.inventory.models import Warehouse, WarehouseAccess, WarehouseStoreType


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
