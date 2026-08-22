"""Quality — Inspection / Quality Plan definition (Task 008).

This app owns the *definition* of what quality checks a product requires: a
company-scoped catalogue of measurable **characteristics** and the **versioned
Quality Plan** that lists, per product specification revision, which
characteristics are inspected, where (work center / stage) and against which
limits.

Scope discipline (see docs/business-analysis/quality-model.md, skill 06,
docs/requirements/do-not-build-yet.md #11/#12/#18/#31, docs/architecture/versioning.md):

* A Quality Plan is **versioned** via the platform ``VersionedRoot`` /
  ``Revision`` pattern and is **bound to a** ``SpecificationRevision`` — so the
  set of checks in force is always reconstructable from the revision that was
  active (versioning.md). The MECHANICAL lifecycle (draft -> activate ->
  supersede) lives in ``services`` and mirrors Engineering / Manufacturing.
* Characteristics, methods, stages, sampling and limits are **data**, never
  code: adding a new inspection is adding a row, not a branch. Test methods,
  standards, sampling rules and inspection points are SLZ-specific and OPEN
  (Q-039 / Q-040), so they are FREE TEXT / nullable with NO invented values.

Deliberately NOT built (OPEN gates — do-not-build-yet):
* Quality CHECK execution & results (measured values, PASS/FAIL/CONDITIONAL) —
  these are append-only records tied to a lot / roll / work order / batch, which
  requires the traceability + stock layer that is gated on roll-serialization vs.
  lot+count (Q-046, #18, the highest-priority gate).
* Non-conformance (NCR) / QC_HOLD, disposition, scrap & rework records and reason
  codes (Q-041 / Q-043 / Q-016·042, #12), COA issuance (Q-045), and formal
  recall / CAPA / 8D (Q-044, #31) — all later tasks.
* Any single terminal inspection gate or hard-coded plan/characteristic/tolerance
  /sampling set (skill 06 FORBIDDEN list, #11) — plans are authored per product,
  never generated or assumed.
"""

from __future__ import annotations

from django.db import models

from apps.core.models import BaseModel, SoftDeleteModel
from apps.core.versioning import Revision, VersionedRoot


class CharacteristicDatatype(models.TextChoices):
    """How a characteristic is measured. Kept minimal and generic; the concrete
    method/standard is free-text data (Q-039 OPEN), not encoded here."""

    NUMBER = "NUMBER", "Number"
    TEXT = "TEXT", "Text"
    BOOL = "BOOL", "Boolean"


class QualityCharacteristic(BaseModel):
    """A measurable quality attribute (thickness, ΔE, bond/seal strength, COF,
    a dimension, an attribute pass/fail…).

    Company-scoped data-driven catalogue: what is measured, how (``method`` — a
    FREE-TEXT standard/instrument reference, Q-039 OPEN, never a locked list) and
    with which datatype + optional default unit. Spec *limits* are NOT stored on
    the characteristic — they belong to the plan item (and ultimately the product
    spec revision), because the same characteristic has different limits per
    product.
    """

    company = models.ForeignKey(
        "organization.Company",
        on_delete=models.PROTECT,
        related_name="quality_characteristics",
    )
    code = models.CharField(max_length=60)
    name_fa = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    datatype = models.CharField(
        max_length=8,
        choices=CharacteristicDatatype.choices,
        default=CharacteristicDatatype.NUMBER,
    )
    # Test method / standard / instrument — FREE TEXT (Q-039 OPEN). Not a locked
    # enum; SLZ's actual methods per stage are to be supplied by the business.
    method = models.CharField(max_length=255, blank=True, default="")
    default_uom = models.ForeignKey(
        "catalog.UnitOfMeasure",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="quality_characteristics",
    )
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "quality_characteristic"
        ordering = ["company", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "code"], name="uq_quality_characteristic_company_code"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name_fa}"


