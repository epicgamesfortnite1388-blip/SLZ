"""Planning engine — deterministic inventory replenishment suggestions.

The engine is deliberately read-only: it aggregates live supply/demand records
and returns suggestions. It never creates purchase or production orders —
humans review suggestions and use the existing order workflows.

Inputs per policy (each computed from the append-only ledger / open documents):

* on_hand            — ledger-derived stock in the policy warehouse
* allocated          — RESERVED allocations against the item's stock (finished
                       products only; raw-material units are not reservation
                       targets in this architecture)
* incoming_purchase  — remaining open quantity on APPROVED/SENT purchase-order
                       lines (materials only; POs carry materials)
* open_production    — remaining planned quantity on RELEASED production orders
                       (finished products only)
* open_demand        — CONFIRMED sales-order line quantities (finished products
                       only)

Formula (honest, no fabricated precision):

    projected = on_hand + incoming_purchase + open_production - allocated - open_demand
    if projected < reorder_point:
        suggested_qty = max(0, target_level - projected)
        action = PURCHASE (materials) or MANUFACTURE (products)

Raw-material *demand* from BOM explosion is NOT modelled here — it needs the
consumption-basis dataset that remains business-open — so material rows carry
no open_demand and act as pure reorder-point replenishment policies. This is
documented rather than guessed.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional

from django.db.models import Sum

from apps.procurement.models import GoodsReceiptLine, PurchaseOrderLine, PurchaseOrderStatus
from apps.production.models import ProductionOrder, ProductionOrderStatus, ProductionOutput
from apps.sales.models import SalesOrderLine, SalesOrderStatus
from apps.shipment.models import Allocation, AllocationStatus


@dataclass
class PlanningRow:
    policy_id: int
    item_code: str
    item_name_fa: str
    item_type: str  # MATERIAL | PRODUCT
    warehouse_id: Optional[int]
    on_hand: Decimal
    allocated: Decimal
    incoming_purchase: Decimal
    open_production: Decimal
    open_demand: Decimal
    projected: Decimal
    reorder_point: Decimal
    target_level: Decimal
    safety_stock: Optional[Decimal]
    lead_time_days: Optional[int]
    suggested_qty: Decimal
    action: str  # NONE | PURCHASE | MANUFACTURE
    reason: str


ZERO = Decimal("0")


def _po_remaining_per_material(company, materials: Iterable) -> dict:
    """Open purchase supply per material (approved/sent, not fully received)."""
    if not materials:
        return {}
    open_lines = PurchaseOrderLine.objects.filter(
        material__in=materials,
        order__status__in=[PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.SENT],
        order__company=company,
    )
    per_line = {}
    for line in open_lines.select_related("order"):
        received = (
            GoodsReceiptLine.objects.filter(po_line=line).aggregate(total=Sum("quantity"))["total"]
            or 0
        )
        remaining = line.quantity - Decimal(str(received))
        per_line[line.material_id] = per_line.get(line.material_id, ZERO) + remaining
    return per_line


def _open_production_per_product(company, products: Iterable) -> dict:
    """Remaining planned quantity on RELEASED orders per produced item."""
    if not products:
        return {}
    result = {}
    orders = ProductionOrder.objects.filter(
        company=company, customer_product__in=products, status=ProductionOrderStatus.RELEASED
    )
    for order in orders:
        posted = (
            ProductionOutput.objects.filter(production_order=order).aggregate(
                total=Sum("quantity")
            )["total"]
            or 0
        )
        remaining = order.planned_quantity - Decimal(str(posted))
        if remaining > 0:
            result[order.customer_product_id] = (
                result.get(order.customer_product_id, ZERO) + remaining
            )
    return result


def _open_demand_per_product(company, products: Iterable) -> dict:
    """Confirmed (open) sales-order demand per produced item."""
    if not products:
        return {}
    rows = (
        SalesOrderLine.objects.filter(
            customer_product__in=products,
            order__company=company,
            order__status=SalesOrderStatus.CONFIRMED,
        )
        .values("customer_product_id")
        .annotate(total=Sum("quantity"))
    )
    return {r["customer_product_id"]: Decimal(str(r["total"])) for r in rows}


def _product_unit_ids(company, products) -> dict:
    """Map product -> traceability-unit ids that were produced for it."""
    outputs = ProductionOutput.objects.filter(
        production_order__company=company,
        production_order__customer_product__in=products,
    ).values_list("production_order__customer_product_id", "traceability_unit_id")
    mapping = {}
    for product_id, unit_id in outputs:
        mapping.setdefault(product_id, []).append(unit_id)
    return mapping


def _allocated_per_product(company, products) -> dict:
    """RESERVED allocation quantity against produced units, per product."""
    mapping = _product_unit_ids(company, products)
    result = {p: ZERO for p in products}
    if not mapping:
        return result
    all_unit_ids = [uid for ids in mapping.values() for uid in ids]
    rows = (
        Allocation.objects.filter(
            company=company,
            status=AllocationStatus.RESERVED,
            traceability_unit_id__in=all_unit_ids,
        )
        .values("traceability_unit_id")
        .annotate(total=Sum("quantity"))
    )
    by_unit = {r["traceability_unit_id"]: Decimal(str(r["total"])) for r in rows}
    for product_id, unit_ids in mapping.items():
        result[product_id] = sum((by_unit.get(uid, ZERO) for uid in unit_ids), ZERO)
    return result


def _material_on_hand(company, warehouse, material) -> Decimal:
    from apps.inventory.services import on_hand_quantity

    return on_hand_quantity(company=company, warehouse=warehouse, material=material)


def _product_on_hand(company, warehouse, unit_ids) -> Decimal:
    """Ledger on-hand for a set of produced units in one warehouse."""
    from django.db.models import Case, DecimalField, F, Value, When

    from apps.inventory.models import StockMovement, StockMovementDirection

    if not unit_ids:
        return ZERO
    net = StockMovement.objects.filter(
        company=company, warehouse=warehouse, traceability_unit_id__in=unit_ids
    ).aggregate(
        total=Sum(
            Case(
                When(direction=StockMovementDirection.IN, then=F("quantity")),
                When(direction=StockMovementDirection.OUT, then=-F("quantity")),
                default=Value(0),
                output_field=DecimalField(),
            )
        )
    )[
        "total"
    ]
    return Decimal(net or 0)


def run_planning(company, warehouse=None) -> list[PlanningRow]:
    """Compute suggestion rows for the company's ACTIVE policies."""
    from apps.planning.models import PlanningPolicy

    policies = PlanningPolicy.objects.filter(company=company, is_active=True).select_related(
        "warehouse", "material", "customer_product"
    )
    if warehouse is not None:
        policies = policies.filter(warehouse=warehouse)

    materials = [p.material for p in policies if p.material_id]
    products = [p.customer_product for p in policies if p.customer_product_id]

    po_supply = _po_remaining_per_material(company, materials)
    mo_supply = _open_production_per_product(company, products)
    demand = _open_demand_per_product(company, products)
    allocated = _allocated_per_product(company, products)
    product_unit_map = _product_unit_ids(company, products)

    rows = []
    for policy in policies:
        if policy.material_id:
            on_hand = _material_on_hand(company, policy.warehouse, policy.material)
            incoming = po_supply.get(policy.material_id, ZERO)
            open_prod = ZERO
            open_demand = ZERO
            alloc = ZERO
            action = "PURCHASE"
        else:
            unit_ids = product_unit_map.get(policy.customer_product_id, [])
            on_hand = _product_on_hand(company, policy.warehouse, unit_ids)
            incoming = ZERO
            open_prod = mo_supply.get(policy.customer_product_id, ZERO)
            open_demand = demand.get(policy.customer_product_id, ZERO)
            alloc = allocated.get(policy.customer_product_id, ZERO)
            action = "MANUFACTURE"

        projected = on_hand + incoming + open_prod - alloc - open_demand
        below = projected < policy.reorder_point
        suggested = ZERO
        reason = ""
        if below:
            suggested = max(ZERO, policy.target_level - projected)
            reason = "projected below reorder point"
            if suggested <= 0:
                suggested = ZERO
                reason = "projected below reorder point but target already covered"
                action = "NONE"
        else:
            action = "NONE"
            reason = "projected at or above reorder point"

        rows.append(
            PlanningRow(
                policy_id=policy.id,
                item_code=policy.item_code,
                item_name_fa=policy.item_name_fa,
                item_type=policy.item_type,
                warehouse_id=policy.warehouse_id,
                on_hand=on_hand,
                allocated=alloc,
                incoming_purchase=incoming,
                open_production=open_prod,
                open_demand=open_demand,
                projected=projected,
                reorder_point=policy.reorder_point,
                target_level=policy.target_level,
                safety_stock=policy.safety_stock,
                lead_time_days=policy.lead_time_days,
                suggested_qty=suggested,
                action=action,
                reason=reason,
            )
        )
    rows.sort(key=lambda r: (r.item_type, r.item_code))
    return rows


def summary_rows(rows: list[PlanningRow]) -> dict:
    """Compact summary counts for the planning screen / dashboard tile."""
    return {
        "total_policies": len(rows),
        "action_required": sum(1 for r in rows if r.action != "NONE"),
        "to_purchase": sum(1 for r in rows if r.action == "PURCHASE"),
        "to_manufacture": sum(1 for r in rows if r.action == "MANUFACTURE"),
        "low_stock_items": sum(1 for r in rows if r.action != "NONE"),
    }
