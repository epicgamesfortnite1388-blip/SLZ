"""Production — Work Orders (Task 011).

This app owns the *manufacturing commercial-document* layer: the **Production
Order** (a.k.a. Work Order), the shop-floor commitment to make a given quantity
of a customer product to a **frozen engineering definition** (a specific
``SpecificationRevision`` and, optionally, the ``BomRevision`` / ``RoutingRevision``
in effect). It is the manufacturing counterpart of the Task 009 purchase order
and the Task 010 sales order: a single transactional instance driven by a
**status lifecycle (state machine)** — deliberately NOT the ``VersionedRoot`` /
``Revision`` pattern (that models engineering versions, not shop paper).

Scope discipline (see docs/reconciliation/current-to-future-system.md rows 9/15/
18/19/20/21/22, docs/business-analysis/manufacturing-processes.md, docs/
requirements/do-not-build-yet.md, skill 03):

* A production order carries a MANUAL ``number`` (unique per company). No
  auto-numbering / WO coding scheme is invented (#14 OPEN) — the business
  supplies the number.
* It is **header-only**: it pins WHAT to make (``customer_product``), HOW MUCH
  (``planned_quantity`` + ``uom``), and the FROZEN definition it is built to
  (``spec_revision``; optional ``bom_revision`` / ``routing_revision``). The
  material lines and operations already live on those revisions — duplicating
  them here as editable order lines would either be redundant or would be
  execution tracking (gated on Q-046) and is deliberately NOT done.
* The lifecycle is the generic, minimal shop paper trail:
  ``DRAFT → RELEASED → COMPLETED → CLOSED`` (+ ``CANCELLED``). ``RELEASED`` is the
  authorization to the shop floor; ``COMPLETED`` / ``CLOSED`` are MANUAL
  administrative marks — they are NOT derived from operation confirmations or
  produced-quantity roll-ups (that is execution, gated).
* The header is editable only while DRAFT (a released order is a commitment).

Deliberately NOT built (OPEN gates — do-not-build-yet):
* Material issue / consumption, backflush, and roll/lot **genealogy** (SR-08,
  #19) — bound to the traceability + stock layer gated on Q-046 (#18, highest
  priority; C-003 forbids migrating that schema until roll-serialization-vs-
  lot+count is decided).
* Operation confirmations, produced/scrap quantity capture, downtime, and the
  allowed-scrap/downtime threshold tables (SR-05/SR-06, #9/#12) — no execution
  record exists here; ``COMPLETED`` is a manual flag only.
* Inline / final QC **results** and auto stop + rework spawning (SR-06, row 20) —
  the Task 008 quality layer defines plans; results need Q-046.
* Margin-based prioritization (SR-13) and outsourcing execution locus
  (SR-14 / DR-043 / NQ-004) — no priority or make-vs-buy rule is invented.
* ATP / promised-date and capacity feasibility (SR-12 / R-30, #12) — scheduled
  dates are captured as plain fields; nothing is computed or promised.
"""

from __future__ import annotations

from django.db import models

from apps.core.models import BaseModel, SoftDeleteModel


class MaterialIssueMethod(models.TextChoices):
    EXPLICIT = "EXPLICIT", "Explicit lot/roll issue"
    BACKFLUSH = "BACKFLUSH", "Backflush"


class ProductionOrderStatus(models.TextChoices):
    """Production-order lifecycle. Editable only in DRAFT; terminal in
    CLOSED / CANCELLED.

    ``RELEASED`` authorizes the shop floor (the manufacturing commitment).
    ``COMPLETED`` and ``CLOSED`` are MANUAL administrative marks — execution
    states (issued / in-operation / confirmed) are intentionally absent because
    they belong to the gated traceability + stock layer (Q-046)."""

    DRAFT = "DRAFT", "Draft"
    RELEASED = "RELEASED", "Released"
    COMPLETED = "COMPLETED", "Completed"
    CLOSED = "CLOSED", "Closed"
    CANCELLED = "CANCELLED", "Cancelled"


