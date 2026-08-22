"""Production use-cases (document status transitions + events) — Task 011.

A Production Order is a transactional instance with a **status state machine**
(not the versioning lifecycle of BOM/Routing/Quality). The only business logic
here is the mechanical, guarded status transition:

* reject a transition whose source status is not allowed (409);
* reject a target status the model does not declare (409);
* re-check the source status on a locked row inside the transaction, so
  concurrent transitions of one order cannot both succeed (first wins, 409);
* apply the new status under ``atomic_with_events`` and emit ``EntityUpdated``
  (NOT ``EntityApproved`` — the audit subscriber ignores that) so the change is
  recorded in the audit trail;
* guard that only DRAFT orders may be mutated.

Deliberately NOT here (OPEN business decisions / gated — do-not-build-yet):
* material issue / consumption / backflush and roll-lot genealogy (SR-08, #19,
  gated on Q-046);
* operation confirmations, produced/scrap capture, downtime tables (SR-05/06);
* QC results + auto stop/rework (SR-06); margin priority (SR-13); outsourcing
  locus (SR-14/DR-043); ATP / capacity feasibility (SR-12/R-30). ``release`` is a
  single manual transition gated by the ``production.order.manage`` permission.
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
            f"'{to_status}' is not a valid status for this production order.",
            code="invalid_status_transition",
        )


def assert_document_editable(document: models.Model) -> None:
    """Reject mutation of a non-DRAFT order (commitment immutability rule)."""
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
    """Apply a guarded status transition and emit an audited ``EntityUpdated``.

    The target status is validated against the model's declared ``status``
    choices, and the source-status check is re-evaluated on a freshly locked row
    (``select_for_update``) inside the transaction — so two concurrent
    transitions of the same order cannot both pass validation (first committer
    wins; the loser gets a 409 and nothing is persisted).

    Raises ``ConflictError(code="invalid_status_transition")`` if the order's
    current status is not in ``allowed_from``, or the target is not a declared
    status of the order model.
    """
    _assert_declared_status(document, to_status)

    with atomic_with_events() as events:
        locked = type(document).objects.select_for_update().get(pk=document.pk)
        if locked.status not in set(allowed_from):
            raise ConflictError(
                f"Cannot move this production order from '{locked.status}' to " f"'{to_status}'.",
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
