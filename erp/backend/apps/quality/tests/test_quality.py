"""Quality tests: characteristics catalogue, quality-plan versioning, RBAC.

Covers the CONFIRMED definition layer only — the data-driven characteristic
catalogue and the versioned Quality Plan lifecycle (draft -> activate ->
supersede, immutability of non-DRAFT revisions, one plan per spec revision,
child-item editability guard) plus permission gating. No OPEN business rule
(sampling, tolerances, inspection points, methods) is enforced — those stay
free-text/nullable data — and NO check-execution / NCR / scrap layer exists to
test, by design (gated on Q-046, #11/#12/#18/#31).
"""

from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.catalog.models import (
    Material,
    ProductClass,
    ProductFamily,
    ProductGroup,
    ProductType,
    UnitOfMeasure,
    UomDimension,
)
from apps.core.tests.factories import auth_client, grant, make_company, make_user
from apps.core.versioning import RevisionStatus
from apps.engineering.models import CustomerProduct, SpecificationRevision
from apps.inventory.models import TraceabilityUnit, TraceabilityUnitType
from apps.manufacturing.models import WorkCenter
from apps.partners.models import Partner
from apps.quality import services as quality_services
from apps.quality.models import (
    QualityCharacteristic,
    QualityCheckResult,
    QualityPlan,
    QualityPlanItem,
    QualityPlanRevision,
)


def build_prereqs(company):
    """Minimal catalog + engineering spec-revision prerequisites."""
    uom = UnitOfMeasure.objects.create(code="MIC", name_fa="میکرون", dimension=UomDimension.LENGTH)
    customer = Partner.objects.create(
        company=company, code="C-001", name_fa="مشتری", is_customer=True
    )
    group = ProductGroup.objects.create(code="FOOD", name_fa="بسته‌بندی غذایی")
    ptype = ProductType.objects.create(code="FILM", name_fa="فیلم")
    pclass = ProductClass.objects.create(product_type=ptype, code="LAM", name_fa="لمینت")
    family = ProductFamily.objects.create(product_class=pclass, code="POUCH", name_fa="پوچ")
    cp = CustomerProduct.objects.create(
        company=company,
        customer=customer,
        code="CP-1",
        name_fa="محصول",
        product_group=group,
        family=family,
        base_uom=uom,
    )
    spec = SpecificationRevision.objects.create(
        root=cp,
        revision_number=1,
        status=RevisionStatus.ACTIVE,
        spec_format="ROLL_STOCK",
    )
    return {"uom": uom, "spec": spec, "company": company}


class QualityCharacteristicApiTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.user = make_user()
        grant(
            self.user,
            "quality.characteristic.view",
            "quality.characteristic.manage",
        )
        self.client = auth_client(self.user)

    def test_create_characteristic_persists_and_audits(self):
        resp = self.client.post(
            "/api/v1/quality/characteristics/",
            {
                "company": str(self.company.id),
                "code": "THK",
                "name_fa": "ضخامت",
                "datatype": "NUMBER",
                "method": "ASTM D6988",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        ch = QualityCharacteristic.objects.get(code="THK")
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="quality.QualityCharacteristic",
                entity_id=str(ch.id),
            ).exists()
        )

    def test_duplicate_characteristic_code_per_company_rejected(self):
        payload = {
            "company": str(self.company.id),
            "code": "THK",
            "name_fa": "ضخامت",
        }
        self.client.post("/api/v1/quality/characteristics/", payload, format="json")
        dup = self.client.post("/api/v1/quality/characteristics/", payload, format="json")
        self.assertEqual(dup.status_code, 400, dup.content)

    def test_method_and_datatype_are_free_data(self):
        resp = self.client.post(
            "/api/v1/quality/characteristics/",
            {
                "company": str(self.company.id),
                "code": "DE",
                "name_fa": "اختلاف رنگ",
                "datatype": "NUMBER",
                "method": "spectro ΔE2000",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["method"], "spectro ΔE2000")


class QualityPlanLifecycleTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)
        self.user = make_user()
        grant(
            self.user,
            "quality.plan.view",
            "quality.plan.manage",
            "quality.characteristic.view",
            "quality.characteristic.manage",
        )
        self.client = auth_client(self.user)
        self.plan = QualityPlan.objects.create(spec_revision=self.p["spec"])
        self.characteristic = QualityCharacteristic.objects.create(
            company=self.company,
            code="THK",
            name_fa="ضخامت",
        )
        self.wc = WorkCenter.objects.create(company=self.company, code="EXT", name_fa="اکستروژن")

    def _create_draft(self):
        return self.client.post(
            "/api/v1/quality/plan-revisions/",
            {"root": str(self.plan.id)},
            format="json",
        )

    def test_draft_gets_monotonic_revision_number(self):
        r1 = self._create_draft()
        r2 = self._create_draft()
        self.assertEqual(r1.status_code, 201, r1.content)
        self.assertEqual(r1.data["revision_number"], 1)
        self.assertEqual(r1.data["status"], "DRAFT")
        self.assertEqual(r2.data["revision_number"], 2)

    def test_activate_supersedes_prior_active_and_audits(self):
        id1 = self._create_draft().data["id"]
        id2 = self._create_draft().data["id"]
        a1 = self.client.post(f"/api/v1/quality/plan-revisions/{id1}/activate/")
        self.assertEqual(a1.status_code, 200, a1.content)
        a2 = self.client.post(f"/api/v1/quality/plan-revisions/{id2}/activate/")
        self.assertEqual(a2.status_code, 200, a2.content)
        self.assertEqual(QualityPlanRevision.objects.get(id=id1).status, "SUPERSEDED")
        self.assertEqual(QualityPlanRevision.objects.get(id=id2).status, "ACTIVE")
        self.assertTrue(
            AuditLog.objects.filter(
                action="UPDATE",
                entity_type="quality.QualityPlanRevision",
                entity_id=id2,
            ).exists()
        )

    def test_cannot_activate_non_draft(self):
        rid = self._create_draft().data["id"]
        self.client.post(f"/api/v1/quality/plan-revisions/{rid}/activate/")
        again = self.client.post(f"/api/v1/quality/plan-revisions/{rid}/activate/")
        self.assertEqual(again.status_code, 409, again.content)

    def test_plan_item_editable_only_while_draft(self):
        rid = self._create_draft().data["id"]
        item = {
            "revision": rid,
            "sequence": 1,
            "characteristic": str(self.characteristic.id),
            "work_center": str(self.wc.id),
            "stage_label": "after extrusion",
            "lower_limit": "78.000000",
            "upper_limit": "82.000000",
            "sampling": "100%",
        }
        ok = self.client.post("/api/v1/quality/plan-items/", item, format="json")
        self.assertEqual(ok.status_code, 201, ok.content)
        self.client.post(f"/api/v1/quality/plan-revisions/{rid}/activate/")
        blocked = self.client.post(
            "/api/v1/quality/plan-items/",
            {**item, "sequence": 2},
            format="json",
        )
        self.assertEqual(blocked.status_code, 409, blocked.content)

    def test_plan_item_limits_and_sampling_optional(self):
        rid = self._create_draft().data["id"]
        resp = self.client.post(
            "/api/v1/quality/plan-items/",
            {
                "revision": rid,
                "sequence": 1,
                "characteristic": str(self.characteristic.id),
                "stage_label": "incoming",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertIsNone(resp.data["lower_limit"])
        self.assertIsNone(resp.data["upper_limit"])
        self.assertEqual(resp.data["sampling"], "")

    def test_one_plan_per_spec_revision(self):
        dup = QualityPlan(spec_revision=self.p["spec"])
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            dup.save()

    def test_plan_item_characteristic_must_match_plan_company(self):
        # A characteristic from another company must not leak onto this plan.
        other_company = make_company(code="OTHERCO")
        other_char = QualityCharacteristic.objects.create(
            company=other_company,
            code="THK-X",
            name_fa="ضخامت دیگر",
        )
        rid = self._create_draft().data["id"]
        resp = self.client.post(
            "/api/v1/quality/plan-items/",
            {
                "revision": rid,
                "sequence": 1,
                "characteristic": str(other_char.id),
                "stage_label": "incoming",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("characteristic", resp.data["error"]["details"])

    def test_plan_item_work_center_must_match_plan_company(self):
        other_company = make_company(code="OTHERCO")
        other_wc = WorkCenter.objects.create(
            company=other_company,
            code="EXT-X",
            name_fa="اکستروژن دیگر",
        )
        rid = self._create_draft().data["id"]
        resp = self.client.post(
            "/api/v1/quality/plan-items/",
            {
                "revision": rid,
                "sequence": 1,
                "characteristic": str(self.characteristic.id),
                "work_center": str(other_wc.id),
                "stage_label": "after extrusion",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertIn("work_center", resp.data["error"]["details"])


class QualityPermissionTests(TestCase):
    def setUp(self):
        self.company = make_company()

    def test_view_only_cannot_create_characteristic(self):
        user = make_user(email="viewer@slz.test")
        grant(user, "quality.characteristic.view")
        client = auth_client(user)
        resp = client.post(
            "/api/v1/quality/characteristics/",
            {"company": str(self.company.id), "code": "X", "name_fa": "x"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_unpermitted_user_cannot_list_plans(self):
        client = auth_client(make_user(email="nobody@slz.test"))
        resp = client.get("/api/v1/quality/plans/")
        self.assertEqual(resp.status_code, 403, resp.content)


class QualityCheckPostingTests(TestCase):
    """Regression tests for the QC posting service (append-only results)."""

    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)
        self.user = make_user()
        self.plan = QualityPlan.objects.create(spec_revision=self.p["spec"])
        revision = QualityPlanRevision.objects.create(root=self.plan, revision_number=1)
        self.characteristic = QualityCharacteristic.objects.create(
            company=self.company, code="THK", name_fa="ضخامت"
        )
        self.plan_item = QualityPlanItem.objects.create(
            revision=revision, sequence=1, characteristic=self.characteristic
        )
        material = Material.objects.create(
            company=self.company, code="MAT", name_fa="ماده", base_uom=self.p["uom"]
        )
        self.unit = TraceabilityUnit.objects.create(
            company=self.company,
            material=material,
            unit_type=TraceabilityUnitType.ROLL,
            identifier="ROLL-1",
            quantity=Decimal("10"),
            uom=self.p["uom"],
        )

    def _post(self, **overrides):
        from django.utils import timezone

        kwargs = {
            "plan_item": self.plan_item,
            "traceability_unit": self.unit,
            "measured_value": "80",
            "disposition": "PASS",
            "checked_at": timezone.now(),
            "actor": self.user,
        }
        kwargs.update(overrides)
        return quality_services.post_check_result(**kwargs)

    def test_invalid_disposition_rejected_atomically(self):
        from apps.core.exceptions import BusinessRuleError

        with self.assertRaises(BusinessRuleError) as ctx:
            self._post(disposition="MAYBE")
        self.assertEqual(ctx.exception.code, "qc.invalid_disposition")
        self.assertFalse(QualityCheckResult.objects.exists())

    def test_cross_company_unit_rejected(self):
        from apps.core.exceptions import BusinessRuleError

        other = make_company(code="OTHERQC")
        other_material = Material.objects.create(
            company=other, code="MAT-X", name_fa="ماده دیگر", base_uom=self.p["uom"]
        )
        other_unit = TraceabilityUnit.objects.create(
            company=other,
            material=other_material,
            unit_type=TraceabilityUnitType.ROLL,
            identifier="ROLL-X",
            quantity=Decimal("1"),
            uom=self.p["uom"],
        )
        with self.assertRaises(BusinessRuleError) as ctx:
            self._post(traceability_unit=other_unit)
        self.assertEqual(ctx.exception.code, "qc.cross_company")
        self.assertFalse(QualityCheckResult.objects.exists())

    def test_hold_note_write_failure_rolls_back_result(self):
        """The result row and the HOLD note commit atomically: if tagging the
        unit fails, no orphaned QC result may remain."""
        from unittest import mock

        from apps.inventory.models import TraceabilityUnit as TU

        with (
            mock.patch.object(TU, "save", side_effect=RuntimeError("disk full")),
            self.assertRaises(RuntimeError),
        ):
            self._post(disposition="HOLD")
        self.assertFalse(QualityCheckResult.objects.exists(), "result must roll back")
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.notes, "")

    def test_pass_persists_without_touching_unit(self):
        result = self._post(disposition="PASS")
        result.refresh_from_db()
        self.assertEqual(result.disposition, "PASS")
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.notes, "")
