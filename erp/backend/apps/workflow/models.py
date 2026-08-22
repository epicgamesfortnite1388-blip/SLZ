"""Workflow models.

Intentionally small: a definition describes the approval shape (sequential or
parallel, and the ordered approvers), an instance tracks one entity through the
standard state set, and steps capture each approver's decision with a comment
and timestamp for audit. Business-specific routing rules are configuration, not
code.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class WorkflowState(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    UNDER_REVIEW = "UNDER_REVIEW", "Under review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"


class ApprovalMode(models.TextChoices):
    SEQUENTIAL = "SEQUENTIAL", "Sequential"
    PARALLEL = "PARALLEL", "Parallel"


class StepDecision(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class WorkflowDefinition(BaseModel):
    code = models.CharField(max_length=100, unique=True)
    name_en = models.CharField(max_length=200)
    name_fa = models.CharField(max_length=200)
    approval_mode = models.CharField(
        max_length=16, choices=ApprovalMode.choices, default=ApprovalMode.SEQUENTIAL
    )
    # Free-form configuration (e.g. threshold rules) — interpreted by callers,
    # never hard-coded here.
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "workflow_definition"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class WorkflowInstance(BaseModel):
    definition = models.ForeignKey(
        WorkflowDefinition, on_delete=models.PROTECT, related_name="instances"
    )
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=64, db_index=True)
    state = models.CharField(
        max_length=16,
        choices=WorkflowState.choices,
        default=WorkflowState.DRAFT,
        db_index=True,
    )

    class Meta:
        db_table = "workflow_instance"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["entity_type", "entity_id"])]

    def __str__(self) -> str:
        return f"{self.definition.code}:{self.entity_type}#{self.entity_id} [{self.state}]"


class ApprovalStep(BaseModel):
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name="steps")
    sequence = models.PositiveIntegerField()
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approval_steps"
    )
    decision = models.CharField(
        max_length=16, choices=StepDecision.choices, default=StepDecision.PENDING
    )
    comment = models.TextField(blank=True, default="")
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "workflow_approval_step"
        ordering = ["instance", "sequence"]
        unique_together = ("instance", "sequence")

    def __str__(self) -> str:
        return f"step {self.sequence} [{self.decision}]"
