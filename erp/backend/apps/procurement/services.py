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

from typing import Iterable, Optional

from django.db import models

from apps.core.events import EntityUpdated
from apps.core.exceptions import ConflictError
from apps.core.transactions import atomic_with_events


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
                changes={"status": to_status},
            )
        )
    return document
