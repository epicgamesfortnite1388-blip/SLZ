"""Bridge domain events onto the audit trail.

Subscribing here keeps modules decoupled: a module publishes an ``EntityCreated``
event and the audit trail records it, without the module importing audit.
"""

from __future__ import annotations

from apps.audit.services import record_audit
from apps.core import events


def _handle_created(event: events.EntityCreated) -> None:
    record_audit(
        action="CREATE",
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        actor_id=event.actor_id,
        company_id=event.company_id,
        after_state=event.state,
        metadata=event.metadata,
        correlation_id=event.correlation_id,
    )


def _handle_updated(event: events.EntityUpdated) -> None:
    record_audit(
        action="UPDATE",
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        actor_id=event.actor_id,
        company_id=event.company_id,
        before_state=event.before_state,
        after_state=(
            event.after_state if event.after_state is not None else getattr(event, "changes", None)
        ),
        metadata=event.metadata,
        correlation_id=event.correlation_id,
    )


def _handle_deleted(event: events.EntityDeleted) -> None:
    record_audit(
        action="DELETE",
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        actor_id=event.actor_id,
        company_id=event.company_id,
        before_state=event.state,
        metadata=event.metadata,
        correlation_id=event.correlation_id,
    )


def register() -> None:
    events.bus.subscribe(events.EntityCreated, _handle_created)
    events.bus.subscribe(events.EntityUpdated, _handle_updated)
    events.bus.subscribe(events.EntityDeleted, _handle_deleted)


register()
