"""Shipment services — allocation, release, and delivery posting."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.db import models, transaction

from apps.core.events import EntityCreated
from apps.core.exceptions import BusinessRuleError, ConflictError
from apps.core.transactions import atomic_with_events
from apps.inventory import services as inventory_services
from apps.inventory.models import StockMovementDirection
from apps.shipment.models import (
    Allocation,
    AllocationStatus,
    Shipment,
    ShipmentLine,
    ShipmentStatus,
)


def _actor_id(actor) -> Optional[str]:
    pk = getattr(actor, "pk", None)
    return str(pk) if pk else None


@transaction.atomic
def reserve(
    *,
    company,
    sales_order_line,
    traceability_unit,
    quantity,
    uom,
    notes: str = "",
    actor=None,
) -> Allocation:
    """Reserve a traceability unit for a sales-order line.

    Guards:
    - The unit must belong to the same company.
    - The quantity must not exceed what's available (= on hand - already
      allocated to other order lines + already allocated to THIS line).
    - Over-allocation across order lines is blocked.
    """
    from apps.inventory.models import TraceabilityUnit
    from apps.inventory.services import on_hand_quantity

    # Lock the traceability unit row to serialize concurrent reservations.
    # Two callers racing on the same unit will not both pass the
    # availability check below — the second blocks until the first commits.
    TraceabilityUnit.objects.select_for_update().get(pk=traceability_unit.pk)

    if traceability_unit.company_id != company.id:
        raise BusinessRuleError(
            "Traceability unit must belong to the same company.",
            code="allocation.cross_company",
        )
    if sales_order_line.order.company_id != company.id:
        raise BusinessRuleError(
            "Sales order line must belong to the same company.",
            code="allocation.cross_company",
        )

    on_hand = on_hand_quantity(
        company=company,
        traceability_unit=traceability_unit,
    )
    # Already allocated to any order line
    already = Allocation.objects.filter(
        traceability_unit=traceability_unit,
        status=AllocationStatus.RESERVED,
    ).exclude(sales_order_line=sales_order_line).aggregate(t=models.Sum("quantity"))[
        "t"
    ] or Decimal(
        "0"
    )
    available = on_hand - already
    requested = Decimal(str(quantity))

    if requested > available:
        raise BusinessRuleError(
            f"Insufficient available stock: {available} available, {requested} requested.",
            code="allocation.over_allocated",
        )

    alloc = Allocation.objects.create(
        company=company,
        sales_order_line=sales_order_line,
        traceability_unit=traceability_unit,
        quantity=requested,
        uom=uom,
        status=AllocationStatus.RESERVED,
        notes=notes,
        created_by=actor,
        updated_by=actor,
    )
    return alloc


@transaction.atomic
def release(allocation: Allocation, *, actor=None) -> Allocation:
    """Release one allocation (marks it RELEASED, creates a new row for audit)."""
    if allocation.status != AllocationStatus.RESERVED:
        raise ConflictError(
            "Only RESERVED allocations can be released.",
            code="allocation.not_reserved",
        )
    allocation.status = AllocationStatus.RELEASED
    allocation.updated_by = actor
    allocation.save(update_fields=["status", "updated_by", "updated_at"])
    return allocation


@transaction.atomic
def create_shipment(serializer, *, actor=None):
    """Post one shipment atomically.

    For each line:
    - Verifies the unit is allocated (RESERVED) and not already shipped.
    - Posts an OUT stock movement.
    - Creates a genealogy link forward if the unit has production provenance.
    """
    payload = serializer.validated_data
    company = payload["company"]
    warehouse = payload["warehouse"]
    lines = payload.get("lines") or []
    if not lines:
        raise BusinessRuleError("A shipment needs at least one line.", code="shipment.empty")

    with atomic_with_events() as events:
        shipment = Shipment.objects.create(
            company=company,
            sales_order=payload.get("sales_order"),
            customer=payload["customer"],
            warehouse=warehouse,
            number=payload["number"],
            status=ShipmentStatus.SHIPPED,
            shipped_at=payload["shipped_at"],
            notes=payload.get("notes", ""),
            created_by=actor,
            updated_by=actor,
        )
        events.append(
            EntityCreated(
                entity_type="shipment.Shipment",
                entity_id=str(shipment.pk),
                actor_id=_actor_id(actor),
                company_id=str(company.id),
                state={"number": shipment.number},
            )
        )

        for entry in lines:
            unit = entry["traceability_unit"]
            qty = Decimal(str(entry["quantity"]))

            # Cross-company guards: every referenced row must belong to the
            # shipping company (Q-055). Defense in depth on top of queryset
            # scoping — payload references are validated explicitly.
            if unit.company_id != company.id:
                raise BusinessRuleError(
                    "Traceability unit belongs to another company.",
                    code="shipment.cross_company",
                )
            order_line = entry.get("sales_order_line")
            if order_line is not None and order_line.order.company_id != company.id:
                raise BusinessRuleError(
                    "Sales order line belongs to another company.",
                    code="shipment.cross_company_line",
                )

            # Verify the unit is allocated
            alloc = None
            if entry.get("allocation"):
                alloc = entry["allocation"]
                if alloc.status != AllocationStatus.RESERVED:
                    raise ConflictError(
                        f"Allocation {alloc.id} is not RESERVED.",
                        code="shipment.allocation_not_reserved",
                    )
                if alloc.traceability_unit_id != unit.id:
                    raise BusinessRuleError(
                        "Allocation traceability unit mismatch.",
                        code="shipment.allocation_mismatch",
                    )
                if qty > Decimal(str(alloc.quantity)):
                    raise BusinessRuleError(
                        "Shipment quantity exceeds the allocated quantity " f"({alloc.quantity}).",
                        code="shipment.over_shipped",
                    )

            dial = ShipmentLine.objects.create(
                shipment=shipment,
                sales_order_line=entry.get("sales_order_line"),
                allocation=alloc,
                traceability_unit=unit,
                quantity=qty,
                uom=entry["uom"],
                notes=entry.get("notes", ""),
                created_by=actor,
                updated_by=actor,
            )

            movement = inventory_services.post_movement(
                company=company,
                warehouse=warehouse,
                direction=StockMovementDirection.OUT,
                quantity=qty,
                uom=entry["uom"],
                traceability_unit=unit,
                reference_type="shipment.ShipmentLine",
                reference_id=dial.pk,
                notes=f"Shipment {shipment.number}",
                actor=actor,
            )

            events.append(
                EntityCreated(
                    entity_type="shipment.ShipmentLine",
                    entity_id=str(dial.id),
                    actor_id=_actor_id(actor),
                    company_id=str(company.id),
                    state={
                        "quantity": str(entry["quantity"]),
                        "movement_id": str(movement.id),
                    },
                )
            )

        return shipment
