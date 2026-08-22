"""Inventory execution services — the sanctioned way to move stock.

``StockMovement`` is the append-only source of truth; balances are always
derived from it, never stored (SR-10 kardex semantics).

Rules enforced here (confirmed decisions):
* Q-046/Q-049 — movements reference a serialized/batched ``TraceabilityUnit``
  whenever the material category requires one; bulk materials may move without
  a unit.
* Negative stock is impossible: an OUT may never drive the on-hand quantity of
  its (material, warehouse) or traceability unit below zero.
* Quarantined stock cannot be issued: OUT movements from a warehouse whose
  store type is QUARANTINE are rejected.
* Every posting is atomic and emits an audit event via the standard bus.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Case, DecimalField, F, Sum, Value, When

from apps.core.exceptions import BusinessRuleError
from apps.core.middleware import get_correlation_id
from apps.inventory.models import StockMovement, StockMovementDirection, WarehouseStoreType

_IN = StockMovementDirection.IN
_OUT = StockMovementDirection.OUT


def _fmt(value: Decimal) -> str:
    """Plain decimal string without trailing zeros (stable API output)."""
    text = format(Decimal(value), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _signed(direction: str, quantity) -> Decimal:
    value = Decimal(quantity)
    return value if direction == _IN else -value


@transaction.atomic
def post_movement(
    *,
    company,
    warehouse,
    direction: str,
    quantity,
    uom,
    material=None,
    traceability_unit=None,
    reference_type: str = "",
    reference_id=None,
    notes: str = "",
    actor=None,
):
    """Append one validated movement row and return it.

    Guards:
    * ``quantity`` must be positive.
    * An OUT cannot drive the on-hand quantity of its (material | unit,
      warehouse) pair below zero (no negative stock).
    * Issuing from a quarantine store is forbidden.
    """
    if quantity is None or Decimal(quantity) <= 0:
        raise BusinessRuleError(
            "Movement quantity must be positive.", code="inventory.quantity_invalid"
        )
    if direction not in (_IN, _OUT, StockMovementDirection.TRANSFER):
        raise BusinessRuleError("Unknown direction.", code="inventory.direction_invalid")
    if direction != _IN and warehouse.store_type == WarehouseStoreType.QUARANTINE:
        raise BusinessRuleError(
            "Quarantined stock cannot be issued.", code="inventory.quarantine_issue"
        )

    if direction == _OUT:
        on_hand = on_hand_quantity(
            company=company,
            warehouse=warehouse,
            material=material,
            traceability_unit=traceability_unit,
        )
        if on_hand < Decimal(quantity):
            raise BusinessRuleError(
                f"Insufficient stock: on hand {on_hand}, requested {quantity}.",
                code="inventory.insufficient_stock",
            )

    movement = StockMovement.objects.create(
        company=company,
        warehouse=warehouse,
        traceability_unit=traceability_unit,
        material=material,
        direction=direction,
        quantity=Decimal(quantity),
        uom=uom,
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes,
        created_by=actor,
        updated_by=actor,
    )
    from apps.audit.services import record_audit

    record_audit(
        action="CREATE",
        entity_type="inventory.StockMovement",
        entity_id=str(movement.id),
        actor=actor,
        after_state={
            "direction": direction,
            "quantity": str(movement.quantity),
            "warehouse": str(warehouse.pk),
            "material": str(getattr(material, "pk", None)) if material else None,
            "unit": str(traceability_unit.pk) if traceability_unit else None,
        },
        metadata={"reference_type": reference_type},
        correlation_id=get_correlation_id() or "",
    )
    return movement


def on_hand_quantity(*, company, warehouse=None, material=None, traceability_unit=None) -> Decimal:
    """Derived on-hand quantity from the append-only ledger."""
    qs = StockMovement.objects.filter(company=company)
    if warehouse is not None:
        qs = qs.filter(warehouse=warehouse)
    if material is not None:
        qs = qs.filter(material=material)
    if traceability_unit is not None:
        qs = qs.filter(traceability_unit=traceability_unit)
    signed_sum = qs.aggregate(
        net=Sum(
            Case(
                When(direction=_IN, then=F("quantity")),
                When(direction=_OUT, then=-F("quantity")),
                default=Value(0),
                output_field=DecimalField(),
            )
        )
    )["net"]
    return Decimal(signed_sum or 0)


def balances(company, *, warehouse=None, material=None) -> list[dict]:
    """Grouped on-hand rows for one company, optionally narrowed.

    Returns dicts of {warehouse, material, traceability_unit, uom, on_hand}
    covering every dimension combination that has at least one movement.
    """
    qs = StockMovement.objects.filter(company=company)
    if warehouse is not None:
        qs = qs.filter(warehouse=warehouse)
    if material is not None:
        qs = qs.filter(material=material)

    dims = ("warehouse_id", "material_id", "traceability_unit_id", "uom_id")
    grouped = (
        qs.values(*dims)
        .annotate(
            on_hand=Sum(
                Case(
                    When(direction=_IN, then=F("quantity")),
                    When(direction=_OUT, then=-F("quantity")),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            )
        )
        .order_by(*dims)
    )
    return [
        {
            "warehouse": row["warehouse_id"],
            "material": row["material_id"],
            "traceability_unit": row["traceability_unit_id"],
            "uom": row["uom_id"],
            "on_hand": _fmt(row["on_hand"] or 0),
        }
        for row in grouped
    ]


def kardex(*, company, traceability_unit=None, material=None, warehouse=None) -> list[dict]:
    """Chronological movement history with a running balance."""
    qs = StockMovement.objects.filter(company=company).select_related(
        "warehouse", "material", "traceability_unit", "uom"
    )
    if traceability_unit is not None:
        qs = qs.filter(traceability_unit=traceability_unit)
    if material is not None:
        qs = qs.filter(material=material)
    if warehouse is not None:
        qs = qs.filter(warehouse=warehouse)

    running = Decimal(0)
    rows = []
    for m in qs.order_by("created_at", "id"):
        running += _signed(m.direction, m.quantity)
        rows.append(
            {
                "id": str(m.id),
                "timestamp": m.created_at,
                "warehouse": m.warehouse_id,
                "material": m.material_id,
                "traceability_unit": m.traceability_unit_id,
                "direction": m.direction,
                "quantity": str(m.quantity),
                "uom": m.uom_id,
                "balance_after": _fmt(running),
                "reference_type": m.reference_type,
                "reference_id": str(m.reference_id) if m.reference_id else None,
            }
        )
    return rows
