"""Inventory Foundation — Warehouses, store types & per-user access (Task 007).

This app owns the inventory master data and the confirmed traceability/execution foundation:
*where* stock can live (warehouses, typed by their special store role) and *who*
may access each warehouse (SR-10). It deliberately does **not** yet model any
stock quantity, movement, lot, roll, batch, genealogy or kardex.

Scope discipline (see docs/business-analysis/inventory-model.md, skill
05-inventory-traceability, docs/reconciliation/slz-specific-rules.md SR-08/09/10,
docs/requirements/do-not-build-yet.md):

Built here (CONFIRMED, un-gated):
* ``Warehouse`` — company/site-scoped (DR-040 / SR-15), carrying the SR-10
  **special store type** (scrap, quarantine, cliché, line-side (پای کار),
  consignment (امانی), stagnant (راکد), plus RM/WIP/FG/general/staging/returns).
  "Unlimited warehouses with special store types" (SR-10).
* ``WarehouseAccess`` — the SR-10 **per-user warehouse access** mechanism (a
  user × warehouse grant with an access level). The *content* (which user gets
  which warehouse) is data; the concrete role catalogue stays OPEN (Q-053).

Deliberately NOT built (OPEN gates — do-not-build-yet):
* Stock movements / quantity-on-hand / **rial+quantity kardex** (SR-10) — a
  movement references a lot/roll whose identity is gated on Q-046; valuation is
  gated on Q-034/#2. Never mutate a quantity; movements are append-only when built.
* **Raw-material lots, rolls/reels, production batches and parent→child
  genealogy** (SR-08) — the roll **serialization vs lot+count** decision
  (Q-046 / DR-020, do-not-build-yet #18) is the *highest-priority* foundational
  gate and "must be decided before the traceability schema is migrated" (C-003).
* Two-stage goods receipt temporary → QC → definitive (SR-09), reservations /
  availability (Q-050), the consumption-permit transaction (SR-10), material
  issue method explicit-vs-backflush (Q-048/#21), inventoried intermediates /
  BOM levels (Q-026/#19), traceability granularity (Q-049/#20), shelf-life /
  FEFO enforcement (Q-051/#16) and recall/mock-recall automation (#31).
* Sub-warehouse **Location / Zone / bin** model — whether bin-level tracking is
  needed at all is OPEN (Q-047); the confirmed unit is the warehouse itself.

Per-user access is declarative master data here: no stock operation exists yet
to enforce it against. Enforcement wires in when the movement layer is built,
once Q-046 is resolved.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, SoftDeleteModel


class TraceabilityUnitType(models.TextChoices):
    BATCH = "BATCH", "Batch"
    ROLL = "ROLL", "Roll"
    PALLET = "PALLET", "Pallet"
    CARTON = "CARTON", "Carton"


class StockMovementDirection(models.TextChoices):
    IN = "IN", "In"
    OUT = "OUT", "Out"
    TRANSFER = "TRANSFER", "Transfer"


class WarehouseStoreType(models.TextChoices):
    """The special store types SLZ warehouses carry (SR-10).

    Grounded in ``docs/business-analysis/inventory-model.md`` §2 (location types)
    and SR-10's explicit special stores. This is a CONFIRMED enum of *roles a
    warehouse plays* — it does not encode any stock behaviour (that is the gated
    movement layer). Adding a role is adding a choice, not code.
    """

    GENERAL = "GENERAL", "General"
    RAW_MATERIAL = "RAW_MATERIAL", "Raw material"
    WIP = "WIP", "Work in progress"
    FINISHED_GOODS = "FINISHED_GOODS", "Finished goods"
    SCRAP = "SCRAP", "Scrap"
    QUARANTINE = "QUARANTINE", "Quarantine"
    CLICHE = "CLICHE", "Cliché / printing tooling"
    LINE_SIDE = "LINE_SIDE", "Line-side (پای کار)"
    CONSIGNMENT = "CONSIGNMENT", "Consignment (امانی)"
    STAGNANT = "STAGNANT", "Stagnant / slow-moving (راکد)"
    SHIPPING_STAGING = "SHIPPING_STAGING", "Shipping / staging"
    RETURNS = "RETURNS", "Returns"


class WarehouseAccessLevel(models.TextChoices):
    """How much a user may do in a warehouse (SR-10 per-user access).

    Kept intentionally coarse (view vs operate) — the fine-grained role/scoping
    catalogue is OPEN (Q-053, do-not-build-yet #8). Absence of a grant means no
    access; there is no explicit NONE row.
    """

    VIEW = "VIEW", "View"
    OPERATE = "OPERATE", "Operate"


class TraceabilityUnit(BaseModel):
    """A serialized or batch handling unit used by the confirmed traceability policy.

    Roll IDs are unique physical entities. Pallets and cartons are handling units
    with explicit parent links; the model does not infer packing quantities.
    """

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="traceability_units"
    )
    material = models.ForeignKey(
        "catalog.Material",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="traceability_units",
    )
    # UUID provenance reference avoids a catalog/engineering/inventory migration
    # cycle; the production and engineering APIs validate the owning record.
    customer_product_id = models.UUIDField(null=True, blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    unit_type = models.CharField(max_length=10, choices=TraceabilityUnitType.choices)
    identifier = models.CharField(max_length=80)
    quantity = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    uom = models.ForeignKey(
        "catalog.UnitOfMeasure",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="traceability_units",
    )
    weight = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    length = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    width = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    core = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "inventory_traceability_unit"
        ordering = ["company", "identifier"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "identifier"], name="uq_traceability_unit_company_identifier"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.identifier} [{self.unit_type}]"


class GenealogyLink(BaseModel):
    """Directed parent/child genealogy between traceability units."""

    parent = models.ForeignKey(
        TraceabilityUnit, on_delete=models.PROTECT, related_name="genealogy_parents"
    )
    child = models.ForeignKey(
        TraceabilityUnit, on_delete=models.PROTECT, related_name="genealogy_children"
    )
    production_order_id = models.UUIDField(null=True, blank=True)
    operation_label = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        db_table = "inventory_genealogy_link"
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "child", "production_order_id"],
                name="uq_genealogy_parent_child_order",
            ),
        ]


class StockMovement(BaseModel):
    """Append-only quantity movement; balance is derived from these rows."""

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="stock_movements"
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse", on_delete=models.PROTECT, related_name="stock_movements"
    )
    traceability_unit = models.ForeignKey(
        TraceabilityUnit,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    material = models.ForeignKey(
        "catalog.Material",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    direction = models.CharField(max_length=10, choices=StockMovementDirection.choices)
    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    uom = models.ForeignKey(
        "catalog.UnitOfMeasure", on_delete=models.PROTECT, related_name="stock_movements"
    )
    reference_type = models.CharField(max_length=120)
    reference_id = models.UUIDField(null=True, blank=True)
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "inventory_stock_movement"
        ordering = ["created_at", "id"]


class Warehouse(SoftDeleteModel):
    """A stock-holding location, company/site-scoped and typed by store role.

    SLZ runs **unlimited warehouses with special store types** (SR-10). A
    warehouse is company-scoped (DR-040) and normally sits at a ``site``
    (SR-15); ``site`` is optional because virtual/consignment stores may not map
    to a physical facility and NQ-002 (exact site list) is still OPEN — mirrors
    the ``WorkCenter``/``Machine`` precedent. ``store_type`` declares the role;
    it carries NO stock behaviour (movements/kardex are the gated later layer).
    """

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="warehouses"
    )
    site = models.ForeignKey(
        "organization.Site",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="warehouses",
    )
    code = models.CharField(max_length=60)
    name_fa = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    store_type = models.CharField(
        max_length=20,
        choices=WarehouseStoreType.choices,
        default=WarehouseStoreType.GENERAL,
    )
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "inventory_warehouse"
        ordering = ["company", "code"]
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="uq_warehouse_company_code"),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name_fa}"


class WarehouseAccess(BaseModel):
    """A per-user access grant to a warehouse (SR-10).

    One grant per (warehouse, user). Hard-deletable: a revoked grant carries no
    historical business meaning of its own (the audit log records the CREATE /
    DELETE events). This is declarative master data — no stock operation yet
    enforces it; enforcement is wired in with the gated movement layer.
    """

    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="access_grants")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="warehouse_access",
    )
    access_level = models.CharField(
        max_length=10,
        choices=WarehouseAccessLevel.choices,
        default=WarehouseAccessLevel.VIEW,
    )

    class Meta:
        db_table = "inventory_warehouse_access"
        ordering = ["warehouse", "user"]
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "user"], name="uq_warehouse_access_wh_user"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}@{self.warehouse_id}:{self.access_level}"
