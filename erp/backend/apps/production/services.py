"""Production use-cases: lifecycle transitions and execution postings."""

from __future__ import annotations

from typing import Iterable, Optional

from django.db import models

from apps.core.events import EntityCreated, EntityUpdated
from apps.core.exceptions import ConflictError
from apps.core.transactions import atomic_with_events
from apps.inventory import services as inventory_services
from apps.inventory.models import StockMovementDirection
from apps.production.models import ProductionOrderStatus


def _actor_id(actor) -> Optional[str]:
    pk = getattr(actor, "pk", None)
    return str(pk) if pk else None


def _assert_declared_status(document: models.Model, to_status: str) -> None:
    declared = {value for value, _label in document._meta.get_field("status").choices}
    if to_status not in declared:
        raise ConflictError(
            f"'{to_status}' is not a valid status for this production order.",
            code="invalid_status_transition",
        )


def assert_document_editable(document: models.Model) -> None:
    if not document.is_editable:
        raise ConflictError(
            "This production order is not in DRAFT and cannot be modified; use "
            "the appropriate status action instead.",
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
    _assert_declared_status(document, to_status)

    with atomic_with_events() as events:
        locked = type(document).objects.select_for_update().get(pk=document.pk)
        if locked.status not in set(allowed_from):
            raise ConflictError(
                f"Cannot move this production order from '{locked.status}' to '{to_status}'.",
                code="invalid_status_transition",
            )
        locked.status = to_status
        locked.updated_by = actor
        locked.save(update_fields=["status", "updated_by", "updated_at"])
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


def _assert_order_released(order) -> None:
    """Execution postings are only valid against RELEASED production orders."""
    if order.status != ProductionOrderStatus.RELEASED:
        raise ConflictError(
            "Execution postings require a RELEASED production order " f"(current: {order.status}).",
            code="production.order_not_released",
        )


def create_material_issue(serializer, *, actor=None):
    """Post one immutable issue and its append-only OUT movement atomically."""
    _assert_order_released(serializer.validated_data["production_order"])
    with atomic_with_events() as events:
        issue = serializer.save(created_by=actor, updated_by=actor)
        movement = inventory_services.post_movement(
            company=issue.production_order.company,
            warehouse=issue.warehouse,
            direction=StockMovementDirection.OUT,
            quantity=issue.quantity,
            uom=issue.uom,
            material=issue.material,
            traceability_unit=issue.traceability_unit,
            reference_type="production.MaterialIssue",
            reference_id=issue.id,
            notes=issue.operation_label,
            actor=actor,
        )
        company_id = str(issue.production_order.company_id)
        events.append(
            EntityCreated(
                entity_type="production.MaterialIssue",
                entity_id=str(issue.id),
                actor_id=_actor_id(actor),
                company_id=company_id,
                state={"method": issue.method, "quantity": str(issue.quantity)},
            )
        )
        events.append(
            EntityCreated(
                entity_type="inventory.StockMovement",
                entity_id=str(movement.id),
                actor_id=_actor_id(actor),
                company_id=company_id,
                state={"direction": movement.direction, "quantity": str(movement.quantity)},
            )
        )

        # Q-034: auto-post an ISSUE cost layer at the current weighted-average.
        _post_issue_cost_layer(
            company=issue.production_order.company,
            material=issue.material,
            date=issue.created_at.date() if issue.created_at else None,
            quantity=issue.quantity,
            reference_id=issue.id,
            actor=actor,
        )

    return issue


def _post_issue_cost_layer(*, company, material, date, quantity, reference_id=None, actor=None):
    """Post a costing ISSUE layer. Best-effort — costing failures never break the issue."""
    try:
        from apps.costing.integration import post_cost_on_issue

        post_cost_on_issue(
            company=company,
            material=material,
            date=date,
            quantity=quantity,
            reference_type="production.MaterialIssue",
            reference_id=reference_id,
            actor=actor,
        )
    except Exception:
        import logging

        logger = logging.getLogger("apps.production")
        logger.warning(
            "Cost layer posting skipped for material issue %s",
            reference_id,
            exc_info=True,
        )


def create_production_output(serializer, *, actor=None):
    """Post one immutable output and its append-only IN movement atomically."""
    _assert_order_released(serializer.validated_data["production_order"])
    with atomic_with_events() as events:
        output = serializer.save(created_by=actor, updated_by=actor)
        movement = inventory_services.post_movement(
            company=output.production_order.company,
            warehouse=output.warehouse,
            direction=StockMovementDirection.IN,
            quantity=output.quantity,
            uom=output.uom,
            material=None,
            traceability_unit=output.traceability_unit,
            reference_type="production.ProductionOutput",
            reference_id=output.id,
            notes=output.operation_label,
            actor=actor,
        )
        company_id = str(output.production_order.company_id)
        events.append(
            EntityCreated(
                entity_type="production.ProductionOutput",
                entity_id=str(output.id),
                actor_id=_actor_id(actor),
                company_id=company_id,
                state={"quantity": str(output.quantity)},
            )
        )
        events.append(
            EntityCreated(
                entity_type="inventory.StockMovement",
                entity_id=str(movement.id),
                actor_id=_actor_id(actor),
                company_id=company_id,
                state={"direction": movement.direction, "quantity": str(movement.quantity)},
            )
        )

        # Q-034: auto-post a PRODUCTION_OUTPUT cost layer so produced stock
        # enters the valuation ledger at its actual consumed-material cost.
        _post_output_cost_layer(output=output, actor=actor)

    return output


def _post_output_cost_layer(*, output, actor=None):
    """Post a costing PRODUCTION_OUTPUT layer. Best-effort — costing failures never break the output.

    The layer is keyed to the produced unit's catalog material (units that
    reference only a customer product have no material identity to value and
    are skipped). The layer adds the produced quantity and its value to the
    produced material's ledger so later consumption of that material removes
    value at the correct WA.

    Value = the portion of this order's material consumption (Σ ISSUE-layer
    totals of the order's material issues) not yet absorbed by earlier outputs
    of the same order — i.e. actual consumption cost since the last output
    confirmation. For the common single-output order the layer therefore
    carries the full consumed material cost; labor/machine conversion is
    intentionally absent until Q-031/Q-033 rates are confirmed, and later
    corrections arrive as ADJUSTMENT layers.
    """
    try:
        from decimal import Decimal

        from django.db.models import Sum

        from apps.costing.integration import post_cost_on_output
        from apps.costing.models import CostLayer, CostLayerType

        order = output.production_order
        unit = output.traceability_unit
        material = unit.material if unit is not None and unit.material_id else None
        if material is None:
            # Produced unit without a catalog material — nothing to key the
            # layer on (the IN movement is equally material-less).
            return

        issue_ids = list(order.material_issues.values_list("id", flat=True))
        consumed = CostLayer.objects.filter(
            company_id=order.company_id,
            layer_type=CostLayerType.ISSUE,
            reference_type="production.MaterialIssue",
            reference_id__in=issue_ids,
        ).aggregate(t=Sum("total_cost"))["t"] or Decimal("0")
        # Cost already capitalised by earlier outputs of the same order (the
        # current output's layer is not posted yet, so it is naturally absent).
        other_output_ids = list(order.outputs.exclude(pk=output.pk).values_list("id", flat=True))
        absorbed = CostLayer.objects.filter(
            company_id=order.company_id,
            layer_type=CostLayerType.PRODUCTION_OUTPUT,
            reference_type="production.ProductionOutput",
            reference_id__in=other_output_ids,
        ).aggregate(t=Sum("total_cost"))["t"] or Decimal("0")
        remaining = consumed - absorbed
        if remaining < 0:
            remaining = Decimal("0")
        qty = Decimal(str(output.quantity))
        if qty > 0 and remaining > 0:
            unit_cost = (remaining / qty).quantize(Decimal("0.000001"))
        else:
            unit_cost = Decimal("0")

        post_cost_on_output(
            company=order.company,
            material=material,
            date=output.created_at.date() if output.created_at else None,
            quantity=output.quantity,
            unit_cost=unit_cost,
            reference_type="production.ProductionOutput",
            reference_id=output.id,
            actor=actor,
        )
    except Exception:
        import logging

        logger = logging.getLogger("apps.production")
        logger.warning(
            "Cost layer posting skipped for production output %s",
            getattr(output, "id", None),
            exc_info=True,
        )
