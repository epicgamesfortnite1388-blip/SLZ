"""Shipment — Allocation, reservation, and delivery (SR-08 downstream).

Allocation reserves traceability units for specific sales-order lines.
Shipment posts OUT stock movements against allocated units and records
customer delivery provenance.

Both are append-only: allocations can be released (a new DEALLOCATION row),
but never edited; shipments are immutable execution records.
"""

from __future__ import annotations

from django.db import models

from apps.core.models import BaseModel, SoftDeleteModel


class AllocationStatus(models.TextChoices):
    RESERVED = "RESERVED", "Reserved"
    RELEASED = "RELEASED", "Released"
    SHIPPED = "SHIPPED", "Shipped"


class ShipmentStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SHIPPED = "SHIPPED", "Shipped"
    VOIDED = "VOIDED", "Voided"


class Allocation(BaseModel):
    """One reservation of a traceability unit for a sales-order line.

    If the unit has already been shipped or allocated elsewhere, the
    service rejects with an over-allocation error.
    A release creates a new RELEASED row; the original RESERVED row is
    never mutated.
    """

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="allocations"
    )
    sales_order_line = models.ForeignKey(
        "sales.SalesOrderLine",
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    traceability_unit = models.ForeignKey(
        "inventory.TraceabilityUnit",
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    uom = models.ForeignKey(
        "catalog.UnitOfMeasure", on_delete=models.PROTECT, related_name="allocations"
    )
    status = models.CharField(
        max_length=10,
        choices=AllocationStatus.choices,
        default=AllocationStatus.RESERVED,
    )
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "shipment_allocation"
        ordering = ["company", "created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name="ck_allocation_quantity_positive",
            ),
        ]

    def __str__(self) -> str:
        return f"Alloc {self.traceability_unit_id} → {self.sales_order_line_id}"


class Shipment(SoftDeleteModel):
    """One delivery to a customer, referencing a sales order.

    Created directly in SHIPPED state; every line posts an OUT movement.
    The shipment is immutable after posting.
    """

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="shipments"
    )
    sales_order = models.ForeignKey(
        "sales.SalesOrder",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="shipments",
    )
    customer = models.ForeignKey(
        "partners.Customer",
        on_delete=models.PROTECT,
        related_name="shipments",
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse", on_delete=models.PROTECT, related_name="shipments"
    )
    number = models.CharField(max_length=40)
    status = models.CharField(
        max_length=10,
        choices=ShipmentStatus.choices,
        default=ShipmentStatus.SHIPPED,
        db_index=True,
    )
    shipped_at = models.DateField()
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "shipment_shipment"
        ordering = ["-shipped_at", "company"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"],
                name="uq_shipment_company_number",
            ),
        ]

    def __str__(self) -> str:
        return f"Shipment {self.number}"


class ShipmentLine(BaseModel):
    """One shipped unit: links the traceability unit and posts an OUT movement."""

    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="lines")
    sales_order_line = models.ForeignKey(
        "sales.SalesOrderLine",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="shipment_lines",
    )
    allocation = models.ForeignKey(
        Allocation,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="shipment_lines",
    )
    traceability_unit = models.ForeignKey(
        "inventory.TraceabilityUnit",
        on_delete=models.PROTECT,
        related_name="shipment_lines",
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    uom = models.ForeignKey(
        "catalog.UnitOfMeasure", on_delete=models.PROTECT, related_name="shipment_lines"
    )
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "shipment_shipment_line"
        ordering = ["shipment", "pk"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name="ck_shipment_line_quantity_positive",
            ),
        ]
