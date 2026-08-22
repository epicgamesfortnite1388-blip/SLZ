"""Manufacturing — BOM & Routing (Task 006).

This app owns the *engineering definition* of how a product is made: the
resources it runs on (work centers, machines) and the two versioned structures
bound to a product specification revision — the **Bill of Materials** (what is
consumed) and the **Routing** (the ordered operations that produce output).

Scope discipline (see docs/business-analysis/bom-and-routing.md, skill 03,
docs/requirements/do-not-build-yet.md):

* BOM and Routing are **versioned** via the platform ``VersionedRoot`` /
  ``Revision`` pattern and are each **bound to a** ``SpecificationRevision`` — so
  a produced configuration is always reconstructable from the revision in effect
  (versioning.md). The MECHANICAL lifecycle (draft -> activate -> supersede)
  lives in ``services``; it is shared with Product Engineering.
* Machine behaviour is **data-driven**: a ``Machine`` carries a
  ``capability_profile`` JSON (web width, thickness, speeds, color stations, …).
  There is NO hard-coded machine logic (constraint #9 / skill 03).

Deliberately NOT built (OPEN gates — do-not-build-yet):
* BOM consumption bases, waste factors, standard scrap % (Q-027, #9) — quantities
  are captured, ``consumption_basis`` is FREE TEXT (not a locked enum) and
  ``scrap_pct`` is nullable with NO invented default.
* Standard routing templates & stage-skip rules (Q-029, #10) — routings are
  authored, not generated.
* Which intermediates are inventoried / real BOM levels (Q-026, #19) — a BOM's
  ``output_material`` is optional; no level is assumed or derived.
* Alternates/substitutes (A-014, Q-028), changeover matrix, machine-qualification
  pools, required skills, QC-plan links, tooling links, outsourcing execution
  locus (DR-043/NQ-004), and all production EXECUTION (production/work orders,
  consumption, genealogy) — later tasks.
"""

from __future__ import annotations

from django.db import models

from apps.core.models import BaseModel, SoftDeleteModel
from apps.core.versioning import Revision, VersionedRoot


class WorkCenter(BaseModel):
    """A logical production stage (Extrusion, Printing, Lamination, Slitting,
    Converting, Packing) that groups interchangeable machines.

    Company-scoped; ``site`` is optional because production capability is
    site-specific (SR-15) but a work center may be defined before its site is
    pinned. ``sequence_hint`` records the typical stage order for display only —
    it does NOT define any routing (routings are authored per spec revision).
    """

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="work_centers"
    )
    site = models.ForeignKey(
        "organization.Site",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="work_centers",
    )
    code = models.CharField(max_length=60)
    name_fa = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    sequence_hint = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "manufacturing_work_center"
        ordering = ["company", "sequence_hint", "code"]
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="uq_work_center_company_code"),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name_fa}"


class Machine(BaseModel):
    """A physical resource belonging to a work center.

    ``capability_profile`` is free-form JSON (web width, thickness range, speed
    range, color stations, supported materials/structures, setup baselines).
    Planning/validation reads these attributes GENERICALLY — adding a machine is
    adding data, never code (constraint #9).
    """

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="machines"
    )
    site = models.ForeignKey(
        "organization.Site",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="machines",
    )
    work_center = models.ForeignKey(WorkCenter, on_delete=models.PROTECT, related_name="machines")
    code = models.CharField(max_length=60)
    name_fa = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    capability_profile = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "manufacturing_machine"
        ordering = ["company", "code"]
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="uq_machine_company_code"),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name_fa}"


