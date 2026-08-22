"""Tooling / cliché asset tests (SR-03): identity, integrity, lifecycle, RBAC.

Covers the CONFIRMED tooling layer only — cliché/sheet/set identity, usage-life
counters, the company-boundary + cliché-store integrity rules, and the guarded
retire/reactivate lifecycle. NO tooling COST model exists to test (OPEN,
Q-004/036, do-not-build-yet #5) and no automatic usage increment (gated Q-046).
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
from apps.engineering.models import CustomerProduct, ToolingAsset
from apps.inventory.models import Warehouse, WarehouseStoreType
from apps.partners.models import Partner


def build_prereqs(company):
    """Customer + product + a cliché store and a non-cliché store."""
    uom = UnitOfMeasure.objects.create(code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS)
    group = ProductGroup.objects.create(code="FOOD", name_fa="بسته‌بندی غذایی")
    ptype = ProductType.objects.create(code="FILM", name_fa="فیلم")
    pclass = ProductClass.objects.create(product_type=ptype, code="LAM", name_fa="لمینت")
    family = ProductFamily.objects.create(product_class=pclass, code="POUCH", name_fa="پوچ")
    customer = Partner.objects.create(
        company=company, code="C-001", name_fa="مشتری", is_customer=True
    )
    product = CustomerProduct.objects.create(
        company=company,
        customer=customer,
        code="CP-001",
        name_fa="پوچ",
        product_group=group,
        family=family,
        base_uom=uom,
    )
    cliche_store = Warehouse.objects.create(
        company=company,
        code="WH-CLICHE",
        name_fa="انبار کلیشه",
        store_type=WarehouseStoreType.CLICHE,
    )
    rm_store = Warehouse.objects.create(
        company=company,
        code="WH-RM",
        name_fa="انبار مواد",
        store_type=WarehouseStoreType.RAW_MATERIAL,
    )
    return {
        "uom": uom,
        "customer": customer,
        "product": product,
        "cliche_store": cliche_store,
        "rm_store": rm_store,
    }


class ToolingAssetTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)
        self.user = make_user()
        grant(self.user, "engineering.tooling.view", "engineering.tooling.manage")
        self.client = auth_client(self.user)

    def _payload(self, **overrides):
        data = {
            "company": str(self.company.id),
            "customer": str(self.p["customer"].id),
            "code": "CL-001",
            "name_fa": "کلیشه محصول",
            "tooling_type": "CLICHE",
        }
        data.update(overrides)
        return data

    def _create(self, **overrides):
        return self.client.post(
            "/api/v1/engineering/tooling-assets/",
            self._payload(**overrides),
            format="json",
        )

    def test_create_defaults_active_and_audits(self):
        resp = self._create()
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["status"], "ACTIVE")
        asset = ToolingAsset.objects.get(code="CL-001")
        self.assertEqual(asset.created_by_id, self.user.id)
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="engineering.ToolingAsset",
                entity_id=str(asset.id),
            ).exists()
        )

    def test_status_is_read_only_on_create(self):
        resp = self._create(status="RETIRED")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["status"], "ACTIVE")

    def test_duplicate_code_per_company_rejected(self):
        self._create()
        dup = self._create()
        self.assertEqual(dup.status_code, 400, dup.content)

    def test_warehouse_must_be_cliche_store(self):
        bad = self._create(warehouse=str(self.p["rm_store"].id))
        self.assertEqual(bad.status_code, 400, bad.content)
        # The standardized error envelope nests field errors under error.details.
        self.assertIn("warehouse", bad.data["error"]["details"])
        good = self._create(warehouse=str(self.p["cliche_store"].id))
        self.assertEqual(good.status_code, 201, good.content)

    def test_customer_product_must_match_company(self):
        other_company = make_company(code="OTHERCO")
        other_product = CustomerProduct.objects.create(
            company=other_company,
            customer=self.p["customer"],
            code="CP-OTHER",
            name_fa="محصول دیگر",
            product_group=self.p["product"].product_group,
            family=self.p["product"].family,
            base_uom=self.p["uom"],
        )
        resp = self._create(customer_product=str(other_product.id))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("customer_product", resp.data["error"]["details"])

    def test_customer_product_must_match_customer(self):
        other_customer = Partner.objects.create(
            company=self.company,
            code="C-002",
            name_fa="مشتری دو",
            is_customer=True,
        )
        other_product = CustomerProduct.objects.create(
            company=self.company,
            customer=other_customer,
            code="CP-OC",
            name_fa="محصول مشتری دیگر",
            product_group=self.p["product"].product_group,
            family=self.p["product"].family,
            base_uom=self.p["uom"],
        )
        resp = self._create(customer_product=str(other_product.id))
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("customer_product", resp.data["error"]["details"])

    def test_is_life_exceeded_computed(self):
        resp = self._create(usage_life_limit=100, usage_count=100)
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertTrue(resp.data["is_life_exceeded"])
        resp2 = self._create(code="CL-002", usage_life_limit=100, usage_count=40)
        self.assertFalse(resp2.data["is_life_exceeded"])
        resp3 = self._create(code="CL-003")
        self.assertFalse(resp3.data["is_life_exceeded"])

    def test_retire_and_reactivate_lifecycle_audits(self):
        aid = self._create().data["id"]
        r = self.client.post(f"/api/v1/engineering/tooling-assets/{aid}/retire/")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["status"], "RETIRED")
        back = self.client.post(f"/api/v1/engineering/tooling-assets/{aid}/reactivate/")
        self.assertEqual(back.status_code, 200, back.content)
        self.assertEqual(back.data["status"], "ACTIVE")
        self.assertTrue(
            AuditLog.objects.filter(
                action="UPDATE",
                entity_type="engineering.ToolingAsset",
                entity_id=aid,
            ).exists()
        )

    def test_retire_when_already_retired_conflicts(self):
        aid = self._create().data["id"]
        self.client.post(f"/api/v1/engineering/tooling-assets/{aid}/retire/")
        again = self.client.post(f"/api/v1/engineering/tooling-assets/{aid}/retire/")
        self.assertEqual(again.status_code, 409, again.content)

    def test_reactivate_when_active_conflicts(self):
        aid = self._create().data["id"]
        resp = self.client.post(f"/api/v1/engineering/tooling-assets/{aid}/reactivate/")
        self.assertEqual(resp.status_code, 409, resp.content)


class ToolingAssetPermissionTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)

    def _payload(self):
        return {
            "company": str(self.company.id),
            "customer": str(self.p["customer"].id),
            "code": "CL-X",
            "name_fa": "کلیشه",
            "tooling_type": "CLICHE",
        }

    def test_view_only_cannot_create(self):
        user = make_user(email="viewer@slz.test")
        grant(user, "engineering.tooling.view")
        client = auth_client(user)
        resp = client.post("/api/v1/engineering/tooling-assets/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_unpermitted_user_cannot_list(self):
        client = auth_client(make_user(email="nobody@slz.test"))
        resp = client.get("/api/v1/engineering/tooling-assets/")
        self.assertEqual(resp.status_code, 403, resp.content)
