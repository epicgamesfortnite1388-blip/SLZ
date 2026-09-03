"""Recall service — bounded traceability exposure + audited status transitions.

Exposure computation NEVER mutates inventory or shipments: it reads the
append-only genealogy ledger (``inventory.GenealogyLink``) and shipment lines to
answer "what raw lots fed this unit, what finished units came from it, and
which shipments/customers received them". Traversal is bounded and cycle-safe so
malformed historical data cannot hang the query.

Status transitions follow the project's locking idiom: re-read the recall under
``select_for_update`` and re-check state so a CLOSE racing a CANCEL (or two
duplicate transitions) cannot double-finalize.
"""

from __future__ import annotations

from typing import Iterable, Set

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit
from apps.core.events import EntityUpdated, bus
from apps.core.exceptions import BusinessRuleError
from apps.recall.models import Recall, RecallStatus

# Bounded traversal: at most this many genealogy hops in either direction, and a
# hard cap on collected ids so a corrupted huge cluster cannot blow up memory.
_MAX_HOPS = 30
_MAX_IDS = 5000


def _bounded_traverse(*, start_ids: Iterable, direction: str) -> Set:
    """Walk the genealogy graph from ``start_ids`` in one direction.

    ``direction="up"`` follows ``child -> parent`` (raw materials consumed into
    the seed). ``direction="down"`` follows ``parent -> child`` (finished units
    made from the seed). Each hop is a single bulk query; visited ids and a hop
    budget prevent cycles/runaway graphs.
    """
    from apps.inventory.models import GenealogyLink

    start = set(start_ids)
    frontier = set(start)
    visited: Set = set()
    for _ in range(_MAX_HOPS):
        if not frontier or len(visited) >= _MAX_IDS:
            break
        if direction == "up":
            rows = GenealogyLink.objects.filter(child_id__in=frontier).values_list(
                "parent_id", flat=True
            )
        else:
            rows = GenealogyLink.objects.filter(parent_id__in=frontier).values_list(
                "child_id", flat=True
            )
        nxt = set(rows)
        nxt.discard(None)
        new_ids = nxt - visited - start
        if not new_ids:
            break
        visited |= new_ids
        frontier = new_ids
    return visited


def compute_exposure(recall: Recall) -> dict:
    """Compute recall exposure without mutating anything.

    Returns a serializable structure grouping the affected units (seeds +
    upstream raw lots + downstream finished units), the production orders that
    created affected units, and the shipments/customers that received affected
    finished units. All lookups are scoped to the recall's company.
    """
    from apps.inventory.models import TraceabilityUnit
    from apps.shipment.models import Shipment, ShipmentLine

    seed_ids = set(recall.affected_units.values_list("traceability_unit_id", flat=True))
    upstream_ids = _bounded_traverse(start_ids=seed_ids, direction="up")
    downstream_ids = _bounded_traverse(start_ids=seed_ids, direction="down")

    affected_unit_ids = seed_ids | upstream_ids | downstream_ids

    units = list(
        TraceabilityUnit.objects.filter(id__in=affected_unit_ids, company=recall.company).values(
            "id", "identifier", "unit_type", "material_id", "customer_product_id"
        )
    )

    # Production orders that created any affected finished unit (genealogy links
    # carry the producing order id; production outputs are the authoritative
    # record of "this order produced this unit").
    from apps.production.models import ProductionOrder, ProductionOutput

    produced_ids = set(seed_ids) | downstream_ids
    output_order_ids = set(
        ProductionOutput.objects.filter(
            traceability_unit_id__in=produced_ids,
            production_order__company=recall.company,
        ).values_list("production_order_id", flat=True)
    )
    production_orders = list(
        ProductionOrder.objects.filter(id__in=output_order_ids, company=recall.company).values(
            "id", "number", "status"
        )
    )

    # Shipments / customers that received an affected finished unit.
    shipped_lines = ShipmentLine.objects.filter(
        traceability_unit_id__in=produced_ids,
        shipment__company=recall.company,
    ).select_related("shipment__customer__partner")

    shipment_ids = {sl.shipment_id for sl in shipped_lines}
    shipments = list(
        Shipment.objects.filter(id__in=shipment_ids, company=recall.company).values(
            "id", "number", "shipped_at", "customer_id"
        )
    )
    customers = []
    seen_customers = set()
    for sl in shipped_lines:
        customer = sl.shipment.customer
        if customer.id in seen_customers:
            continue
        seen_customers.add(customer.id)
        customers.append(
            {
                "id": str(customer.id),
                "name_fa": customer.partner.name_fa,
                "name_en": customer.partner.name_en,
                "code": customer.partner.code,
            }
        )

    return {
        "seed_units": len(seed_ids),
        "upstream_units": len(upstream_ids),
        "downstream_units": len(downstream_ids),
        "affected_units": units,
        "production_orders": production_orders,
        "shipments": shipments,
        "customers": customers,
    }


# Explicit, auditable state machine (mirrors the workflow module's philosophy).
_ALLOWED = {
    RecallStatus.DRAFT: {RecallStatus.OPEN, RecallStatus.CANCELLED},
    RecallStatus.OPEN: {
        RecallStatus.INVESTIGATING,
        RecallStatus.ACTION_REQUIRED,
        RecallStatus.CLOSED,
        RecallStatus.CANCELLED,
    },
    RecallStatus.INVESTIGATING: {
        RecallStatus.ACTION_REQUIRED,
        RecallStatus.OPEN,
        RecallStatus.CLOSED,
    },
    RecallStatus.ACTION_REQUIRED: {
        RecallStatus.CLOSED,
        RecallStatus.INVESTIGATING,
        RecallStatus.OPEN,
    },
    RecallStatus.CLOSED: set(),
    RecallStatus.CANCELLED: set(),
}


@transaction.atomic
def transition(*, recall: Recall, to_status: str, actor=None) -> Recall:
    """Move a recall to ``to_status`` atomically, with lock + re-check.

    Terminal states (CLOSED/CANCELLED) are final: a CLOSE racing a CANCEL has
    exactly one winner; the loser receives a clean business error.
    """
    # Re-read under lock before mutating shared state.
    recall = Recall.objects.select_for_update().get(pk=recall.pk)
    allowed = _ALLOWED.get(recall.status, set())
    from_status = recall.status
    if to_status not in allowed:
        if recall.is_terminal:
            raise BusinessRuleError(
                f"Recall is already {recall.status.lower()}; it cannot be reopened.",
                code="recall_terminal",
            )
        raise BusinessRuleError(
            f"Transition {recall.status} -> {to_status} is not allowed.",
            code="recall_invalid_transition",
        )

    if from_status == RecallStatus.DRAFT and to_status == RecallStatus.OPEN:
        recall.initiated_at = timezone.now()
        recall.initiated_by = actor
    recall.status = to_status
    recall.save(update_fields=["status", "initiated_at", "initiated_by", "updated_at"])

    record_audit(
        action="RECALL_TRANSITION",
        entity_type="recall.Recall",
        entity_id=str(recall.pk),
        actor=actor,
        company_id=str(recall.company_id),
        metadata={"from": from_status, "to": to_status},
    )
    bus.publish(
        EntityUpdated(
            entity_type="recall.Recall",
            entity_id=str(recall.pk),
            changes={"status": to_status},
        )
    )
    return recall
