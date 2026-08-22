"""Reusable versioning abstractions.

Future business modules (Specification, BOM, Routing, Artwork, Price list) all
share the same shape: a stable *root* entity plus an ordered series of
immutable *revisions*, exactly one of which is ACTIVE at a time. This module
provides the reusable pattern only — it does NOT define any business entity.

Rules encoded here (see docs/architecture/versioning.md):
* A revision is immutable once it leaves DRAFT; corrections create a new
  revision rather than editing history.
* Superseding a revision never deletes the old one (auditability).
* The concrete produced configuration must always be reconstructable from the
  revision that was in effect — so downstream records reference a revision id,
  not just the root.
"""

from __future__ import annotations

from django.db import models

from apps.core.models import BaseModel


class RevisionStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    ACTIVE = "ACTIVE", "Active"
    SUPERSEDED = "SUPERSEDED", "Superseded"
    ARCHIVED = "ARCHIVED", "Archived"


class VersionedRoot(BaseModel):
    """Abstract stable identity that owns a series of revisions."""

    class Meta:
        abstract = True


class Revision(BaseModel):
    """Abstract immutable revision.

    Concrete subclasses add a ForeignKey ``root`` to their VersionedRoot and any
    payload fields. ``revision_number`` is monotonic per root.
    """

    revision_number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16, choices=RevisionStatus.choices, default=RevisionStatus.DRAFT
    )
    effective_from = models.DateTimeField(null=True, blank=True)
    effective_to = models.DateTimeField(null=True, blank=True)
    change_reason = models.TextField(blank=True, default="")

    class Meta:
        abstract = True
        ordering = ["revision_number"]

    @property
    def is_active(self) -> bool:
        return self.status == RevisionStatus.ACTIVE

    @property
    def is_editable(self) -> bool:
        """Only DRAFT revisions may be edited; everything else is immutable."""
        return self.status == RevisionStatus.DRAFT
