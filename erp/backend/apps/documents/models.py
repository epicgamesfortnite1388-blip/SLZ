"""Attachment model: a generic document associated with any entity."""

from __future__ import annotations

import hashlib

from django.db import models

from apps.core.models import SoftDeleteModel


class Attachment(SoftDeleteModel):
    """A stored file linked to an arbitrary entity via (type, id).

    The raw bytes live in the storage backend under ``storage_key``; only
    metadata lives in the database. History is preserved (soft delete).
    """

    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=64, db_index=True)
    # Resolved from the referenced entity at upload time (Q-055 company
    # isolation). Nullable only for rows that predate the resolution registry;
    # new uploads always stamp it and unresolvable targets are rejected.
    company = models.ForeignKey(
        "organization.Company",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="attachments",
    )
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=150, blank=True, default="")
    size_bytes = models.PositiveBigIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64, blank=True, default="")
    storage_key = models.CharField(max_length=512, unique=True)
    description = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "documents_attachment"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["entity_type", "entity_id"])]

    def __str__(self) -> str:
        return self.original_filename

    @staticmethod
    def compute_checksum(uploaded_file) -> str:
        sha = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            sha.update(chunk)
        uploaded_file.seek(0)
        return sha.hexdigest()
