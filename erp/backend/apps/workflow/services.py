"""Workflow service functions — the only sanctioned way to mutate state.

Each transition is atomic, writes an audit entry, publishes a domain event and
notifies the relevant users. State machine is deliberately small and explicit.
"""

from __future__ import annotations

from typing import List

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit
from apps.core.events import EntityApproved, EntityRejected, bus
from apps.core.exceptions import BusinessRuleError
from apps.notifications.models import NotificationType
from apps.notifications.services import notify
from apps.workflow.models import (
    ApprovalMode,
    ApprovalStep,
    StepDecision,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowState,
)


@transaction.atomic
def start_workflow(
    *,
    definition: WorkflowDefinition,
    entity_type: str,
    entity_id: str,
    approvers: List,
    actor=None,
) -> WorkflowInstance:
    if not approvers:
        raise BusinessRuleError("At least one approver is required.")
    instance = WorkflowInstance.objects.create(
        definition=definition,
        entity_type=entity_type,
        entity_id=str(entity_id),
        state=WorkflowState.SUBMITTED,
        created_by=actor,
    )
    for index, approver in enumerate(approvers, start=1):
        ApprovalStep.objects.create(
            instance=instance, sequence=index, approver=approver, created_by=actor
        )
    instance.state = WorkflowState.UNDER_REVIEW
    instance.save(update_fields=["state", "updated_at"])
    _notify_pending(instance)
    record_audit(
        action="CREATE",
        entity_type="workflow.WorkflowInstance",
        entity_id=str(instance.pk),
        actor=actor,
        metadata={"target": f"{entity_type}#{entity_id}"},
    )
    return instance


def _active_steps(instance: WorkflowInstance):
    return instance.steps.filter(decision=StepDecision.PENDING).order_by("sequence")


def _notify_pending(instance: WorkflowInstance) -> None:
    mode = instance.definition.approval_mode
    pending = _active_steps(instance)
    targets = pending if mode == ApprovalMode.PARALLEL else pending[:1]
    for step in targets:
        notify(
            recipient=step.approver,
            type=NotificationType.APPROVAL_REQUIRED,
            title="Approval required",
            body=f"Your approval is requested for {instance.entity_type}#{instance.entity_id}.",
            entity_type=instance.entity_type,
            entity_id=instance.entity_id,
        )


@transaction.atomic
def record_decision(
    *,
    instance: WorkflowInstance,
    approver,
    approve: bool,
    comment: str = "",
) -> WorkflowInstance:
    # Re-read under lock: two concurrent decisions (or a decision racing a
    # cancel) must not both pass the state/pending checks and double-finalize
    # the instance (which would publish the approval event twice and write two
    # audit rows). First committer wins; the loser gets a clean 409-style error.
    instance = WorkflowInstance.objects.select_for_update().get(pk=instance.pk)
    if instance.state not in (WorkflowState.UNDER_REVIEW, WorkflowState.SUBMITTED):
        raise BusinessRuleError("Workflow is not open for decisions.")

    step = (
        instance.steps.filter(approver=approver, decision=StepDecision.PENDING)
        .order_by("sequence")
        .first()
    )
    if step is None:
        raise BusinessRuleError("No pending approval step for this user.")

    # Sequential mode: only the earliest pending step may act.
    if instance.definition.approval_mode == ApprovalMode.SEQUENTIAL:
        earliest = _active_steps(instance).first()
        if earliest and earliest.pk != step.pk:
            raise BusinessRuleError("An earlier approver must act first.")

    step.decision = StepDecision.APPROVED if approve else StepDecision.REJECTED
    step.comment = comment
    step.decided_at = timezone.now()
    step.save(update_fields=["decision", "comment", "decided_at", "updated_at"])

    if not approve:
        _finalize(instance, WorkflowState.REJECTED, approver, comment)
        return instance

    if not _active_steps(instance).exists():
        _finalize(instance, WorkflowState.APPROVED, approver, comment)
    else:
        _notify_pending(instance)
    return instance


@transaction.atomic
def cancel_workflow(
    *, instance: WorkflowInstance, actor=None, reason: str = ""
) -> WorkflowInstance:
    # Lock + re-check: a cancel racing a final approval must not both succeed
    # (only one final state transition per instance).
    instance = WorkflowInstance.objects.select_for_update().get(pk=instance.pk)
    if instance.state in (WorkflowState.APPROVED, WorkflowState.REJECTED, WorkflowState.CANCELLED):
        raise BusinessRuleError("Workflow already finalized.")
    _finalize(instance, WorkflowState.CANCELLED, actor, reason)
    return instance


def _finalize(instance: WorkflowInstance, state: str, actor, comment: str) -> None:
    instance.state = state
    instance.save(update_fields=["state", "updated_at"])
    action = {
        WorkflowState.APPROVED: "APPROVE",
        WorkflowState.REJECTED: "REJECT",
        WorkflowState.CANCELLED: "CANCEL",
    }[state]
    record_audit(
        action=action,
        entity_type="workflow.WorkflowInstance",
        entity_id=str(instance.pk),
        actor=actor,
        metadata={"comment": comment},
    )
    if state == WorkflowState.APPROVED:
        bus.publish(EntityApproved(entity_type=instance.entity_type, entity_id=instance.entity_id))
    elif state == WorkflowState.REJECTED:
        bus.publish(
            EntityRejected(
                entity_type=instance.entity_type, entity_id=instance.entity_id, reason=comment
            )
        )
    if instance.created_by_id and state in (WorkflowState.APPROVED, WorkflowState.REJECTED):
        notify(
            recipient=instance.created_by,
            type=NotificationType.APPROVAL_COMPLETED,
            title=f"Request {state.lower()}",
            body=f"{instance.entity_type}#{instance.entity_id} was {state.lower()}.",
            entity_type=instance.entity_type,
            entity_id=instance.entity_id,
        )
