"""Reusable abstract base models.

Design policy (see docs/architecture/data-lifecycle.md):
* Every persistent entity uses a UUID primary key (``UUIDModel``) so IDs are
  stable, non-guessable and safe to expose in URLs/APIs. Human-facing business
  numbers (e.g. SO-2026-000001) are separate fields, never the PK.
* ``TimeStampedModel`` / ``AuthoredModel`` add audit columns.
* ``SoftDeleteModel`` is *opt-in*. It is applied only to entities whose history
  must be preserved (master data, documents). Transient/log rows are hard
  deleted. Do not blindly inherit soft-delete everywhere.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.core.managers import AliveManager, AllObjectsManager, SoftDeleteQuerySet


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID")

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuthoredModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel, AuthoredModel):
    """Standard base for platform entities (no soft delete)."""

    class Meta:
        abstract = True


class SoftDeleteModel(BaseModel):
    """Opt-in soft-delete base. ``objects`` hides deleted rows."""

    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = AliveManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def delete(self, using=None, keep_parents=False):
        from django.utils import timezone

        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at", "updated_at"])


__all__ = [
    "UUIDModel",
    "TimeStampedModel",
    "AuthoredModel",
    "BaseModel",
    "SoftDeleteModel",
    "SoftDeleteQuerySet",
]
