"""Costing engine tests — dated weighted-average valuation.

Covers:
* WA unit-cost calculation from multiple receipt layers
* Dated nature: layers after as_of_date are excluded
* Zero cost when no layers exist
* Immutable layer audit trail
* Issue layer cost at prevailing WA
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.catalog.models import Material, UnitOfMeasure, UomDimension
from apps.core.tests.factories import auth_client, grant, make_company, make_superuser, make_user
from apps.costing import integration, services
from apps.costing.models import CostLayerType


class CostingTestBase(TestCase):
    def setUp(self):
        self.company = make_company()
        self.uom = UnitOfMeasure.objects.create(
            code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS
        )
        self.material = Material.objects.create(
            company=self.company, code="RM-PE", name_fa="پلی‌اتیلن", base_uom=self.uom
        )
        self.user = make_superuser()

    def _receipt(self, qty, uc, d="2026-08-01"):
        return services.post_cost_layer(
            company=self.company,
            material=self.material,
            date=date.fromisoformat(d),
            quantity=Decimal(str(qty)),
            unit_cost=Decimal(str(uc)),
            layer_type=CostLayerType.RECEIPT,
            reference_type="test.receipt",
            actor=self.user,
        )

    def _issue(self, qty, d="2026-08-01"):
        # Issue at current WA cost
        wa = services.wa_unit_cost(
            company=self.company, material=self.material, as_of_date=date.fromisoformat(d)
        )
        return services.post_cost_layer(
            company=self.company,
            material=self.material,
            date=date.fromisoformat(d),
            quantity=Decimal(str(qty)),
            unit_cost=wa,
            layer_type=CostLayerType.ISSUE,
            reference_type="test.issue",
            actor=self.user,
        )


class WaUnitCostTests(CostingTestBase):
    def test_single_receipt_wa_equals_unit_cost(self):
        self._receipt(100, 50)
        wa = services.wa_unit_cost(company=self.company, material=self.material)
        self.assertEqual(wa, Decimal("50"))

    def test_two_receipts_give_weighted_average(self):
        # 100 kg @ $50 + 200 kg @ $80 = $5,000 + $16,000 = $21,000 / 300 = $70
        self._receipt(100, 50, "2026-08-01")
        self._receipt(200, 80, "2026-08-05")
        wa = services.wa_unit_cost(company=self.company, material=self.material)
        self.assertEqual(wa, Decimal("70"))

    def test_dated_wa_excludes_future_layers(self):
        self._receipt(100, 50, "2026-08-01")
        self._receipt(200, 80, "2026-08-10")
        wa = services.wa_unit_cost(
            company=self.company,
            material=self.material,
            as_of_date=date(2026, 8, 5),
        )
        self.assertEqual(wa, Decimal("50"))

    def test_issue_reduces_quantity_but_preserves_cost(self):
        self._receipt(100, 50, "2026-08-01")
        # Issue 40 kg at current WA ($50)
        self._issue(40, "2026-08-02")
        # Remaining: 60 kg at $50 = $3,000 → WA still $50
        wa = services.wa_unit_cost(
            company=self.company,
            material=self.material,
            as_of_date=date(2026, 8, 2),
        )
        self.assertEqual(wa, Decimal("50"))

    def test_three_receipts_one_issue_correct_wa(self):
        # Receipts: 50@$100 + 30@$120 + 20@$90 = $5,000+$3,600+$1,800 = $10,400 / 100 = $104
        self._receipt(50, 100, "2026-08-01")
        self._receipt(30, 120, "2026-08-02")
        self._receipt(20, 90, "2026-08-03")
        wa_before = services.wa_unit_cost(company=self.company, material=self.material)
        self.assertEqual(wa_before, Decimal("104"))

        # Issue 40 kg at $104
        self._issue(40, "2026-08-04")
        # Remaining: 60 kg. Net cost: $10,400 - $4,160 = $6,240 / 60 = $104
        wa_after = services.wa_unit_cost(
            company=self.company,
            material=self.material,
            as_of_date=date(2026, 8, 4),
        )
        self.assertEqual(wa_after, Decimal("104"))

    def test_zero_cost_when_no_layers(self):
        wa = services.wa_unit_cost(company=self.company, material=self.material)
        self.assertEqual(wa, Decimal("0"))

    def test_zero_cost_when_all_consumed(self):
        self._receipt(100, 50, "2026-08-01")
        self._issue(100, "2026-08-02")
        wa = services.wa_unit_cost(
            company=self.company,
            material=self.material,
            as_of_date=date(2026, 8, 2),
        )
        self.assertEqual(wa, Decimal("0"))


class CostLayerApiTests(CostingTestBase):
    def setUp(self):
        super().setUp()
        self.user_viewer = make_user(email="costview@slz.test")
        grant(self.user_viewer, "costing.layer.view")
        self.viewer_client = auth_client(self.user_viewer)

    def test_cost_layers_list_requires_permission(self):
        client = auth_client(make_user(email="nocost@slz.test"))
        resp = client.get("/api/v1/costing/cost-layers/")
        self.assertEqual(resp.status_code, 403)

    def test_cost_layers_list_returns_layers(self):
        self._receipt(100, 50)
        resp = self.viewer_client.get("/api/v1/costing/cost-layers/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)

    def test_wa_cost_endpoint(self):
        self._receipt(200, 75, "2026-08-01")
        resp = self.viewer_client.get(
            f"/api/v1/costing/cost-layers/wa-cost/?material={self.material.id}"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["wa_unit_cost"], "75")

    def test_cost_summary_endpoint(self):
        self._receipt(500, 40, "2026-08-01")
        resp = self.viewer_client.get("/api/v1/costing/cost-layers/summary/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["wa_unit_cost"], "40")
        self.assertEqual(resp.data[0]["on_hand_qty"], "500")
        self.assertEqual(resp.data[0]["on_hand_cost"], "20000")

    def test_wa_cost_404_for_unknown_material(self):
        resp = self.viewer_client.get(
            "/api/v1/costing/cost-layers/wa-cost/?material=00000000-0000-0000-0000-000000000000"
        )
        self.assertEqual(resp.status_code, 404)

    def test_cost_layers_are_read_only(self):
        self._receipt(100, 50)
        resp = self.viewer_client.post(
            "/api/v1/costing/cost-layers/",
            {"company": str(self.company.id), "material": str(self.material.id)},
            format="json",
        )
        self.assertIn(resp.status_code, (400, 403, 405))


class CostingIntegrationTests(CostingTestBase):
    def test_receipt_integration_posts_cost_layer(self):
        layer = integration.post_cost_on_receipt(
            company=self.company,
            material=self.material,
            date="2026-08-01",
            quantity="200",
            unit_price=Decimal("45"),
            reference_type="procurement.GoodsReceiptLine",
            actor=self.user,
        )
        self.assertEqual(layer.layer_type, CostLayerType.RECEIPT)
        self.assertEqual(layer.quantity, Decimal("200"))
        self.assertEqual(layer.unit_cost, Decimal("45"))
        self.assertEqual(layer.total_cost, Decimal("9000"))

    def test_receipt_without_price_uses_zero_cost(self):
        layer = integration.post_cost_on_receipt(
            company=self.company,
            material=self.material,
            date="2026-08-01",
            quantity="100",
            reference_type="procurement.GoodsReceiptLine",
            actor=self.user,
        )
        self.assertEqual(layer.unit_cost, Decimal("0"))
        self.assertEqual(layer.total_cost, Decimal("0"))

    def test_issue_integration_uses_current_wa(self):
        # First, seed a receipt so WA is known
        self._receipt(100, 50, "2026-08-01")
        # Then issue at WA
        layer = integration.post_cost_on_issue(
            company=self.company,
            material=self.material,
            date="2026-08-02",
            quantity="40",
            reference_type="production.MaterialIssue",
            actor=self.user,
        )
        self.assertEqual(layer.layer_type, CostLayerType.ISSUE)
        self.assertEqual(layer.quantity, Decimal("40"))
        self.assertEqual(layer.unit_cost, Decimal("50"))

    def test_issue_with_no_receipt_uses_zero_cost(self):
        layer = integration.post_cost_on_issue(
            company=self.company,
            material=self.material,
            date="2026-08-01",
            quantity="10",
            reference_type="production.MaterialIssue",
            actor=self.user,
        )
        self.assertEqual(layer.unit_cost, Decimal("0"))
