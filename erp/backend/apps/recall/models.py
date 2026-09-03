"""Recall — quality-event workflow over traceability (Stage 3).

A ``Recall`` is a company-scoped quality event attached to one or more affected
traceability units (lots/rolls/batches). Creating a recall NEVER mutates
inventory or shipments automatically — exposure (affected production orders,
shipments, customers) is *computed on demand* from the genealogy/shipment
records via ``apps.recall.services``, so the recall itself stays a pure,
auditable record.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class RecallStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    OPEN = "OPEN", "Open"
    INVESTIGATING = "INVESTIGATING", "Investigating"
    ACTION_REQUIRED = "ACTION_REQUIRED", "Action required"
    CLOSED = "CLOSED", "Closed"
    CANCELLED = "CANCELLED", "Cancelled"


class RecallSeverity(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class Recall(BaseModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="recalls"
    )
    code = models.CharField(max_length=60)
    reason = models.TextField()
    severity = models.CharField(
        max_length=16, choices=RecallSeverity.choices, default=RecallSeverity.MEDIUM
    )
    status = models.CharField(
        max_length=16, choices=RecallStatus.choices, default=RecallStatus.DRAFT, db_index=True
    )
    initiated_at = models.DateTimeField(null=True, blank=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="initiated_recalls",
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "recall_recall"
        ordering = ["-initiated_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="uq_recall_company_code"),
        ]

    def __str__(self) -> str:
        return f"{self.code} [{self.status}]"

    @property
    def is_terminal(self) -> bool:
        return self.status in (RecallStatus.CLOSED, RecallStatus.CANCELLED)


class RecallAffectedUnit(BaseModel):
    """Explicitly-affected traceability unit on a recall (user-curated seeds)."""

    recall = models.ForeignKey(Recall, on_delete=models.CASCADE, related_name="affected_units")
    traceability_unit = models.ForeignKey(
        "inventory.TraceabilityUnit", on_delete=models.PROTECT, related_name="recall_links"
    )
    note = models.CharField(max_length=300, blank=True, default="")

    class Meta:
        db_table = "recall_affected_unit"
        constraints = [
            models.UniqueConstraint(
                fields=["recall", "traceability_unit"],
                name="uq_recall_affected_unit",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.recall_id} -> unit {self.traceability_unit_id}"
