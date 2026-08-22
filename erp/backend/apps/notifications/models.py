"""Notification model and event-type taxonomy."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class NotificationType(models.TextChoices):
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED", "Approval required"
    APPROVAL_COMPLETED = "APPROVAL_COMPLETED", "Approval completed"
    TASK_ASSIGNED = "TASK_ASSIGNED", "Task assigned"
    STATUS_CHANGED = "STATUS_CHANGED", "Status changed"
    DEADLINE_APPROACHING = "DEADLINE_APPROACHING", "Deadline approaching"
    SYSTEM_ALERT = "SYSTEM_ALERT", "System alert"


class Notification(BaseModel):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=32, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default="")
    # Optional deep link to the entity that triggered the notification.
    entity_type = models.CharField(max_length=100, blank=True, default="")
    entity_id = models.CharField(max_length=64, blank=True, default="")
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications_notification"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read"])]

    def __str__(self) -> str:
        return f"{self.type} -> {self.recipient_id}"
