"""Integration hooks: auto-post cost layers from inventory movements.

Import this module to register cost-layer side effects when GRN receipts,
material issues, and production outputs create stock movements.
Callers opt in via post_cost_on_receipt / post_cost_on_issue.
"""

from __future__ import annotations

from decimal import Decimal

from apps.costing.models import CostLayerType
from apps.costing.services import post_cost_layer


def post_cost_on_receipt(
    *,
    company,
    material,
    date,
    quantity,
    unit_price: Decimal | None = None,
    po_line_id=None,
    reference_type: str = "",
    reference_id=None,
    actor=None,
):
    """Post a RECEIPT cost layer for one GRN line.

    If ``unit_price`` is None, the layer posts at unit_cost=0
    (pricing is optional in procurement). This preserves the costing
    audit trail; the price can be corrected via ADJUSTMENT layers later.
    """
    uc = unit_price if unit_price is not None else Decimal("0")
    return post_cost_layer(
        company=company,
        material=material,
        date=date,
        quantity=quantity,
        unit_cost=uc,
        layer_type=CostLayerType.RECEIPT,
        reference_type=reference_type,
        reference_id=reference_id,
        po_line_id=po_line_id,
        actor=actor,
    )


def post_cost_on_issue(
    *,
    company,
    material,
    date,
    quantity,
    reference_type: str = "",
    reference_id=None,
    actor=None,
):
    """Post an ISSUE cost layer for a material consumption.

    The unit_cost is derived from the current WA cost at issue time
    inside ``post_cost_layer`` (caller passes whatever WA they computed).
    """
    from apps.costing.services import wa_unit_cost

    uc = wa_unit_cost(company=company, material=material, as_of_date=date)
    return post_cost_layer(
        company=company,
        material=material,
        date=date,
        quantity=quantity,
        unit_cost=uc,
        layer_type=CostLayerType.ISSUE,
        reference_type=reference_type,
        reference_id=reference_id,
        actor=actor,
    )
