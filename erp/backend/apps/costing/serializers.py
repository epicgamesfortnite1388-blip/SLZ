"""Serializers for costing — read-only API (layers are append-only)."""

from __future__ import annotations

from rest_framework import serializers

from apps.costing.models import CostLayer


class CostLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostLayer
        fields = [
            "id",
            "company",
            "material",
            "date",
            "quantity",
            "unit_cost",
            "total_cost",
            "layer_type",
            "reference_type",
            "reference_id",
            "po_line_id",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
