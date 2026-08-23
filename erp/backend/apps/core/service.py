"""Generic master-data write use-cases.

Task 003 left trivial org scaffolding on a bare ``ModelViewSet`` (no audit).
Real master data (Task 004+) must never bypass the audit trail, so writes go
through these helpers: each runs in one ``atomic_with_events`` block and appends
the standard lifecycle event. The audit subscriber (``apps.audit.subscribers``)
turns those events into audit rows, so modules stay decoupled from audit.

Business *rules* still belong in each entity's ``clean()``/serializer; these
helpers only own the transaction + event boundary shared by every entity.
"""

from __future__ import annotations

from typing import Any, Optional

from apps.core.events import EntityCreated, EntityDeleted, EntityUpdated
from apps.core.transactions import atomic_with_events


def entity_label(instance) -> str:
    """Dotted label used for events/audit, e.g. ``partners.Partner``."""
    return f"{instance._meta.app_label}.{instance.__class__.__name__}"


def _actor_id(actor) -> Optional[str]:
    pk = getattr(actor, "pk", None)
    return str(pk) if pk else None


def _company_id(instance) -> Optional[str]:
    """Extract the owning company id from a model instance, if any."""
    cid = getattr(instance, "company_id", None)
    return str(cid) if cid else None


def _json_safe_changes(data: dict[str, Any]) -> dict[str, Any]:
    """Best-effort JSON-safe snapshot of changed fields for the audit trail."""
    safe: dict[str, Any] = {}
    for key, value in (data or {}).items():
        if isinstance(value, (str, int, float, bool, type(None))):
            safe[key] = value
        else:
            safe[key] = str(value)
    return safe


def _snapshot(instance) -> dict[str, Any]:
    """Best-effort JSON-safe field snapshot for the audit trail.

    ``model_to_dict`` covers editable fields only (the pk and auto columns are
    already carried by ``entity_id``/timestamps elsewhere), so this is a
    human-readable view of the record, not a full table dump.
    """
    from django.forms.models import model_to_dict

    try:
        return _json_safe_changes(model_to_dict(instance))
    except Exception:  # snapshotting must never break the write it audits
        return {}


def create_from_serializer(serializer, *, actor=None):
    """Persist a new entity from a validated serializer and emit ``EntityCreated``."""
    with atomic_with_events() as events:
        instance = serializer.save(created_by=actor, updated_by=actor)
        events.append(
            EntityCreated(
                entity_type=entity_label(instance),
                entity_id=str(instance.pk),
                actor_id=_actor_id(actor),
                company_id=_company_id(instance),
                state=_snapshot(instance),
            )
        )
    return instance


def update_from_serializer(serializer, *, actor=None):
    """Persist changes from a validated serializer and emit ``EntityUpdated``."""
    changes = _json_safe_changes(dict(getattr(serializer, "validated_data", {}) or {}))
    with atomic_with_events() as events:
        before = _snapshot(getattr(serializer, "instance"))
        instance = serializer.save(updated_by=actor)
        events.append(
            EntityUpdated(
                entity_type=entity_label(instance),
                entity_id=str(instance.pk),
                actor_id=_actor_id(actor),
                company_id=_company_id(instance),
                changes=changes,
                before_state=before,
                after_state=_snapshot(instance),
            )
        )
    return instance


def delete_instance(instance, *, actor=None):
    """Delete (soft where supported) and emit ``EntityDeleted``."""
    label = entity_label(instance)
    pk = str(instance.pk)
    with atomic_with_events() as events:
        state = _snapshot(instance)
        instance.delete()
        events.append(
            EntityDeleted(
                entity_type=label,
                entity_id=pk,
                actor_id=_actor_id(actor),
                company_id=_company_id(instance),
                state=state,
            )
        )
    return instance
