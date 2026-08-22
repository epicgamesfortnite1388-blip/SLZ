"""Quality use-cases (transactions + events) — Task 008.

The ONLY business logic here is the MECHANICAL versioning lifecycle of the
Quality Plan, mirroring ``apps.manufacturing.services`` /
``apps.engineering.services`` (versioning.md, skill 06):

* create a new DRAFT revision (monotonic ``revision_number`` per root);
* activate a DRAFT revision, superseding the prior ACTIVE one and stamping
  effective dates;
* guard that only DRAFT revisions (and their child items) may be mutated.

``QualityPlanRevision`` is a ``core.versioning`` ``Revision`` subclass, so this
generic implementation is identical in shape to the manufacturing lifecycle —
kept per-module for consistency with the established architecture.

Deliberately NOT here (OPEN business decisions — do-not-build-yet):
* quality CHECK execution & results (measured values / PASS-FAIL) — needs the
  gated traceability + stock layer (Q-046, #18);
* NCR / QC_HOLD / disposition, scrap & rework reason codes (Q-041/043/016·042,
  #12), COA (Q-045), recall / CAPA (Q-044, #31);
* approver/threshold policy for plan activation (OPEN) — activation is gated by
  the ``quality.plan.manage`` permission only.
"""

from __future__ import annotations

from typing import Optional

from django.db import models
from django.db.models import Max
from django.utils import timezone

from apps.core.events import EntityCreated, EntityUpdated
from apps.core.exceptions import ConflictError
from apps.core.transactions import atomic_with_events
from apps.core.versioning import Revision, RevisionStatus


def _actor_id(actor) -> Optional[str]:
    pk = getattr(actor, "pk", None)
    return str(pk) if pk else None


def next_revision_number(revision_model: type[Revision], root: models.Model) -> int:
    current = revision_model.objects.filter(root=root).aggregate(m=Max("revision_number"))["m"]
    return (current or 0) + 1


def create_revision_draft(
    *,
    revision_model: type[Revision],
    entity_type: str,
    root: models.Model,
    actor=None,
    **fields,
) -> Revision:
    """Create a new DRAFT revision of ``root`` for the given revision model."""
    with atomic_with_events() as events:
        revision = revision_model.objects.create(
            root=root,
            revision_number=next_revision_number(revision_model, root),
            status=RevisionStatus.DRAFT,
            created_by=actor,
            updated_by=actor,
            **fields,
        )
        events.append(
            EntityCreated(
                entity_type=entity_type,
                entity_id=str(revision.pk),
                actor_id=_actor_id(actor),
            )
        )
    return revision


def assert_revision_editable(revision: Revision) -> None:
    """Reject mutation of a non-DRAFT revision (immutability rule)."""
    if not revision.is_editable:
        raise ConflictError(
            "This revision is not in DRAFT and cannot be modified; create a new "
            "revision instead.",
            code="revision_not_editable",
        )


def activate_revision(
    *,
    revision: Revision,
    entity_type: str,
    actor=None,
    effective_from=None,
) -> Revision:
    """Activate a DRAFT revision; supersede the prior ACTIVE revision of its root.

    Mechanical version transition only — no approver/threshold policy (OPEN).
    Access is gated by the ``quality.plan.manage`` permission at the view. Emits
    ``EntityUpdated`` (NOT ``EntityApproved``) so the audit subscriber records
    the state change.
    """
    if revision.status != RevisionStatus.DRAFT:
        raise ConflictError(
            "Only a DRAFT revision can be activated.",
            code="revision_not_draft",
        )

    now = timezone.now()
    effective_from = effective_from or now
    model = type(revision)

    with atomic_with_events() as events:
        # Re-read under lock: two concurrent activations of the same DRAFT must
        # not both pass the DRAFT check (first committer wins, loser gets 409).
        locked = model.objects.select_for_update().get(pk=revision.pk)
        if locked.status != RevisionStatus.DRAFT:
            raise ConflictError(
                "Only a DRAFT revision can be activated.",
                code="revision_not_draft",
            )
        revision = locked
        prior = (
            model.objects.select_for_update()
            .filter(root=revision.root, status=RevisionStatus.ACTIVE)
            .exclude(pk=revision.pk)
        )
        for old in prior:
            old.status = RevisionStatus.SUPERSEDED
            old.effective_to = now
            old.updated_by = actor
            old.save(update_fields=["status", "effective_to", "updated_by", "updated_at"])
            events.append(
                EntityUpdated(
                    entity_type=entity_type,
                    entity_id=str(old.pk),
                    actor_id=_actor_id(actor),
                    changes={"status": RevisionStatus.SUPERSEDED},
                )
            )

        revision.status = RevisionStatus.ACTIVE
        revision.effective_from = effective_from
        revision.updated_by = actor
        revision.save(update_fields=["status", "effective_from", "updated_by", "updated_at"])
        events.append(
            EntityUpdated(
                entity_type=entity_type,
                entity_id=str(revision.pk),
                actor_id=_actor_id(actor),
                changes={"status": RevisionStatus.ACTIVE},
            )
        )
    return revision


# ---------------------------------------------------------------------------
# QC execution results (append-only, per-roll/batch)
# ---------------------------------------------------------------------------


def post_check_result(
    *,
    plan_item,
    traceability_unit,
    measured_value: str,
    disposition: str,
    checked_at,
    checked_by=None,
    notes: str = "",
    actor=None,
):
    """Record one QC measurement for a traceability unit against a plan item.

    Guards:
    - Unit must belong to the same company as the plan item's product.
    - PASS/FAIL/HOLD disposition. HOLD tags the unit's notes for quarantine.
    Result rows are append-only.
    """
    from apps.quality.models import QualityCheckResult

    plan_company = plan_item.revision.root.spec_revision.root.company_id
    unit_company = traceability_unit.company_id
    if plan_company != unit_company:
        from apps.core.exceptions import BusinessRuleError

        raise BusinessRuleError(
            "Plan item and traceability unit must belong to the same company.",
            code="qc.cross_company",
        )

    result = QualityCheckResult.objects.create(
        plan_item=plan_item,
        traceability_unit=traceability_unit,
        measured_value=measured_value,
        disposition=disposition,
        checked_at=checked_at,
        checked_by=checked_by,
        notes=notes,
        created_by=actor,
        updated_by=actor,
    )

    if disposition == "HOLD":
        if not traceability_unit.notes:
            traceability_unit.notes = ""
        traceability_unit.notes = (
            traceability_unit.notes
            + f" [QC HOLD: {checked_at.isoformat()}]"
        ).strip()
        traceability_unit.save(update_fields=["notes", "updated_at"])

    return result
