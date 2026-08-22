"""Audit recording service — the single entry point for writing audit rows."""

from __future__ import annotations

from typing import Any, Optional

from apps.audit.models import AuditLog
from apps.core.middleware import get_correlation_id


def record_audit(
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    actor=None,
    actor_id: Optional[str] = None,
    before_state: Optional[dict] = None,
    after_state: Optional[dict] = None,
    metadata: Optional[dict] = None,
    correlation_id: Optional[str] = None,
) -> AuditLog:
    """Persist a single audit entry.

    ``correlation_id`` defaults to the current request's id so a full request
    can be reconstructed across modules.

    Callers may pass either an ``actor`` **instance** (direct service writes) or
    an ``actor_id`` (the event path — domain events carry only the id to stay
    decoupled from the user model). When only ``actor_id`` is given, the user is
    resolved here so ``AuditLog.actor``/``actor_label`` are populated on the
    event path too. An unresolvable id degrades gracefully to an anonymous row.
    """
    if actor is None and actor_id:
        actor = _resolve_actor(actor_id)

    actor_label = ""
    if actor is not None and getattr(actor, "pk", None):
        actor_label = getattr(actor, "email", None) or str(actor)

    return AuditLog.objects.create(
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        actor=actor if getattr(actor, "pk", None) else None,
        actor_label=actor_label,
        before_state=before_state,
        after_state=after_state,
        metadata=metadata or {},
        correlation_id=correlation_id or get_correlation_id() or "",
    )


def _resolve_actor(actor_id: str):
    """Best-effort lookup of the acting user by id.

    Returns ``None`` if the id is malformed or the user no longer exists, so a
    stale/invalid actor never blocks an audit write.
    """
    from django.contrib.auth import get_user_model
    from django.core.exceptions import ValidationError

    User = get_user_model()
    try:
        return User.objects.filter(pk=actor_id).first()
    except (ValueError, TypeError, ValidationError):
        return None


def serialize_instance(instance, fields: Optional[list[str]] = None) -> dict[str, Any]:
    """Best-effort JSON-safe snapshot of a model instance for before/after state."""
    from django.forms.models import model_to_dict

    data = model_to_dict(instance, fields=fields)
    return {k: (str(v) if not _json_safe(v) else v) for k, v in data.items()}


def _json_safe(value) -> bool:
    return isinstance(value, (str, int, float, bool, type(None), list, dict))
