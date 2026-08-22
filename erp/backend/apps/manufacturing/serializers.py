"""Serializers for Manufacturing — BOM & Routing (shape + input validation).

Business/lifecycle rules live in ``apps.manufacturing.services``; these
serializers validate wire shape and revision editability so clients get clean
4xx errors instead of 500s. Mirrors ``apps.engineering.serializers``.
"""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.core.exceptions import ConflictError
from apps.core.validation import PositiveDecimalField
from apps.manufacturing.models import (
    BillOfMaterials,
    BomLine,
    BomRevision,
    Machine,
    Routing,
    RoutingOperation,
    RoutingRevision,
    WorkCenter,
)


class WorkCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCenter
        fields = [
            "id",
            "company",
            "site",
            "code",
            "name_fa",
            "name_en",
            "sequence_hint",
            "is_active",
            "created_at",
            "updated_at",
        ]


class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = [
            "id",
            "company",
            "site",
            "work_center",
            "code",
            "name_fa",
            "name_en",
            "capability_profile",
            "is_active",
            "created_at",
            "updated_at",
        ]


class BillOfMaterialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillOfMaterials
        fields = [
            "id",
            "spec_revision",
            "output_material",
            "is_active",
            "created_at",
            "updated_at",
        ]


class BomRevisionSerializer(serializers.ModelSerializer):
    """Read + DRAFT-create. ``root`` writable on create; ``revision_number`` /
    ``status`` / effective dates are managed by the service."""

    class Meta:
        model = BomRevision
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


class RoutingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Routing
        fields = [
            "id",
            "spec_revision",
            "is_active",
            "created_at",
            "updated_at",
        ]


class RoutingRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingRevision
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
    """Base for revision child rows: forbid attaching/moving to a non-DRAFT
    revision (immutability rule)."""

    def _target_revision(self, attrs):
        return attrs.get("revision") or getattr(self.instance, "revision", None)

    def validate(self, attrs):
        revision = self._target_revision(attrs)
        if revision is not None and not revision.is_editable:
            raise ConflictError(
                "The parent revision is not in DRAFT; create a new revision "
                "before editing its content.",
                code="revision_not_editable",
            )
        return attrs


class BomLineSerializer(_ChildOfRevisionSerializer):
    class Meta:
        model = BomLine
        fields = [
            "id",
            "revision",
            "sequence",
            "material",
            "quantity_per_output",
            "uom",
            "consumption_basis",
            "scrap_pct",
            "notes",
            "created_at",
            "updated_at",
        ]

    # A component consumption of zero or less is internally contradictory.
    quantity_per_output = PositiveDecimalField()
    # A negative scrap percentage is meaningless; zero is allowed.
    scrap_pct = serializers.DecimalField(
        max_digits=7,
        decimal_places=4,
        min_value=Decimal("0"),
        allow_null=True,
        required=False,
    )


class RoutingOperationSerializer(_ChildOfRevisionSerializer):
    class Meta:
        model = RoutingOperation
        fields = [
            "id",
            "revision",
            "sequence",
            "work_center",
            "operation_name",
            "output_material",
            "setup_time_minutes",
            "run_rate",
            "run_rate_basis",
            "notes",
            "created_at",
            "updated_at",
        ]