class BillOfMaterials(VersionedRoot):
    """Versioned BOM root, bound to one ``SpecificationRevision``.

    ``output_material`` names which item level this BOM produces (the product is
    multi-level; Q-026 is OPEN, so it is OPTIONAL and no level is derived). A BOM
    is unique per (spec_revision, output_material).
    """

    spec_revision = models.ForeignKey(
        "engineering.SpecificationRevision",
        on_delete=models.PROTECT,
        related_name="boms",
    )
    output_material = models.ForeignKey(
        "catalog.Material",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="bom_outputs",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "manufacturing_bom"
        ordering = ["spec_revision", "output_material"]
        constraints = [
            models.UniqueConstraint(
                fields=["spec_revision", "output_material"],
                name="uq_bom_specrev_output",
            ),
        ]

    def __str__(self) -> str:
        return f"BOM {self.spec_revision_id}/{self.output_material_id}"


class BomRevision(Revision):
    """Immutable versioned BOM. ``revision_number`` monotonic per root; content
    editable only while DRAFT; activation supersedes the prior ACTIVE one."""

    root = models.ForeignKey(BillOfMaterials, on_delete=models.PROTECT, related_name="revisions")

    class Meta:
        db_table = "manufacturing_bom_revision"
        ordering = ["root", "revision_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["root", "revision_number"], name="uq_bom_revision_root_number"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.root_id} v{self.revision_number} [{self.status}]"


class BomLine(SoftDeleteModel):
    """One consumed material with a quantity per unit of output.

    ``consumption_basis`` is FREE TEXT (the canonical basis set is OPEN, Q-027)
    and ``scrap_pct`` is nullable with NO invented default. Editable only while
    the parent revision is DRAFT (enforced in the service/serializer layer).
    """

    revision = models.ForeignKey(BomRevision, on_delete=models.CASCADE, related_name="lines")
    sequence = models.PositiveSmallIntegerField()
    material = models.ForeignKey(
        "catalog.Material", on_delete=models.PROTECT, related_name="bom_lines"
    )
    quantity_per_output = models.DecimalField(max_digits=18, decimal_places=6)
    uom = models.ForeignKey(
        "catalog.UnitOfMeasure", on_delete=models.PROTECT, related_name="bom_lines"
    )
    consumption_basis = models.CharField(max_length=60, blank=True, default="")
    scrap_pct = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "manufacturing_bom_line"
        ordering = ["revision", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["revision", "sequence"], name="uq_bom_line_revision_sequence"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.revision_id} L{self.sequence}:{self.material_id}"


class Routing(VersionedRoot):
    """Versioned routing root, bound to one ``SpecificationRevision`` (one
    routing per spec revision)."""

    spec_revision = models.ForeignKey(
        "engineering.SpecificationRevision",
        on_delete=models.PROTECT,
        related_name="routings",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "manufacturing_routing"
        ordering = ["spec_revision"]
        constraints = [
            models.UniqueConstraint(fields=["spec_revision"], name="uq_routing_specrev"),
        ]

    def __str__(self) -> str:
        return f"Routing {self.spec_revision_id}"


class RoutingRevision(Revision):
    """Immutable versioned routing. ``revision_number`` monotonic per root;
    editable only while DRAFT; activation supersedes the prior ACTIVE one."""

    root = models.ForeignKey(Routing, on_delete=models.PROTECT, related_name="revisions")

    class Meta:
        db_table = "manufacturing_routing_revision"
        ordering = ["root", "revision_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["root", "revision_number"],
                name="uq_routing_revision_root_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.root_id} v{self.revision_number} [{self.status}]"


class RoutingOperation(SoftDeleteModel):
    """One ordered step performed at a work center.

    Binds "what is produced" (``output_material``, optional per Q-026) to "where"
    (``work_center``). Run rate / setup are captured as data; the run-rate basis
    is FREE TEXT (m/min, kg/h, pcs/h — canonical set not locked). Machine
    selection, changeover, skills, QC and tooling links belong to later tasks.
    Editable only while the parent revision is DRAFT.
    """

    revision = models.ForeignKey(
        RoutingRevision, on_delete=models.CASCADE, related_name="operations"
    )
    sequence = models.PositiveSmallIntegerField()
    work_center = models.ForeignKey(WorkCenter, on_delete=models.PROTECT, related_name="operations")
    operation_name = models.CharField(max_length=120)
    output_material = models.ForeignKey(
        "catalog.Material",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="routing_operations",
    )
    setup_time_minutes = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    run_rate = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    run_rate_basis = models.CharField(max_length=30, blank=True, default="")
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "manufacturing_routing_operation"
        ordering = ["revision", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["revision", "sequence"],
                name="uq_routing_operation_revision_sequence",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.revision_id} Op{self.sequence}:{self.operation_name}"
