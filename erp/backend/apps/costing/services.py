"""Costing services — dated weighted-average valuation engine.

Every inventory movement that changes material value posts a cost layer.
The weighted-average cost for a material as of any date is derived from
all layers up to that date. Layers are never edited or deleted.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.costing.models import CostLayer, CostLayerType


def _fmt(value: Decimal) -> str:
    """Normalize a Decimal to a string without trailing fractional zeros."""
    s = format(Decimal(value), ".6f")
    if "." in s:
        whole, frac = s.rsplit(".", 1)
        frac = frac.rstrip("0")
        return f"{whole}.{frac}" if frac else whole
    return s


def _safe_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


@transaction.atomic
def post_cost_layer(
    *,
    company,
    material,
    date,
    quantity,
    unit_cost,
    layer_type: str,
    reference_type: str = "",
    reference_id=None,
    po_line_id=None,
    notes: str = "",
    actor=None,
) -> CostLayer:
    """Create one immutable cost layer and return it.

    For ISSUE layers, ``unit_cost`` should be the current WA cost at the
    time of issue (call ``wa_unit_cost`` first). The total_cost is
    quantity × unit_cost.
    """
    qty = _safe_decimal(quantity)
    uc = _safe_decimal(unit_cost)
    total = (qty * uc).quantize(Decimal("0.000001"))

    layer = CostLayer.objects.create(
        company=company,
        material=material,
        date=date,
        quantity=qty,
        unit_cost=uc,
        total_cost=total,
        layer_type=layer_type,
        reference_type=reference_type,
        reference_id=reference_id,
        po_line_id=po_line_id,
        notes=notes,
        created_by=actor,
        updated_by=actor,
    )
    return layer


def wa_unit_cost(company, material, as_of_date=None) -> Decimal:
    """Dated weighted-average unit cost.

    Returns the WA unit cost for one material as of ``as_of_date``
    (inclusive). If no layers exist, returns Decimal(0).

    Formula:
        WA = total_net_cost / total_net_quantity
    where net = sum(all RECEIPT + ADJUSTMENT layers) - sum(all ISSUE layers)
    up to as_of_date.
    """
    qs = CostLayer.objects.filter(company=company, material=material)
    if as_of_date is not None:
        qs = qs.filter(date__lte=as_of_date)

    # Receipts and adjustments add cost; issues remove it.
    additions = qs.filter(layer_type__in=[CostLayerType.RECEIPT, CostLayerType.ADJUSTMENT])
    issues = qs.filter(layer_type=CostLayerType.ISSUE)

    add_cost = additions.aggregate(t=Sum("total_cost"))["t"] or Decimal("0")
    add_qty = additions.aggregate(q=Sum("quantity"))["q"] or Decimal("0")
    iss_cost = issues.aggregate(t=Sum("total_cost"))["t"] or Decimal("0")
    iss_qty = issues.aggregate(q=Sum("quantity"))["q"] or Decimal("0")

    net_cost = add_cost - iss_cost
    net_qty = add_qty - iss_qty

    if net_qty <= 0:
        return Decimal("0")
    return (net_cost / net_qty).quantize(Decimal("0.000001"))


def cost_layers_for(company, material=None, as_of_date=None):
    """Chronological cost layers, optionally filtered by material and date."""
    qs = CostLayer.objects.filter(company=company).select_related("material")
    if material is not None:
        qs = qs.filter(material=material)
    if as_of_date is not None:
        qs = qs.filter(date__lte=as_of_date)
    return qs


def cost_summary(company, as_of_date=None):
    """Per-material cost summary: WA cost, total quantity, total cost.

    Returns a list of dicts with {material_id, wa_unit_cost, on_hand_qty, on_hand_cost}.
    Uses a single bulk aggregation pass instead of N+1 per-material queries.
    """
    from apps.catalog.models import Material

    # Bulk-fetch materials in one query
    materials = list(Material.objects.filter(company=company).values_list("id", flat=True))
    if not materials:
        return []

    # Single aggregation pass: per-material cost totals
    qs = CostLayer.objects.filter(company=company, material_id__in=materials)
    if as_of_date is not None:
        qs = qs.filter(date__lte=as_of_date)

    add_qs = qs.filter(layer_type__in=[CostLayerType.RECEIPT, CostLayerType.ADJUSTMENT])
    iss_qs = qs.filter(layer_type=CostLayerType.ISSUE)

    add_totals = {
        row["material_id"]: {
            "total_cost": row["tc"] or Decimal("0"),
            "quantity": row["q"] or Decimal("0"),
        }
        for row in add_qs.values("material_id").annotate(tc=Sum("total_cost"), q=Sum("quantity"))
    }
    iss_totals = {
        row["material_id"]: {
            "total_cost": row["tc"] or Decimal("0"),
            "quantity": row["q"] or Decimal("0"),
        }
        for row in iss_qs.values("material_id").annotate(tc=Sum("total_cost"), q=Sum("quantity"))
    }

    results = []
    for mid in materials:
        add = add_totals.get(mid, {"total_cost": Decimal("0"), "quantity": Decimal("0")})
        iss = iss_totals.get(mid, {"total_cost": Decimal("0"), "quantity": Decimal("0")})

        net_cost = add["total_cost"] - iss["total_cost"]
        net_qty = add["quantity"] - iss["quantity"]

        wa = (net_cost / net_qty).quantize(Decimal("0.000001")) if net_qty > 0 else Decimal("0")
        on_hand = net_qty

        if on_hand > 0 or wa > 0:
            results.append(
                {
                    "material_id": str(mid),
                    "wa_unit_cost": _fmt(wa),
                    "on_hand_qty": _fmt(on_hand),
                    "on_hand_cost": _fmt(on_hand * wa),
                }
            )
    return results
