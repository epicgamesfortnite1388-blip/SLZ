"""Serializers for Quality — Characteristics & Quality Plans (shape + input
validation).

Business/lifecycle rules live in ``apps.quality.services``; these serializers
validate wire shape and revision editability so clients get clean 4xx errors
instead of 500s. Mirrors ``apps.manufacturing.serializers``.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.core.exceptions import ConflictError
from apps.quality.models import (
    QualityCharacteristic,
    QualityPlan,
    QualityPlanItem,
    QualityPlanRevision,
)


class QualityCharacteristicSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityCharacteristic
        fields = [
            "id",
            "company",
            "code",
            "name_fa",
            "name_en",
            "datatype",
            "method",
            "default_uom",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]


class QualityPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityPlan
        fields = [
            "id",
            "spec_revision",
            "is_active",
            "created_at",
            "updated_at",
        ]


class QualityPlanRevisionSerializer(serializers.ModelSerializer):
    """Read + DRAFT-create. ``root`` writable on create; ``revision_number`` /
    ``status`` / effective dates are managed by the service."""

    class Meta:
        model = QualityPlanRevision
        fields = [
            "id",
            "root",
            "revision_number",
            "status",
            "effective_from",
            "effective_to",
            "change_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "revision_number",
            "status",
            "effective_from",
            "effective_to",
        ]


class _ChildOfRevisionSerializer(serializers.ModelSerializer):
    """Base for revision child rows. Enforces revision immutability (a non-DRAFT
    revision may not be edited) and offers a ``_validate_references`` hook for
    subclasses to add referential-integrity (e.g. cross-company) checks."""

    def _target_revision(self, attrs):
        return attrs.get("revision") or getattr(self.instance, "revision", None)

    def _resolved(self, attrs, field):
        if field in attrs:
            return attrs[field]
        return getattr(self.instance, field, None)

    def _validate_references(self, attrs, revision, errors):
        """Hook: subclasses add referential-integrity checks into ``errors``."""
        return

    def validate(self, attrs):
        revision = self._target_revision(attrs)
        if revision is not None and not revision.is_editable:
            raise ConflictError(
                "The parent revision is not in DRAFT; create a new revision "
                "before editing its content.",
                code="revision_not_editable",
            )
        errors = {}
        self._validate_references(attrs, revision, errors)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class QualityPlanItemSerializer(_ChildOfRevisionSerializer):
    def _validate_references(self, attrs, revision, errors):
        """A plan item must not reference master data from another company than
        the product the plan is written for (DR-040). The plan's company is
        derived through spec_revision → customer_product. Pure data-integrity
        invariant — it invents no business rule."""
        if revision is None:
            return
        # revision.root -> QualityPlan -> spec_revision -> root (CustomerProduct)
        plan_company_id = revision.root.spec_revision.root.company_id
        characteristic = self._resolved(attrs, "characteristic")
        if characteristic is not None and characteristic.company_id != plan_company_id:
            errors["characteristic"] = (
                "Characteristic belongs to a different company than the plan's " "product."
            )
        work_center = self._resolved(attrs, "work_center")
        if work_center is not None and work_center.company_id != plan_company_id:
            errors["work_center"] = (
                "Work center belongs to a different company than the plan's " "product."
            )

    class Meta:
        model = QualityPlanItem
        fields = [
            "id",
            "revision",
            "sequence",
            "characteristic",
            "work_center",
            "stage_label",
            "lower_limit",
            "upper_limit",
            "target",
            "unit",
            "sampling",
            "method_override",
            "is_mandatory",
            "notes",
            "created_at",
            "updated_at",
        ]
