"""Serializers for inventory master data (shape + input validation only)."""

from __future__ import annotations

from rest_framework import serializers

from apps.inventory.models import Warehouse, WarehouseAccess


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = [
            "id",
            "company",
            "site",
            "code",
            "name_fa",
            "name_en",
            "store_type",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]


class WarehouseAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseAccess
        fields = [
            "id",
            "warehouse",
            "user",
            "access_level",
            "created_at",
            "updated_at",
        ]