class QualityPlan(VersionedRoot):
    """Versioned Quality (Inspection) Plan root, bound to one
    ``SpecificationRevision`` (one plan per spec revision — mirrors Routing).

    The plan is the durable identity; its content lives in immutable revisions.
    A produced/inspected configuration is always reconstructable from the plan
    revision that was ACTIVE when the work happened.
    """

    spec_revision = models.ForeignKey(
        "engineering.SpecificationRevision",
        on_delete=models.PROTECT,
        related_name="quality_plans",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "quality_plan"
        ordering = ["spec_revision"]
        constraints = [
            models.UniqueConstraint(fields=["spec_revision"], name="uq_quality_plan_specrev"),
        ]

    def __str__(self) -> str:
        return f"QualityPlan {self.spec_revision_id}"


class QualityPlanRevision(Revision):
    """Immutable versioned quality plan. ``revision_number`` monotonic per root;
    content editable only while DRAFT; activation supersedes the prior ACTIVE
    revision. Uses the shared generic lifecycle service."""

    root = models.ForeignKey(QualityPlan, on_delete=models.PROTECT, related_name="revisions")

    class Meta:
        db_table = "quality_plan_revision"
        ordering = ["root", "revision_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["root", "revision_number"],
                name="uq_quality_plan_revision_root_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.root_id} v{self.revision_number} [{self.status}]"


class QualityPlanItem(SoftDeleteModel):
    """One characteristic to inspect within a plan revision.

    Binds *what* (``characteristic``) to *where* (optional ``work_center`` and a
    FREE-TEXT ``stage_label`` — inspection points are OPEN, Q-039, so never a
    locked enum) and *against which limits* (``lower_limit`` / ``upper_limit`` /
    ``target``, all nullable — SLZ's tolerances are OPEN, Q-022; no default is
    invented, and limits ultimately trace to the product spec revision).

    ``sampling`` and ``method_override`` are FREE TEXT: the 100%-vs-AQL sampling
    rule (Q-040) and the per-plan method are not locked. ``is_mandatory`` is
    descriptive metadata only — there is NO check-execution layer to enforce it
    yet (that is gated on Q-046). Editable only while the parent revision is
    DRAFT (enforced in the serializer layer)."""

    revision = models.ForeignKey(
        QualityPlanRevision, on_delete=models.CASCADE, related_name="items"
    )
    sequence = models.PositiveSmallIntegerField()
    characteristic = models.ForeignKey(
        QualityCharacteristic, on_delete=models.PROTECT, related_name="plan_items"
    )
    # WHERE the check happens. Optional: incoming/pre-ship checks are not tied to
    # a work center. PROTECT — never erase a referenced stage.
    work_center = models.ForeignKey(
        "manufacturing.WorkCenter",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="quality_plan_items",
    )
    # Inspection point label (incoming, after extrusion, final…). OPEN (Q-039) ->
    # FREE TEXT, NOT a hard-coded list.
    stage_label = models.CharField(max_length=120, blank=True, default="")
    lower_limit = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    upper_limit = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    target = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    unit = models.CharField(max_length=30, blank=True, default="")
    # Sampling rule (100% vs AQL / sample size) is OPEN (Q-040) -> FREE TEXT.
    sampling = models.CharField(max_length=120, blank=True, default="")
    # Per-plan override of the characteristic's method; blank = use characteristic.
    method_override = models.CharField(max_length=255, blank=True, default="")
    is_mandatory = models.BooleanField(default=True)
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "quality_plan_item"
        ordering = ["revision", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["revision", "sequence"],
                name="uq_quality_plan_item_revision_sequence",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.revision_id} I{self.sequence}:{self.characteristic_id}"


class QualityCheckResult(BaseModel):
    """One measured value for a plan item against a traceability unit.

    Roll-level QC (Q-046): every produced roll can be checked.
    Results are append-only — corrections come as new rows.
    The disposition status (PASS/FAIL/HOLD) integrates with inventory.
    """

    class Disposition(models.TextChoices):
        PASS = "PASS", "Pass"
        FAIL = "FAIL", "Fail"
        HOLD = "HOLD", "Hold / Quarantine"

    plan_item = models.ForeignKey(
        QualityPlanItem, on_delete=models.PROTECT, related_name="check_results"
    )
    traceability_unit = models.ForeignKey(
        "inventory.TraceabilityUnit",
        on_delete=models.PROTECT,
        related_name="qc_results",
    )
    measured_value = models.CharField(max_length=120)
    disposition = models.CharField(
        max_length=5, choices=Disposition.choices, default=Disposition.PASS
    )
    checked_at = models.DateTimeField()
    checked_by = models.ForeignKey(
        "hr.Employee",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="qc_results",
    )
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "quality_check_result"
        ordering = ["-checked_at"]

    def __str__(self) -> str:
        return f"QC {self.disposition} on {self.traceability_unit_id}"
