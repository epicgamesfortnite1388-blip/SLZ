"""Append-only audit log.

Generic by design: it references entities by ``entity_type`` (a dotted label
like ``identity.User``) and ``entity_id`` (string form of the PK) rather than a
hard FK, so any module — present or future — can be audited without schema
changes. Rows are never updated or deleted through the ORM in normal operation.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class AuditAction(models.TextChoices):
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    DELETE = "DELETE", "Delete"
    APPROVE = "APPROVE", "Approve"
    REJECT = "REJECT", "Reject"
    CANCEL = "CANCEL", "Cancel"
    LOGIN = "LOGIN", "Login"
    LOGOUT = "LOGOUT", "Logout"


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
    )
    actor_label = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Denormalized actor identity, preserved even if the user is removed.",
    )
    company = models.ForeignKey(
        "organization.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
        help_text="Owning company for row-level isolation; NULL for platform events (login/logout).",
    )
    action = models.CharField(max_length=16, choices=AuditAction.choices, db_index=True)
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=64, db_index=True)
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    correlation_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["company", "timestamp"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.action} {self.entity_type}#{self.entity_id} @ {self.timestamp:%Y-%m-%d %H:%M}"
        )
