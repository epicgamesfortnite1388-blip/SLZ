"""Product Engineering tests: customer product, spec lifecycle, child rules, RBAC.

Covers the CONFIRMED versioning mechanics (draft -> activate -> supersede,
immutability of non-DRAFT revisions) and structural validation (layer ordering,
ink subtype). No OPEN business rule (trigger/approver/SKU-derivation) is tested
because none is implemented.
"""

from __future__ import annotations

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
from apps.core.tests.factories import auth_client, grant, make_company, make_user
from apps.engineering.models import CustomerProduct, SpecificationRevision
from apps.partners.models import Partner


def build_catalog(company):
    """Create the minimal catalog prerequisites for engineering tests."""
    uom = UnitOfMeasure.objects.create(code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS)
    group = ProductGroup.objects.create(code="FOOD", name_fa="بسته‌بندی غذایی")
    ptype = ProductType.objects.create(code="FILM", name_fa="فیلم")
    pclass = ProductClass.objects.create(product_type=ptype, code="LAM", name_fa="لمینت")
    family = ProductFamily.objects.create(product_class=pclass, code="POUCH", name_fa="پوچ")
    customer = Partner.objects.create(
        company=company, code="C-001", name_fa="مشتری", is_customer=True
    )
    ink = Material.objects.create(
        company=company,
        code="INK-01",
        name_fa="مرکب مشکی",
        subtype=MaterialSubtype.INK,
        base_uom=uom,
    )
    resin = Material.objects.create(
        company=company,
        code="RES-01",
        name_fa="گرانول",
        subtype=MaterialSubtype.RESIN_MASTERBATCH,
        base_uom=uom,
    )
    return {
        "uom": uom,
        "group": group,
        "family": family,
        "customer": customer,
        "ink": ink,
        "resin": resin,
    }


class CustomerProductApiTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.cat = build_catalog(self.company)
        self.user = make_user()
        grant(
            self.user,
            "engineering.customerproduct.view",
            "engineering.customerproduct.manage",
        )
        self.client = auth_client(self.user)

    def _payload(self, **overrides):
        data = {
            "company": str(self.company.id),
            "customer": str(self.cat["customer"].id),
            "code": "CP-001",
            "name_fa": "پوچ قهوه یک کیلویی",
            "product_group": str(self.cat["group"].id),
            "family": str(self.cat["family"].id),
            "base_uom": str(self.cat["uom"].id),
        }
        data.update(overrides)
        return data

    def test_create_persists_and_audits(self):
        resp = self.client.post(
            "/api/v1/engineering/customer-products/", self._payload(), format="json"
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        cp = CustomerProduct.objects.get(code="CP-001")
        self.assertEqual(cp.created_by_id, self.user.id)
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="engineering.CustomerProduct",
                entity_id=str(cp.id),
            ).exists()
        )

    def test_duplicate_code_per_company_rejected(self):
        self.client.post("/api/v1/engineering/customer-products/", self._payload(), format="json")
        dup = self.client.post(
            "/api/v1/engineering/customer-products/", self._payload(), format="json"
        )
        self.assertEqual(dup.status_code, 400, dup.content)


class SpecificationLifecycleTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.cat = build_catalog(self.company)
        self.user = make_user()
        grant(
            self.user,
            "engineering.specification.view",
            "engineering.specification.manage",
        )
        self.client = auth_client(self.user)
        self.cp = CustomerProduct.objects.create(
            company=self.company,
            customer=self.cat["customer"],
            code="CP-1",
            name_fa="محصول",
            product_group=self.cat["group"],
            family=self.cat["family"],
            base_uom=self.cat["uom"],
        )

    def _create_draft(self, **overrides):
        data = {"root": str(self.cp.id), "spec_format": "ROLL_STOCK"}
        data.update(overrides)
        return self.client.post("/api/v1/engineering/specifications/", data, format="json")

    def test_draft_gets_monotonic_revision_number(self):
        r1 = self._create_draft()
        r2 = self._create_draft()
        self.assertEqual(r1.status_code, 201, r1.content)
        self.assertEqual(r1.data["revision_number"], 1)
        self.assertEqual(r1.data["status"], "DRAFT")
        self.assertEqual(r2.data["revision_number"], 2)

    def test_activate_supersedes_prior_active(self):
        r1 = self._create_draft()
        r2 = self._create_draft()
        id1, id2 = r1.data["id"], r2.data["id"]

        a1 = self.client.post(f"/api/v1/engineering/specifications/{id1}/activate/")
        self.assertEqual(a1.status_code, 200, a1.content)
        rev1 = SpecificationRevision.objects.get(id=id1)
        self.assertEqual(rev1.status, "ACTIVE")
        self.assertIsNotNone(rev1.effective_from)

        a2 = self.client.post(f"/api/v1/engineering/specifications/{id2}/activate/")
        self.assertEqual(a2.status_code, 200, a2.content)
        rev1.refresh_from_db()
        rev2 = SpecificationRevision.objects.get(id=id2)
        self.assertEqual(rev1.status, "SUPERSEDED")
        self.assertIsNotNone(rev1.effective_to)
        self.assertEqual(rev2.status, "ACTIVE")
        self.assertTrue(
            AuditLog.objects.filter(
                action="UPDATE",
                entity_type="engineering.SpecificationRevision",
                entity_id=id2,
            ).exists()
        )

    def test_cannot_edit_active_header(self):
        r1 = self._create_draft()
        rid = r1.data["id"]
        self.client.post(f"/api/v1/engineering/specifications/{rid}/activate/")
        resp = self.client.patch(
            f"/api/v1/engineering/specifications/{rid}/",
            {"bag_type": "STAND_UP"},
            format="json",
        )
        self.assertEqual(resp.status_code, 409, resp.content)

    def test_cannot_activate_non_draft(self):
        r1 = self._create_draft()
        rid = r1.data["id"]
        self.client.post(f"/api/v1/engineering/specifications/{rid}/activate/")
        again = self.client.post(f"/api/v1/engineering/specifications/{rid}/activate/")
        self.assertEqual(again.status_code, 409, again.content)


class SpecChildRuleTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.cat = build_catalog(self.company)
        self.user = make_user()
        grant(
            self.user,
            "engineering.specification.view",
            "engineering.specification.manage",
        )
        self.client = auth_client(self.user)
        self.cp = CustomerProduct.objects.create(
            company=self.company,
            customer=self.cat["customer"],
            code="CP-2",
            name_fa="محصول",
            product_group=self.cat["group"],
            family=self.cat["family"],
            base_uom=self.cat["uom"],
        )
        self.draft = self.client.post(
            "/api/v1/engineering/specifications/",
            {
                "root": str(self.cp.id),
                "spec_format": "ROLL_STOCK",
                "print_process": "FLEXO_SURFACE",
            },
            format="json",
        ).data

    def _layer(self, **overrides):
        data = {
            "revision": self.draft["id"],
            "sequence": 1,
            "material": str(self.cat["resin"].id),
            "function": "SUBSTRATE",
        }
        data.update(overrides)
        return data

    def test_layer_sequence_unique_per_revision(self):
        first = self.client.post("/api/v1/engineering/spec-layers/", self._layer(), format="json")
        self.assertEqual(first.status_code, 201, first.content)
        dup = self.client.post("/api/v1/engineering/spec-layers/", self._layer(), format="json")
        self.assertEqual(dup.status_code, 400, dup.content)

    def test_cannot_add_layer_to_active_revision(self):
        rid = self.draft["id"]
        self.client.post(f"/api/v1/engineering/specifications/{rid}/activate/")
        resp = self.client.post(
            "/api/v1/engineering/spec-layers/", self._layer(sequence=2), format="json"
        )
        self.assertEqual(resp.status_code, 409, resp.content)

    def test_color_ink_must_be_ink_subtype(self):
        bad = self.client.post(
            "/api/v1/engineering/spec-colors/",
            {
                "revision": self.draft["id"],
                "sequence": 1,
                "color_name": "Black",
                "ink": str(self.cat["resin"].id),
            },
            format="json",
        )
        self.assertEqual(bad.status_code, 400, bad.content)
        good = self.client.post(
            "/api/v1/engineering/spec-colors/",
            {
                "revision": self.draft["id"],
                "sequence": 1,
                "color_name": "Black",
                "ink": str(self.cat["ink"].id),
            },
            format="json",
        )
        self.assertEqual(good.status_code, 201, good.content)

    def test_can_delete_layer_of_draft_revision(self):
        created = self.client.post("/api/v1/engineering/spec-layers/", self._layer(), format="json")
        self.assertEqual(created.status_code, 201, created.content)
        layer_id = created.data["id"]
        resp = self.client.delete(f"/api/v1/engineering/spec-layers/{layer_id}/")
        self.assertEqual(resp.status_code, 204, resp.content)

    def test_cannot_delete_layer_of_active_revision(self):
        created = self.client.post("/api/v1/engineering/spec-layers/", self._layer(), format="json")
        self.assertEqual(created.status_code, 201, created.content)
        layer_id = created.data["id"]
        rid = self.draft["id"]
        self.client.post(f"/api/v1/engineering/specifications/{rid}/activate/")
        resp = self.client.delete(f"/api/v1/engineering/spec-layers/{layer_id}/")
        self.assertEqual(resp.status_code, 409, resp.content)


class EngineeringPermissionTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.cat = build_catalog(self.company)

    def test_view_only_cannot_create_customer_product(self):
        user = make_user(email="viewer@slz.test")
        grant(user, "engineering.customerproduct.view")
        client = auth_client(user)
        resp = client.post(
            "/api/v1/engineering/customer-products/",
            {
                "company": str(self.company.id),
                "customer": str(self.cat["customer"].id),
                "code": "X1",
                "name_fa": "x",
                "product_group": str(self.cat["group"].id),
                "family": str(self.cat["family"].id),
                "base_uom": str(self.cat["uom"].id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_unpermitted_user_cannot_list_specifications(self):
        client = auth_client(make_user(email="nobody@slz.test"))
        resp = client.get("/api/v1/engineering/specifications/")
        self.assertEqual(resp.status_code, 403, resp.content)
