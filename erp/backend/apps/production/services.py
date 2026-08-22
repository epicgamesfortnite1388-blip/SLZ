"""Production use-cases: lifecycle transitions and execution postings."""

from __future__ import annotations

from typing import Iterable, Optional

from django.db import models

from apps.core.events import EntityCreated, EntityUpdated
from apps.core.exceptions import ConflictError
from apps.core.transactions import atomic_with_events
from apps.inventory.models import StockMovement, StockMovementDirection


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
                changes={"status": to_status},
            )
        )
    return document


def create_material_issue(serializer, *, actor=None):
    """Post one immutable issue and its append-only OUT movement atomically."""
    with atomic_with_events() as events:
        issue = serializer.save(created_by=actor, updated_by=actor)
        movement = StockMovement.objects.create(
            company=issue.production_order.company,
            warehouse=issue.warehouse,
            traceability_unit=issue.traceability_unit,
            material=issue.material,
            direction=StockMovementDirection.OUT,
            quantity=issue.quantity,
            uom=issue.uom,
            reference_type="production.MaterialIssue",
            reference_id=issue.id,
            notes=issue.operation_label,
            created_by=actor,
            updated_by=actor,
        )
        events.append(
            EntityCreated(
                entity_type="production.MaterialIssue",
                entity_id=str(issue.id),
                actor_id=_actor_id(actor),
                state={"method": issue.method, "quantity": str(issue.quantity)},
            )
        )
        events.append(
            EntityCreated(
                entity_type="inventory.StockMovement",
                entity_id=str(movement.id),
                actor_id=_actor_id(actor),
                state={"direction": movement.direction, "quantity": str(movement.quantity)},
            )
        )
    return issue


def create_production_output(serializer, *, actor=None):
    """Post one immutable output and its append-only IN movement atomically."""
    with atomic_with_events() as events:
        output = serializer.save(created_by=actor, updated_by=actor)
        movement = StockMovement.objects.create(
            company=output.production_order.company,
            warehouse=output.warehouse,
            traceability_unit=output.traceability_unit,
            direction=StockMovementDirection.IN,
            quantity=output.quantity,
            uom=output.uom,
            reference_type="production.ProductionOutput",
            reference_id=output.id,
            notes=output.operation_label,
            created_by=actor,
            updated_by=actor,
        )
        events.append(
            EntityCreated(
                entity_type="production.ProductionOutput",
                entity_id=str(output.id),
                actor_id=_actor_id(actor),
                state={"quantity": str(output.quantity)},
            )
        )
        events.append(
            EntityCreated(
                entity_type="inventory.StockMovement",
                entity_id=str(movement.id),
                actor_id=_actor_id(actor),
                state={"direction": movement.direction, "quantity": str(movement.quantity)},
            )
        )
    return output
