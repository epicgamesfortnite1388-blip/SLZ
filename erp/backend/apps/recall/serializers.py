"""Recall serializers — recall record + affected traceability units."""

from __future__ import annotations

from rest_framework import serializers

from apps.recall.models import Recall, RecallAffectedUnit, RecallStatus


class RecallSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    severity_label = serializers.CharField(source="get_severity_display", read_only=True)
    affected_count = serializers.SerializerMethodField()

    class Meta:
        model = Recall
        fields = [
            "id",
            "company",
            "code",
            "reason",
            "severity",
            "severity_label",
            "status",
            "status_label",
            "initiated_at",
            "initiated_by",
            "notes",
            "affected_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "initiated_at", "initiated_by", "created_at", "updated_at"]
        extra_kwargs = {
            "code": {"required": True},
            "reason": {"required": True},
            "severity": {"required": False},
        }

    def get_affected_count(self, obj) -> int:
        return obj.affected_units.count()

    def validate_status(self, value):
        """Status is managed through the explicit transition service."""
        if self.instance is not None and value != self.instance.status:
            raise serializers.ValidationError("Status changes must use the transition endpoint.")
        if value and value not in (RecallStatus.DRAFT,):
            raise serializers.ValidationError("New recalls must start as DRAFT.")
        return value


class RecallAffectedUnitSerializer(serializers.ModelSerializer):
    unit_identifier = serializers.CharField(source="traceability_unit.identifier", read_only=True)
    unit_type = serializers.CharField(source="traceability_unit.unit_type", read_only=True)
    unit_company = serializers.UUIDField(source="traceability_unit.company_id", read_only=True)

    class Meta:
        model = RecallAffectedUnit
        fields = [
            "id",
            "recall",
            "traceability_unit",
            "unit_identifier",
            "unit_type",
            "unit_company",
            "note",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {"traceability_unit": {"required": True}}

    def validate(self, attrs):
        recall = attrs.get("recall", getattr(self.instance, "recall", None))
        unit = attrs.get("traceability_unit", getattr(self.instance, "traceability_unit", None))
        if recall is None or unit is None:
            return attrs
        # A recall may only reference units of its own company.
        if unit.company_id != recall.company_id:
            raise serializers.ValidationError(
                {"traceability_unit": "Traceability unit must belong to the recall's company."}
            )
        # Adding units to a finalized recall is a state violation.
        if getattr(self, "instance", None) is None and recall.is_terminal:
            raise serializers.ValidationError(
                {"recall": "Cannot add units to a closed or cancelled recall."}
            )
        return attrs