class MaterialIssue(BaseModel):
    """Immutable material consumption record for a released production order.

    EXPLICIT rows name the consumed roll/batch; BACKFLUSH rows may omit the unit
    and identify the source material. The selected method is recorded on every
    row so the audit trail does not depend on a later routing interpretation.
    """

    production_order = models.ForeignKey(
        "production.ProductionOrder", on_delete=models.PROTECT, related_name="material_issues"
    )
    routing_operation_id = models.UUIDField(null=True, blank=True)
    material = models.ForeignKey(
        "catalog.Material", on_delete=models.PROTECT, related_name="material_issues"
    )
    traceability_unit = models.ForeignKey(
        "inventory.TraceabilityUnit",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="material_issues",
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse", on_delete=models.PROTECT, related_name="material_issues"
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    uom = models.ForeignKey(
        "catalog.UnitOfMeasure", on_delete=models.PROTECT, related_name="material_issues"
    )
    method = models.CharField(max_length=10, choices=MaterialIssueMethod.choices)
    operation_label = models.CharField(max_length=120, blank=True, default="")
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "production_material_issue"
        ordering = ["created_at", "id"]


class ProductionOutput(BaseModel):
    """Immutable produced handling-unit record for a production order."""

    production_order = models.ForeignKey(
        "production.ProductionOrder", on_delete=models.PROTECT, related_name="outputs"
    )
    traceability_unit = models.ForeignKey(
        "inventory.TraceabilityUnit", on_delete=models.PROTECT, related_name="production_outputs"
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse", on_delete=models.PROTECT, related_name="production_outputs"
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    uom = models.ForeignKey(
        "catalog.UnitOfMeasure", on_delete=models.PROTECT, related_name="production_outputs"
    )
    operation_label = models.CharField(max_length=120, blank=True, default="")
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "production_output"
        ordering = ["created_at", "id"]


class ProductionOrder(SoftDeleteModel):
    """A shop-floor order to make one customer product to a frozen engineering
    definition. Company-scoped (DR-040); ``site`` optional (SR-15 site
    capability is respected by planning, not encoded here).

    ``number`` is a MANUAL business number, unique per company. The order is
    built to ``spec_revision`` (a specific, frozen ``SpecificationRevision``);
    ``bom_revision`` / ``routing_revision`` optionally pin the exact structures
    in effect (they may not be chosen at draft time — Q-026 keeps BOM level
    OPEN). ``sales_order_line`` records demand provenance for this made-to-order
    business; it is SET_NULL so the order survives if the source line is later
    removed (a production order may also be make-to-stock)."""

    company = models.ForeignKey(
        "organization.Company",
        on_delete=models.PROTECT,
        related_name="production_orders",
    )
    site = models.ForeignKey(
        "organization.Site",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="production_orders",
    )
    number = models.CharField(max_length=40)
    customer_product = models.ForeignKey(
        "engineering.CustomerProduct",
        on_delete=models.PROTECT,
        related_name="production_orders",
    )
    spec_revision = models.ForeignKey(
        "engineering.SpecificationRevision",
        on_delete=models.PROTECT,
        related_name="production_orders",
    )
    bom_revision = models.ForeignKey(
        "manufacturing.BomRevision",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="production_orders",
    )
    routing_revision = models.ForeignKey(
        "manufacturing.RoutingRevision",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="production_orders",
    )
    sales_order_line = models.ForeignKey(
        "sales.SalesOrderLine",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="production_orders",
    )
    status = models.CharField(
        max_length=16,
        choices=ProductionOrderStatus.choices,
        default=ProductionOrderStatus.DRAFT,
        db_index=True,
    )
    planned_quantity = models.DecimalField(max_digits=18, decimal_places=6)
    uom = models.ForeignKey(
        "catalog.UnitOfMeasure",
        on_delete=models.PROTECT,
        related_name="production_orders",
    )
    scheduled_start = models.DateField(null=True, blank=True)
    scheduled_end = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "production_production_order"
        ordering = ["company", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"],
                name="uq_production_order_company_number",
            ),
        ]

    def __str__(self) -> str:
        return f"WO {self.number} [{self.status}]"

    @property
    def is_editable(self) -> bool:
        """Header may be mutated only while DRAFT."""
        return self.status == ProductionOrderStatus.DRAFT
