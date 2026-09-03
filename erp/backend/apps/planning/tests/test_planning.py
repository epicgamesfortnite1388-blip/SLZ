"""Planning tests: reorder-policy CRUD/RBAC/isolation + the read-only engine.

The engine must never mutate documents — it aggregates ledger/documents into
suggestion rows. Covers: policy create with cross-company FK rejection, company
isolation on list/write, engine suggestion math (material: purchase below
reorder point, order-up-to qty), and read-only engine guarantees.
"""

from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.catalog.models import Material, UnitOfMeasure, UomDimension
from apps.core.tests.factories import auth_client, grant, make_company, make_site, make_user
from apps.identity.models import CompanyMembership
from apps.inventory import services as inventory_services
from apps.inventory.models import StockMovementDirection, Warehouse, WarehouseStoreType
from apps.planning import services
from apps.planning.models import PlanningPolicy


def _only_member_of(user, company) -> None:
    """Reduce ``user`` to a single-company membership."""
    CompanyMembership.objects.filter(user=user).exclude(company=company).delete()


def _make_material(company, uom, code="RM-PE", name_fa="پلی‌اتیلن"):
    return Material.objects.create(company=company, code=code, name_fa=name_fa, base_uom=uom)


def _make_warehouse(company, site, code="RM-01"):
    return Warehouse.objects.create(
        company=company,
        site=site,
        code=code,
        name_fa="انبار مواد",
        store_type=WarehouseStoreType.RAW_MATERIAL,
    )


class PlanningPolicyApiTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.site = make_site(company=self.company)
        self.user = make_user()
        grant(self.user, "planning.policy.view", "planning.policy.manage")
        self.client = auth_client(self.user)
        self.uom = UnitOfMeasure.objects.create(
            code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS
        )
        self.material = _make_material(self.company, self.uom)
        self.warehouse = _make_warehouse(self.company, self.site)

    def test_create_policy_persists_and_audits(self):
        resp = self.client.post(
            "/api/v1/planning/policies/",
            {
                "company": str(self.company.id),
                "warehouse": str(self.warehouse.id),
                "material": str(self.material.id),
                "reorder_point": "50",
                "target_level": "200",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        body = resp.json()
        self.assertEqual(body["item_type"], "MATERIAL")
        self.assertEqual(Decimal(body["reorder_point"]), Decimal("50"))
        policy = PlanningPolicy.objects.get(pk=body["id"])
        self.assertEqual(policy.company_id, self.company.id)
        # Every write is audited.
        self.assertTrue(
            AuditLog.objects.filter(entity_type="planning.PlanningPolicy", action="CREATE").exists()
        )

    def test_create_rejects_warehouse_from_another_company(self):
        other_company = make_company(code="OTHER")
        other_site = make_site(company=other_company, code="OTH")
        other_wh = _make_warehouse(other_company, other_site, code="WH-9")
        resp = self.client.post(
            "/api/v1/planning/policies/",
            {
                "company": str(self.company.id),
                "warehouse": str(other_wh.id),
                "material": str(self.material.id),
                "reorder_point": "10",
                "target_level": "100",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_requires_exactly_one_item_kind(self):
        resp = self.client.post(
            "/api/v1/planning/policies/",
            {
                "company": str(self.company.id),
                "warehouse": str(self.warehouse.id),
                "reorder_point": "10",
                "target_level": "100",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_company_isolation_denies_write_to_non_member(self):
        # Outsider belongs only to a different company created first, so they
        # never auto-join ``self.company``.
        other_company = make_company(code="ACME")
        outsider = make_user(email="outsider@slz.test")
        _only_member_of(outsider, other_company)
        grant(outsider, "planning.policy.manage")
        client = auth_client(outsider)
        resp = client.post(
            "/api/v1/planning/policies/",
            {
                "company": str(self.company.id),
                "warehouse": str(self.warehouse.id),
                "material": str(self.material.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_rbac_denies_without_permission(self):
        nobody = make_user(email="nobody@slz.test")
        _only_member_of(nobody, self.company)
        client = auth_client(nobody)
        resp = client.get("/api/v1/planning/policies/")
        self.assertEqual(resp.status_code, 403, resp.content)


class PlanningEngineTests(TestCase):
    """The engine reads live ledger/documents and suggests — never mutates."""

    def setUp(self):
        self.company = make_company()
        self.site = make_site(company=self.company)
        self.user = make_user()
        self.uom = UnitOfMeasure.objects.create(
            code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS
        )
        self.material = _make_material(self.company, self.uom)
        self.warehouse = _make_warehouse(self.company, self.site)

    def _policy(self, reorder="50", target="200", is_active=True):
        return PlanningPolicy.objects.create(
            company=self.company,
            warehouse=self.warehouse,
            material=self.material,
            reorder_point=Decimal(reorder),
            target_level=Decimal(target),
            is_active=is_active,
        )

    def _receipt(self, qty):
        inventory_services.post_movement(
            company=self.company,
            warehouse=self.warehouse,
            direction=StockMovementDirection.IN,
            quantity=Decimal(str(qty)),
            uom=self.uom,
            material=self.material,
            reference_type="test.receipt",
            actor=self.user,
        )

    def test_suggests_purchase_when_projected_below_reorder_point(self):
        self._policy()
        self._receipt(20)
        rows = services.run_planning(self.company)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.on_hand, Decimal("20"))
        self.assertEqual(row.action, "PURCHASE")
        # order-up-to replenishment
        self.assertEqual(row.suggested_qty, Decimal("180"))
        self.assertIn("below reorder", row.reason)

    def test_no_suggestion_when_projected_above_reorder_point(self):
        self._policy()
        self._receipt(120)
        rows = services.run_planning(self.company)
        self.assertEqual(rows[0].action, "NONE")

    def test_inactive_policies_are_skipped(self):
        self._policy(is_active=False)
        rows = services.run_planning(self.company)
        self.assertEqual(rows, [])

    def test_engine_suggestions_are_read_only(self):
        self._policy()
        self._receipt(5)
        rows = services.run_planning(self.company)
        self.assertEqual(len(rows), 1)
        # The engine only returns suggestion rows — it never creates or mutates
        # any document (a PlanningRow carries no document state to persist).
        self.assertEqual(rows[0].suggested_qty, Decimal("195"))
        self.assertEqual(PlanningPolicy.objects.count(), 1)

    def test_summary_counts(self):
        self._policy(reorder="50", target="200")
        rows = services.run_planning(self.company)
        summary = services.summary_rows(rows)
        self.assertEqual(summary["total_policies"], 1)
        self.assertEqual(summary["action_required"], 1)
        self.assertEqual(summary["to_purchase"], 1)
        self.assertEqual(summary["to_manufacture"], 0)
