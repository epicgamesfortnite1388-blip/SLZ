"""Planning — reorder policies for inventory planning (Stage 3).

A ``PlanningPolicy`` records, per company + warehouse, the inventory-reorder
parameters for ONE item: either a purchased ``catalog.Material`` or a produced
``engineering.CustomerProduct`` (exactly one of the two FKs is set). This is
plain min/max-style policy data — no invented business rule; the planner decides
the numbers. The planning engine (``apps.planning.services``) reads these
policies together with live supply/demand records and produces *suggestions*
only — it never creates purchase or production orders (human review + the
existing order workflows stay in charge).
"""

from __future__ import annotations

from django.db import models

from apps.core.models import BaseModel


class PlanningPolicy(BaseModel):
    """Reorder policy for one item in one warehouse of one company."""

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="planning_policies"
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse", on_delete=models.PROTECT, related_name="planning_policies"
    )
    # Exactly one of material / customer_product must be set (enforced below).
    material = models.ForeignKey(
        "catalog.Material",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_policies",
    )
    customer_product = models.ForeignKey(
        "engineering.CustomerProduct",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_policies",
    )
    # Below this projected level the engine suggests replenishment.
    reorder_point = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    # Order-up-to level: suggested qty = target_level - projected.
    target_level = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    # Informational safety buffer (displayed; not part of the formula).
    safety_stock = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    # Preferred supplier for replenishment suggestions (materials only).
    preferred_supplier = models.ForeignKey(
        "partners.Supplier",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_policies",
    )
    # Optional lead-time override in days (informational for the suggestion).
    lead_time_days = models.PositiveSmallIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "planning_policy"
        ordering = ["company", "warehouse", "id"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(material__isnull=False, customer_product__isnull=True)
                    | models.Q(material__isnull=True, customer_product__isnull=False)
                ),
                name="ck_planning_policy_single_item",
            ),
            models.UniqueConstraint(
                fields=["company", "warehouse", "material"],
                condition=models.Q(material__isnull=False),
                name="uq_planning_policy_company_wh_material",
            ),
            models.UniqueConstraint(
                fields=["company", "warehouse", "customer_product"],
                condition=models.Q(customer_product__isnull=False),
                name="uq_planning_policy_company_wh_cp",
            ),
        ]

    def __str__(self) -> str:
        item = self.material.code if self.material_id else self.customer_product.code
        return f"{item} @ {self.warehouse_id} [{self.company_id}]"

    @property
    def item_code(self) -> str:
        return self.material.code if self.material_id else self.customer_product.code

    @property
    def item_name_fa(self) -> str:
        if self.material_id:
            return self.material.name_fa
        return self.customer_product.name_fa

    @property
    def item_type(self) -> str:
        """PURCHASED (raw material) or PRODUCED (manufactured customer product)."""
        return "MATERIAL" if self.material_id else "PRODUCT"
