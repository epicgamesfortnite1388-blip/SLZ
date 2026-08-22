"""Manufacturing tests: work centers, machines, BOM & routing versioning, RBAC.

Covers the CONFIRMED versioning mechanics shared by BOM and Routing (draft ->
activate -> supersede, immutability of non-DRAFT revisions), data-driven machine
capability, child-row editability guard, and permission gating. No OPEN business
rule (consumption bases, scrap defaults, routing templates, BOM levels) is
tested because none is implemented.
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
from apps.core.versioning import RevisionStatus
from apps.engineering.models import CustomerProduct, SpecificationRevision
from apps.manufacturing.models import (
    BillOfMaterials,
    BomRevision,
    Routing,
    RoutingRevision,
    WorkCenter,
)
from apps.partners.models import Partner


def build_prereqs(company):
    """Minimal catalog + engineering spec-revision prerequisites."""
    uom = UnitOfMeasure.objects.create(code="KG", name_fa="کیلوگرم", dimension=UomDimension.MASS)
    customer = Partner.objects.create(
        company=company, code="C-001", name_fa="مشتری", is_customer=True
    )
    group = ProductGroup.objects.create(code="FOOD", name_fa="بسته‌بندی غذایی")
    ptype = ProductType.objects.create(code="FILM", name_fa="فیلم")
    pclass = ProductClass.objects.create(product_type=ptype, code="LAM", name_fa="لمینت")
    family = ProductFamily.objects.create(product_class=pclass, code="POUCH", name_fa="پوچ")
    resin = Material.objects.create(
        company=company,
        code="RES-01",
        name_fa="گرانول",
        subtype=MaterialSubtype.RESIN_MASTERBATCH,
        base_uom=uom,
    )
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
    return {"uom": uom, "resin": resin, "spec": spec, "company": company}


class WorkCenterMachineApiTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.user = make_user()
        grant(
            self.user,
            "manufacturing.workcenter.view",
            "manufacturing.workcenter.manage",
            "manufacturing.machine.view",
            "manufacturing.machine.manage",
        )
        self.client = auth_client(self.user)

    def test_create_work_center_persists_and_audits(self):
        resp = self.client.post(
            "/api/v1/manufacturing/work-centers/",
            {"company": str(self.company.id), "code": "EXT", "name_fa": "اکستروژن"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        wc = WorkCenter.objects.get(code="EXT")
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="manufacturing.WorkCenter",
                entity_id=str(wc.id),
            ).exists()
        )

    def test_duplicate_work_center_code_per_company_rejected(self):
        payload = {
            "company": str(self.company.id),
            "code": "EXT",
            "name_fa": "اکستروژن",
        }
        self.client.post("/api/v1/manufacturing/work-centers/", payload, format="json")
        dup = self.client.post("/api/v1/manufacturing/work-centers/", payload, format="json")
        self.assertEqual(dup.status_code, 400, dup.content)

    def test_machine_capability_profile_is_free_form_json(self):
        wc = WorkCenter.objects.create(company=self.company, code="PRN", name_fa="چاپ")
        resp = self.client.post(
            "/api/v1/manufacturing/machines/",
            {
                "company": str(self.company.id),
                "work_center": str(wc.id),
                "code": "M-01",
                "name_fa": "ماشین چاپ",
                "capability_profile": {
                    "web_width_mm": 1200,
                    "color_stations": 8,
                    "max_speed_m_min": 350,
                },
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["capability_profile"]["color_stations"], 8)


class BomLifecycleTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)
        self.user = make_user()
        grant(self.user, "manufacturing.bom.view", "manufacturing.bom.manage")
        self.client = auth_client(self.user)
        self.bom = BillOfMaterials.objects.create(spec_revision=self.p["spec"])

    def _create_draft(self):
        return self.client.post(
            "/api/v1/manufacturing/bom-revisions/",
            {"root": str(self.bom.id)},
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
        a1 = self.client.post(f"/api/v1/manufacturing/bom-revisions/{id1}/activate/")
        self.assertEqual(a1.status_code, 200, a1.content)
        a2 = self.client.post(f"/api/v1/manufacturing/bom-revisions/{id2}/activate/")
        self.assertEqual(a2.status_code, 200, a2.content)
        self.assertEqual(BomRevision.objects.get(id=id1).status, "SUPERSEDED")
        self.assertEqual(BomRevision.objects.get(id=id2).status, "ACTIVE")
        self.assertTrue(
            AuditLog.objects.filter(
                action="UPDATE",
                entity_type="manufacturing.BomRevision",
                entity_id=id2,
            ).exists()
        )

    def test_cannot_activate_non_draft(self):
        rid = self._create_draft().data["id"]
        self.client.post(f"/api/v1/manufacturing/bom-revisions/{rid}/activate/")
        again = self.client.post(f"/api/v1/manufacturing/bom-revisions/{rid}/activate/")
        self.assertEqual(again.status_code, 409, again.content)

    def test_bom_line_editable_only_while_draft(self):
        rid = self._create_draft().data["id"]
        line = {
            "revision": rid,
            "sequence": 1,
            "material": str(self.p["resin"].id),
            "quantity_per_output": "1.500000",
            "uom": str(self.p["uom"].id),
        }
        ok = self.client.post("/api/v1/manufacturing/bom-lines/", line, format="json")
        self.assertEqual(ok.status_code, 201, ok.content)
        self.client.post(f"/api/v1/manufacturing/bom-revisions/{rid}/activate/")
        blocked = self.client.post(
            "/api/v1/manufacturing/bom-lines/",
            {**line, "sequence": 2},
            format="json",
        )
        self.assertEqual(blocked.status_code, 409, blocked.content)

    def test_delete_bom_line_only_while_draft(self):
        rid = self._create_draft().data["id"]
        line = {
            "revision": rid,
            "sequence": 1,
            "material": str(self.p["resin"].id),
            "quantity_per_output": "1.000000",
            "uom": str(self.p["uom"].id),
        }
        created = self.client.post("/api/v1/manufacturing/bom-lines/", line, format="json")
        self.assertEqual(created.status_code, 201, created.content)
        line_id = created.data["id"]
        # DRAFT: delete allowed.
        second = self.client.post(
            "/api/v1/manufacturing/bom-lines/", {**line, "sequence": 2}, format="json"
        )
        self.assertEqual(second.status_code, 201, second.content)
        ok = self.client.delete(f"/api/v1/manufacturing/bom-lines/{line_id}/")
        self.assertEqual(ok.status_code, 204, ok.content)
        # ACTIVE: delete of remaining line blocked.
        remaining_id = second.data["id"]
        self.client.post(f"/api/v1/manufacturing/bom-revisions/{rid}/activate/")
        blocked = self.client.delete(f"/api/v1/manufacturing/bom-lines/{remaining_id}/")
        self.assertEqual(blocked.status_code, 409, blocked.content)

    def test_bom_line_scrap_pct_optional(self):
        rid = self._create_draft().data["id"]
        resp = self.client.post(
            "/api/v1/manufacturing/bom-lines/",
            {
                "revision": rid,
                "sequence": 1,
                "material": str(self.p["resin"].id),
                "quantity_per_output": "2.000000",
                "uom": str(self.p["uom"].id),
                "consumption_basis": "per_weight",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertIsNone(resp.data["scrap_pct"])


class RoutingLifecycleTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.p = build_prereqs(self.company)
        self.user = make_user()
        grant(self.user, "manufacturing.routing.view", "manufacturing.routing.manage")
        self.client = auth_client(self.user)
        self.routing = Routing.objects.create(spec_revision=self.p["spec"])
        self.wc = WorkCenter.objects.create(company=self.company, code="EXT", name_fa="اکستروژن")

    def _create_draft(self):
        return self.client.post(
            "/api/v1/manufacturing/routing-revisions/",
            {"root": str(self.routing.id)},
            format="json",
        )

    def test_activate_supersedes_prior_active(self):
        id1 = self._create_draft().data["id"]
        id2 = self._create_draft().data["id"]
        self.client.post(f"/api/v1/manufacturing/routing-revisions/{id1}/activate/")
        self.client.post(f"/api/v1/manufacturing/routing-revisions/{id2}/activate/")
        self.assertEqual(RoutingRevision.objects.get(id=id1).status, "SUPERSEDED")
        self.assertEqual(RoutingRevision.objects.get(id=id2).status, "ACTIVE")

    def test_operation_editable_only_while_draft(self):
        rid = self._create_draft().data["id"]
        op = {
            "revision": rid,
            "sequence": 1,
            "work_center": str(self.wc.id),
            "operation_name": "Extrude",
            "run_rate": "250.0000",
            "run_rate_basis": "kg/h",
        }
        ok = self.client.post("/api/v1/manufacturing/routing-operations/", op, format="json")
        self.assertEqual(ok.status_code, 201, ok.content)
        self.client.post(f"/api/v1/manufacturing/routing-revisions/{rid}/activate/")
        blocked = self.client.post(
            "/api/v1/manufacturing/routing-operations/",
            {**op, "sequence": 2},
            format="json",
        )
        self.assertEqual(blocked.status_code, 409, blocked.content)

    def test_delete_operation_only_while_draft(self):
        rid = self._create_draft().data["id"]
        op = {
            "revision": rid,
            "sequence": 1,
            "work_center": str(self.wc.id),
            "operation_name": "Extrude",
            "run_rate": "250.0000",
            "run_rate_basis": "kg/h",
        }
        first = self.client.post("/api/v1/manufacturing/routing-operations/", op, format="json")
        self.assertEqual(first.status_code, 201, first.content)
        second = self.client.post(
            "/api/v1/manufacturing/routing-operations/",
            {**op, "sequence": 2},
            format="json",
        )
        self.assertEqual(second.status_code, 201, second.content)
        # DRAFT: delete allowed.
        ok = self.client.delete(f"/api/v1/manufacturing/routing-operations/{first.data['id']}/")
        self.assertEqual(ok.status_code, 204, ok.content)
        # ACTIVE: delete of remaining operation blocked.
        self.client.post(f"/api/v1/manufacturing/routing-revisions/{rid}/activate/")
        blocked = self.client.delete(
            f"/api/v1/manufacturing/routing-operations/{second.data['id']}/"
        )
        self.assertEqual(blocked.status_code, 409, blocked.content)

    def test_one_routing_per_spec_revision(self):
        dup = Routing(spec_revision=self.p["spec"])
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            dup.save()


class ManufacturingPermissionTests(TestCase):
    def setUp(self):
        self.company = make_company()

    def test_view_only_cannot_create_work_center(self):
        user = make_user(email="viewer@slz.test")
        grant(user, "manufacturing.workcenter.view")
        client = auth_client(user)
        resp = client.post(
            "/api/v1/manufacturing/work-centers/",
            {"company": str(self.company.id), "code": "X", "name_fa": "x"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_unpermitted_user_cannot_list_boms(self):
        client = auth_client(make_user(email="nobody@slz.test"))
        resp = client.get("/api/v1/manufacturing/boms/")
        self.assertEqual(resp.status_code, 403, resp.content)
