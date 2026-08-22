"""Costing app — dated weighted-average material valuation.

Confirmed business decision: material valuation is WA Dated (not simple WA).
Each receipt, issue, and production output creates an immutable cost layer.
The weighted-average unit cost is calculated as of any date from all layers
up to that date, weighted by quantity.

Layers are append-only. No layer is ever edited or deleted — corrections
arrive as new ADJUSTMENT layers.
"""

from __future__ import annotations

from django.db import models

from apps.core.models import BaseModel


class CostLayerType(models.TextChoices):
    RECEIPT = "RECEIPT", "Receipt"
    ISSUE = "ISSUE", "Issue"
    PRODUCTION_OUTPUT = "PRODUCTION_OUTPUT", "Production output"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"


class CostLayer(BaseModel):
    """One immutable cost entry. Together they form the WA ledger.

    Every stock movement that carries a monetary value posts one cost layer
    at the same time. The layer records:
    - what material was valued
    - when the event happened
    - the quantity and unit cost
    - the total cost (quantity × unit_cost for receipts/adjustments;
      issues use the prevailing WA at the time)
    - a reference back to the source record (GRN line, issue, output)
    - an optional PO line for receipt → purchase-price provenance

    WA cost for a material as of a date is:
        sum(receipt_total + adjustment_total - issue_total
            up to that date)
        /
        sum(receipt_qty + adjustment_qty - issue_qty
            up to that date)
    """

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="cost_layers"
    )
    material = models.ForeignKey(
        "catalog.Material", on_delete=models.PROTECT, related_name="cost_layers"
    )
    date = models.DateField(db_index=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=6)
    total_cost = models.DecimalField(max_digits=18, decimal_places=6)
    layer_type = models.CharField(max_length=20, choices=CostLayerType.choices)
    reference_type = models.CharField(max_length=120, blank=True, default="")
    reference_id = models.UUIDField(null=True, blank=True)
    po_line_id = models.UUIDField(null=True, blank=True)
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "costing_cost_layer"
        ordering = ["material", "date", "created_at"]
        indexes = [
            models.Index(fields=["company", "material", "date"]),
        ]

    def __str__(self) -> str:
        return f"{self.layer_type} {self.material_id} " f"q={self.quantity} @ {self.unit_cost}"
