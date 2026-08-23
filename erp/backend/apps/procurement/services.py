"""Procurement use-cases (document status transitions + events) — Task 009.

Purchase documents are transactional instances with a **status state machine**
(not the versioning lifecycle of BOM/Routing/Quality). The only business logic
here is the mechanical, guarded status transition, shared by both document
types via one generic helper:

* reject a transition whose source status is not allowed (409);
* reject a target status the model does not declare (409);
* re-check the source status on a locked row inside the transaction, so
  concurrent transitions of one document cannot both succeed (first wins, 409);
* apply the new status under ``atomic_with_events`` and emit ``EntityUpdated``
  (NOT ``EntityApproved`` — the audit subscriber ignores that) so the change is
  recorded in the audit trail;
* guard that only DRAFT documents (and their child lines) may be mutated.

Deliberately NOT here (OPEN business decisions — do-not-build-yet):
* approval hierarchy / monetary-threshold policy (#7, Q-054/056) — ``approve`` is
  a single manual transition gated by the ``*.manage`` permission at the view;
* goods receipt / GRN state transitions (SR-09, gated on Q-046, #17/#18);
* MRP-driven requisition generation, RFQ/sourcing, FX/valuation, invoicing.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Optional

from django.db import models, transaction

from apps.core.events import EntityCreated, EntityUpdated
from apps.core.exceptions import BusinessRuleError, ConflictError
from apps.core.transactions import atomic_with_events
from apps.inventory import services as inventory_services
from apps.inventory.models import (
    StockMovementDirection,
    TraceabilityUnit,
    TraceabilityUnitType,
    WarehouseStoreType,
)
from apps.procurement.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    GoodsReceiptStatus,
    PurchaseOrderStatus,
)


def _actor_id(actor) -> Optional[str]:
    pk = getattr(actor, "pk", None)
    return str(pk) if pk else None


def _assert_declared_status(document: models.Model, to_status: str) -> None:
    """Reject a target status that the model does not declare (defensive guard)."""
    declared = {value for value, _ in document._meta.get_field("status").choices}
    if to_status not in declared:
        raise ConflictError(
            f"'{to_status}' is not a valid status for this document.",
            code="invalid_status_transition",
        )


def assert_document_editable(document: models.Model) -> None:
    """Reject mutation of a non-DRAFT document (commitment immutability rule)."""
    if not document.is_editable:
        raise ConflictError(
            "This document is not in DRAFT and cannot be modified; use the "
            "appropriate status action instead.",
            code="document_not_editable",
        )


def transition(
    *,
    document: models.Model,
    entity_type: str,
    to_status: str,
    allowed_from: Iterable[str],
    actor=None,
) -> models.Model:
    """Apply a guarded status transition and emit an audited ``EntityUpdated``.

    The target status is validated against the model's declared ``status``
    choices, and the source-status check is re-evaluated on a freshly locked row
    (``select_for_update``) inside the transaction — so two concurrent
    transitions of the same document cannot both pass validation (first
    committer wins; the loser gets a 409 and nothing is persisted).

    Raises ``ConflictError(code="invalid_status_transition")`` if the document's
    current status is not in ``allowed_from``, or the target is not a declared
    status of the document model.
    """
    _assert_declared_status(document, to_status)

    with atomic_with_events() as events:
        locked = type(document).objects.select_for_update().get(pk=document.pk)
        if locked.status not in set(allowed_from):
            raise ConflictError(
                f"Cannot move this document from '{locked.status}' to '{to_status}'.",
                code="invalid_status_transition",
            )
        locked.status = to_status
        locked.updated_by = actor
        locked.save(update_fields=["status", "updated_by", "updated_at"])
        # Keep the caller's instance consistent with the committed row.
        document.status = to_status
        document.updated_by = actor
        events.append(
            EntityUpdated(
                entity_type=entity_type,
                entity_id=str(document.pk),
                actor_id=_actor_id(actor),
                company_id=(
                    str(document.company_id) if getattr(document, "company_id", None) else None
                ),
                changes={"status": to_status},
            )
        )
    return document


def _new_unit_identifier(company, unit_type: str) -> str:
    """Collision-proof identifier for a newly received unit."""
    import uuid as uuid_module

    prefix = unit_type.capitalize()
    while True:
        candidate = prefix + "-" + uuid_module.uuid4().hex[:10].upper()
        if not TraceabilityUnit.objects.filter(company=company, identifier=candidate).exists():
            return candidate


RECEIVABLE_PO_STATUSES = (
    PurchaseOrderStatus.APPROVED,
    PurchaseOrderStatus.SENT,
)


@transaction.atomic
def create_goods_receipt(serializer, *, actor=None):
    """Post one goods receipt atomically.

    Per line (Q-049): creates the traceability unit (serialized roll / batch /
    carton per material category) and an IN stock movement into the destination
    warehouse. Guards: PO must be APPROVED or SENT; line material must match
    the PO line; over-receipt is blocked; quarantine warehouses cannot receive.
    Every created row emits its own audit event via the standard bus.
    """
    from apps.core.exceptions import AuthorizationError

    payload = serializer.validated_data
    company = payload["company"]
    warehouse = payload["warehouse"]
    purchase_order = payload.get("purchase_order")
    lines = payload.get("lines") or []
    if not lines:
        raise BusinessRuleError("A goods receipt needs at least one line.", code="grn.empty")

    if warehouse.store_type == WarehouseStoreType.QUARANTINE:
        raise BusinessRuleError(
            "Goods receipts cannot post into a quarantine store.",
            code="grn.quarantine_destination",
        )
    if purchase_order is not None and purchase_order.company_id != company.id:
        raise AuthorizationError("The purchase order belongs to another company.")
    if purchase_order is not None and purchase_order.status not in RECEIVABLE_PO_STATUSES:
        raise ConflictError(
            "Only APPROVED or SENT purchase orders can be received.",
            code="grn.po_not_receivable",
        )

    with atomic_with_events() as events:
        grn = GoodsReceipt.objects.create(
            company=company,
            warehouse=warehouse,
            supplier=payload.get("supplier"),
            purchase_order=purchase_order,
            number=payload["number"],
            status=GoodsReceiptStatus.POSTED,
            received_at=payload["received_at"],
            notes=payload.get("notes", ""),
            created_by=actor,
            updated_by=actor,
        )
        events.append(
            EntityCreated(
                entity_type="procurement.GoodsReceipt",
                entity_id=str(grn.pk),
                actor_id=_actor_id(actor),
                company_id=str(company.id),
                state={"number": grn.number},
            )
        )

        for entry in lines:
            po_line = entry.get("po_line")
            if (
                po_line is not None
                and purchase_order is not None
                and po_line.order_id != purchase_order.id
            ):
                raise BusinessRuleError(
                    "The referenced PO line belongs to a different order.",
                    code="grn.line_order_mismatch",
                )
            if po_line is not None and po_line.material_id != entry["material"].id:
                raise BusinessRuleError(
                    "Line material does not match the PO line.",
                    code="grn.material_mismatch",
                )
            if po_line is not None:
                already = (
                    GoodsReceiptLine.objects.filter(po_line=po_line).aggregate(
                        total=models.Sum("quantity")
                    )["total"]
                    or 0
                )
                if Decimal(str(already)) + Decimal(str(entry["quantity"])) > po_line.quantity:
                    raise BusinessRuleError(
                        "Over-receipt blocked: ordered %s, already received %s."
                        % (po_line.quantity, already),
                        code="grn.over_receipt",
                    )

            unit_type = entry["traceability_unit_type"]
            if unit_type == TraceabilityUnitType.PALLET:
                raise BusinessRuleError(
                    "Pallets are handling units assembled from other units;",
                    code="grn.unit_type_invalid",
                )
            unit = TraceabilityUnit.objects.create(
                company=company,
                material=entry["material"],
                unit_type=unit_type,
                identifier=_new_unit_identifier(company, unit_type),
                quantity=entry["quantity"],
                uom=entry["uom"],
                created_by=actor,
                updated_by=actor,
            )
            line_row = GoodsReceiptLine.objects.create(
                grn=grn,
                po_line=po_line,
                material=entry["material"],
                quantity=entry["quantity"],
                uom=entry["uom"],
                traceability_unit=unit,
                created_by=actor,
                updated_by=actor,
            )
            movement = inventory_services.post_movement(
                company=company,
                warehouse=warehouse,
                direction=StockMovementDirection.IN,
                quantity=entry["quantity"],
                uom=entry["uom"],
                material=entry["material"],
                traceability_unit=unit,
                reference_type="procurement.GoodsReceiptLine",
                reference_id=line_row.id,
                notes="GRN " + grn.number,
                actor=actor,
            )
            events.append(
                EntityCreated(
                    entity_type="procurement.GoodsReceiptLine",
                    entity_id=str(line_row.id),
                    actor_id=_actor_id(actor),
                    company_id=str(company.id),
                    state={
                        "quantity": str(entry["quantity"]),
                        "movement_id": str(movement.id),
                    },
                )
            )

            # Q-034: auto-post a RECEIPT cost layer for dated weighted-average.
            _post_grn_cost_layer(
                company=company,
                material=entry["material"],
                date=payload["received_at"],
                quantity=entry["quantity"],
                unit_price=getattr(po_line, "unit_price", None) if po_line else None,
                po_line_id=str(po_line.id) if po_line else None,
                reference_id=line_row.id,
                actor=actor,
            )

    return grn


def _post_grn_cost_layer(
    *,
    company,
    material,
    date,
    quantity,
    unit_price=None,
    po_line_id=None,
    reference_id=None,
    actor=None,
):
    """Post a costing RECEIPT layer for one GRN line. Best-effort — costing failures never break the receipt."""
    try:
        from apps.costing.integration import post_cost_on_receipt

        post_cost_on_receipt(
            company=company,
            material=material,
            date=date,
            quantity=quantity,
            unit_price=unit_price,
            po_line_id=po_line_id,
            reference_type="procurement.GoodsReceiptLine",
            reference_id=reference_id,
            actor=actor,
        )
    except Exception:
        import logging

        logger = logging.getLogger("apps.procurement")
        logger.warning("Cost layer posting skipped for GRN line %s", reference_id, exc_info=True)
