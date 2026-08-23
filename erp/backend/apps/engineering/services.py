"""Product Engineering use-cases (transactions + events).

Only the MECHANICAL versioning lifecycle lives here — the parts that are
CONFIRMED by docs/architecture/versioning.md and skill 04:

* create a new DRAFT specification revision (monotonic ``revision_number``);
* activate a DRAFT revision, which supersedes the prior ACTIVE one and stamps
  effective dates;
* guard that only DRAFT revisions (and their child rows) may be mutated.

Deliberately NOT here (OPEN business decisions — do-not-build-yet):
* what change *triggers* a new revision, and who approves it (Q-024, #13/#7);
* the SKU-derivation / product-coding scheme (Q-019 / NQ-005, #14);
* tooling cost model and sampling-mandatory rules (#5, #15).
"""

from __future__ import annotations

from typing import Optional

from django.db.models import Max
from django.utils import timezone

from apps.core.events import EntityCreated, EntityUpdated
from apps.core.exceptions import ConflictError
from apps.core.transactions import atomic_with_events
from apps.core.versioning import RevisionStatus
from apps.engineering.models import (
    CustomerProduct,
    SpecificationRevision,
    ToolingAsset,
    ToolingStatus,
)


def _actor_id(actor) -> Optional[str]:
    pk = getattr(actor, "pk", None)
    return str(pk) if pk else None


def next_revision_number(root: CustomerProduct) -> int:
    current = SpecificationRevision.objects.filter(root=root).aggregate(m=Max("revision_number"))[
        "m"
    ]
    return (current or 0) + 1


def create_specification_draft(
    *, root: CustomerProduct, actor=None, **fields
) -> SpecificationRevision:
    """Create a new DRAFT specification revision for ``root``."""
    with atomic_with_events() as events:
        revision = SpecificationRevision.objects.create(
            root=root,
            revision_number=next_revision_number(root),
            status=RevisionStatus.DRAFT,
            created_by=actor,
            updated_by=actor,
            **fields,
        )
        events.append(
            EntityCreated(
                entity_type="engineering.SpecificationRevision",
                entity_id=str(revision.pk),
                actor_id=_actor_id(actor),
                company_id=str(root.company_id),
            )
        )
    return revision


def assert_revision_editable(revision: SpecificationRevision) -> None:
    """Reject mutation of a non-DRAFT revision (immutability rule)."""
    if not revision.is_editable:
        raise ConflictError(
            "This specification revision is not in DRAFT and cannot be modified; "
            "create a new revision instead.",
            code="revision_not_editable",
        )


def activate_specification(
    revision: SpecificationRevision, *, actor=None, effective_from=None
) -> SpecificationRevision:
    """Activate a DRAFT revision; supersede the prior ACTIVE revision of the root.

    This is the mechanical version transition only — no approver/threshold policy
    is applied here (that is OPEN, Q-024). Access is gated by the
    ``engineering.specification.manage`` permission at the view.
    """
    if revision.status != RevisionStatus.DRAFT:
        raise ConflictError(
            "Only a DRAFT specification revision can be activated.",
            code="revision_not_draft",
        )

    now = timezone.now()
    effective_from = effective_from or now

    with atomic_with_events() as events:
        # Re-read under lock: two concurrent activations of the same DRAFT must
        # not both pass the DRAFT check (first committer wins, loser gets 409).
        locked = SpecificationRevision.objects.select_for_update().get(pk=revision.pk)
        if locked.status != RevisionStatus.DRAFT:
            raise ConflictError(
                "Only a DRAFT specification revision can be activated.",
                code="revision_not_draft",
            )
        revision = locked
        prior = (
            SpecificationRevision.objects.select_for_update()
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
                    entity_type="engineering.SpecificationRevision",
                    entity_id=str(old.pk),
                    actor_id=_actor_id(actor),
                    company_id=str(revision.root.company_id),
                    changes={"status": RevisionStatus.SUPERSEDED},
                )
            )

        revision.status = RevisionStatus.ACTIVE
        revision.effective_from = effective_from
        revision.updated_by = actor
        revision.save(update_fields=["status", "effective_from", "updated_by", "updated_at"])
        events.append(
            EntityUpdated(
                entity_type="engineering.SpecificationRevision",
                entity_id=str(revision.pk),
                actor_id=_actor_id(actor),
                company_id=str(revision.root.company_id),
                changes={"status": RevisionStatus.ACTIVE},
            )
        )
    return revision


def _set_tooling_status(
    asset: ToolingAsset, *, to_status: str, allowed_from: str, actor=None
) -> ToolingAsset:
    """Guarded status change for a tooling asset (audited via EntityUpdated).

    Mirrors the mechanical lifecycle idiom used elsewhere: reject an illegal
    source status with a 409, otherwise flip the status inside a transaction and
    emit an ``EntityUpdated`` so the change is audited. No usage-life-exhaustion
    policy is applied here (that is OPEN, do-not-build-yet #5).
    """
    if asset.status != allowed_from:
        raise ConflictError(
            f"A tooling asset can only move to {to_status} from {allowed_from}.",
            code="invalid_status_transition",
        )
    with atomic_with_events() as events:
        asset.status = to_status
        asset.updated_by = actor
        asset.save(update_fields=["status", "updated_by", "updated_at"])
        events.append(
            EntityUpdated(
                entity_type="engineering.ToolingAsset",
                entity_id=str(asset.pk),
                actor_id=_actor_id(actor),
                company_id=str(asset.company_id),
                changes={"status": to_status},
            )
        )
    return asset


def retire_tooling(asset: ToolingAsset, *, actor=None) -> ToolingAsset:
    """Retire an ACTIVE tooling asset (e.g. worn out / no longer used)."""
    return _set_tooling_status(
        asset,
        to_status=ToolingStatus.RETIRED,
        allowed_from=ToolingStatus.ACTIVE,
        actor=actor,
    )


def reactivate_tooling(asset: ToolingAsset, *, actor=None) -> ToolingAsset:
    """Return a RETIRED tooling asset to service."""
    return _set_tooling_status(
        asset,
        to_status=ToolingStatus.ACTIVE,
        allowed_from=ToolingStatus.RETIRED,
        actor=actor,
    )
