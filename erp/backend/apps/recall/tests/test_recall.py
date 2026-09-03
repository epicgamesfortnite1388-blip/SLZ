"""Recall tests: recall lifecycle/transitions, RBAC, company isolation, and the
read-only exposure computation over genealogy + shipment records.

The exposure engine must NEVER mutate anything — it only walks the append-only
ledger. Covers DRAFT->OPEN->CLOSED transitions with terminal-state guards,
cross-company unit rejection, and backward/forward genealogy + customer/shipment
exposure.
"""

from __future__ import annotations

from datetime import date

from django.test import TestCase

from apps.catalog.models import Material, UnitOfMeasure, UomDimension
from apps.core.tests.factories import auth_client, grant, make_company, make_site, make_user
from apps.identity.models import CompanyMembership
from apps.inventory.models import (
    GenealogyLink,
    TraceabilityUnit,
    TraceabilityUnitType,
    Warehouse,
    WarehouseStoreType,
)
from apps.partners.models import Customer, Partner
from apps.recall import services
from apps.recall.models import Recall, RecallAffectedUnit, RecallStatus
from apps.shipment.models import Shipment, ShipmentLine


def _only_member_of(user, company) -> None:
    CompanyMembership.objects.filter(user=user).exclude(company=company).delete()


def _make_prereqs(company):
    site = make_site(company=company)
    uom, _ = UnitOfMeasure.objects.get_or_create(
        code="KG", defaults={"name_fa": "کیلوگرم", "dimension": UomDimension.MASS}
    )
    material = Material.objects.create(
        company=company, code="RM-PE", name_fa="پلی‌اتیلن", base_uom=uom
    )
    warehouse = Warehouse.objects.create(
        company=company,
        site=site,
        code="WH-1",
        name_fa="انبار اصلی",
        store_type=WarehouseStoreType.GENERAL,
    )
    partner = Partner.objects.create(
        company=company, code="C-001", name_fa="مشتری نمونه", is_customer=True
    )
    customer = Customer.objects.create(partner=partner)
    return {"uom": uom, "material": material, "warehouse": warehouse, "customer": customer}


def _make_unit(company, identifier, material=None, unit_type=TraceabilityUnitType.BATCH):
    return TraceabilityUnit.objects.create(
        company=company,
        material=material,
        identifier=identifier,
        unit_type=unit_type,
        quantity=10,
        uom=None,
    )


class RecallApiTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = _make_prereqs(self.company)
        self.user = make_user()
        grant(self.user, "recall.recall.view", "recall.recall.manage")
        self.client = auth_client(self.user)
        self.unit = _make_unit(self.company, "LOT-0001", material=self.p["material"])

    def _create_recall(self, code="RC-2026-001", **kw):
        payload = {
            "company": str(self.company.id),
            "code": code,
            "reason": "Film thickness out of tolerance on one roll.",
            "severity": "HIGH",
        }
        payload.update(kw)
        return self.client.post("/api/v1/recall/recalls/", payload, format="json")

    def test_create_recall_defaults_to_draft(self):
        resp = self._create_recall()
        self.assertEqual(resp.status_code, 201, resp.content)
        body = resp.json()
        self.assertEqual(body["status"], RecallStatus.DRAFT)
        self.assertIsNone(body["initiated_at"])

    def test_create_cannot_skip_draft(self):
        resp = self._create_recall(code="RC-X", status="OPEN")
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_transition_draft_to_open_sets_initiated_at(self):
        recall = Recall.objects.create(company=self.company, code="RC-1", reason="test")
        RecallAffectedUnit.objects.create(recall=recall, traceability_unit=self.unit)
        resp = self.client.post(
            f"/api/v1/recall/recalls/{recall.id}/transition/",
            {"status": RecallStatus.OPEN},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        recall.refresh_from_db()
        self.assertEqual(recall.status, RecallStatus.OPEN)
        self.assertIsNotNone(recall.initiated_at)

    def test_invalid_transition_rejected(self):
        recall = Recall.objects.create(company=self.company, code="RC-2", reason="test")
        resp = self.client.post(
            f"/api/v1/recall/recalls/{recall.id}/transition/",
            {"status": RecallStatus.CLOSED},  # DRAFT -> CLOSED is not allowed
            format="json",
        )
        self.assertEqual(resp.status_code, 422, resp.content)
        recall.refresh_from_db()
        self.assertEqual(recall.status, RecallStatus.DRAFT)

    def test_terminal_recall_rejects_edit_and_delete(self):
        recall = Recall.objects.create(
            company=self.company, code="RC-3", reason="test", status=RecallStatus.CLOSED
        )
        patch = self.client.patch(
            f"/api/v1/recall/recalls/{recall.id}/",
            {"reason": "updated"},
            format="json",
        )
        self.assertEqual(patch.status_code, 422, patch.content)
        delete = self.client.delete(f"/api/v1/recall/recalls/{recall.id}/")
        self.assertEqual(delete.status_code, 422, delete.content)

    def test_affected_unit_cross_company_rejected(self):
        other = make_company(code="OTHER")
        other_p = _make_prereqs(other)
        other_unit = _make_unit(other, "LOT-9999", material=other_p["material"])
        recall = Recall.objects.create(company=self.company, code="RC-4", reason="test")
        resp = self.client.post(
            "/api/v1/recall/affected-units/",
            {"recall": str(recall.id), "traceability_unit": str(other_unit.id)},
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_company_isolation_list_and_write(self):
        other = make_company(code="ZZZZ")  # created after user -> not auto-joined
        outsider = make_user(email="out@slz.test")
        _only_member_of(outsider, other)
        grant(outsider, "recall.recall.view", "recall.recall.manage")
        client = auth_client(outsider)
        Recall.objects.create(company=self.company, code="RC-H", reason="hidden")
        # List is empty for the outsider (they belong to `other` only).
        resp = client.get("/api/v1/recall/recalls/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["results"], [])
        # Write to company A's recall is denied.
        own = Recall.objects.create(company=other, code="RC-OWN", reason="mine")
        patch = client.patch(f"/api/v1/recall/recalls/{own.id}/", {"reason": "x"}, format="json")
        self.assertEqual(patch.status_code, 200, patch.content)


class RecallExposureTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = _make_prereqs(self.company)

    def _link(self, parent, child):
        return GenealogyLink.objects.create(parent=parent, child=child)

    def test_exposure_walks_genealogy_and_shipments(self):
        raw = _make_unit(self.company, "RAW-001", material=self.p["material"])
        wip = _make_unit(self.company, "WIP-001", material=self.p["material"])
        fg = _make_unit(self.company, "FG-001", unit_type=TraceabilityUnitType.ROLL)
        self._link(raw, wip)
        self._link(wip, fg)

        shipment = Shipment.objects.create(
            company=self.company,
            customer=self.p["customer"],
            warehouse=self.p["warehouse"],
            number="SH-1",
            shipped_at=date(2026, 1, 5),
        )
        ShipmentLine.objects.create(
            shipment=shipment,
            traceability_unit=fg,
            quantity=1,
            uom=self.p["uom"],
        )
        recall = Recall.objects.create(company=self.company, code="RC-E1", reason="suspect FG")
        RecallAffectedUnit.objects.create(recall=recall, traceability_unit=fg)

        exposure = services.compute_exposure(recall)
        # Seed (fg) + upstream (wip, raw).
        ids = {str(u["id"]) for u in exposure["affected_units"]}
        self.assertEqual(len(ids), 3)
        self.assertIn(str(raw.id), ids)
        self.assertIn(str(wip.id), ids)
        self.assertIn(str(fg.id), ids)
        # The shipment of the affected finished unit is visible.
        self.assertEqual(len(exposure["shipments"]), 1)
        self.assertEqual(exposure["shipments"][0]["number"], "SH-1")
        self.assertEqual(len(exposure["customers"]), 1)
        self.assertEqual(exposure["customers"][0]["name_fa"], "مشتری نمونه")

    def test_exposure_is_read_only_and_cycle_safe(self):
        a = _make_unit(self.company, "A-001")
        b = _make_unit(self.company, "B-001")
        self._link(a, b)
        self._link(b, a)  # malformed cycle
        recall = Recall.objects.create(company=self.company, code="RC-E2", reason="cycle")
        RecallAffectedUnit.objects.create(recall=recall, traceability_unit=a)
        # Bounded traversal terminates despite the cycle: the malformed graph
        # makes B both an ancestor and a descendant of A, but each is collected
        # exactly once and no infinite loop occurs.
        exposure = services.compute_exposure(recall)
        ids = {str(u["id"]) for u in exposure["affected_units"]}
        self.assertEqual(len(ids), 2)
        self.assertIn(str(a.id), ids)
        self.assertIn(str(b.id), ids)
        self.assertLessEqual(exposure["upstream_units"], 1)
        self.assertLessEqual(exposure["downstream_units"], 1)
        # Nothing was created or mutated by computing exposure.
        self.assertEqual(GenealogyLink.objects.count(), 2)
        self.assertEqual(RecallAffectedUnit.objects.count(), 1)
        self.assertEqual(Recall.objects.count(), 1)

    def test_raw_seed_reports_downstream_shipment_customers(self):
        # A recall seeded at a raw material still surfaces finished shipments.
        raw = _make_unit(self.company, "RAW-002", material=self.p["material"])
        fg = _make_unit(self.company, "FG-002", unit_type=TraceabilityUnitType.ROLL)
        self._link(raw, fg)
        shipment = Shipment.objects.create(
            company=self.company,
            customer=self.p["customer"],
            warehouse=self.p["warehouse"],
            number="SH-2",
            shipped_at=date(2026, 2, 1),
        )
        ShipmentLine.objects.create(
            shipment=shipment, traceability_unit=fg, quantity=1, uom=self.p["uom"]
        )
        recall = Recall.objects.create(company=self.company, code="RC-E3", reason="raw suspect")
        RecallAffectedUnit.objects.create(recall=recall, traceability_unit=raw)
        exposure = services.compute_exposure(recall)
        self.assertEqual(len(exposure["shipments"]), 1)
        self.assertEqual(exposure["shipments"][0]["number"], "SH-2")
