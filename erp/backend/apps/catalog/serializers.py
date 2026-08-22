"""Serializers for catalog master data (shape + input validation only)."""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import (
    Material,
    Product,
    ProductClass,
    ProductFamily,
    ProductGroup,
    ProductType,
    UnitOfMeasure,
    UomConversion,
)


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = [
            "id",
            "code",
            "name_fa",
            "name_en",
            "dimension",
            "is_active",
            "created_at",
            "updated_at",
        ]


class UomConversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UomConversion
        fields = ["id", "from_uom", "to_uom", "factor", "created_at", "updated_at"]

    def validate(self, attrs):
        from_uom = attrs.get("from_uom", getattr(self.instance, "from_uom", None))
        to_uom = attrs.get("to_uom", getattr(self.instance, "to_uom", None))
        factor = attrs.get("factor", getattr(self.instance, "factor", None))
        if from_uom and to_uom:
            if from_uom == to_uom:
                raise serializers.ValidationError(
                    "A conversion must be between two different units."
                )
            if from_uom.dimension != to_uom.dimension:
                raise serializers.ValidationError("Both units must belong to the same dimension.")
        if factor is not None and factor <= 0:
            raise serializers.ValidationError("Conversion factor must be positive.")
        return attrs


class ProductGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductGroup
        fields = [
            "id",
            "code",
            "name_fa",
            "name_en",
            "is_active",
            "created_at",
            "updated_at",
        ]


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = [
            "id",
            "code",
            "name_fa",
            "name_en",
            "is_active",
            "created_at",
            "updated_at",
        ]


class ProductClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductClass
        fields = [
            "id",
            "product_type",
            "code",
            "name_fa",
            "name_en",
            "is_active",
            "created_at",
            "updated_at",
        ]


class ProductFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFamily
        fields = [
            "id",
            "product_class",
            "code",
            "name_fa",
            "name_en",
            "is_active",
            "created_at",
            "updated_at",
        ]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "company",
            "code",
            "name_fa",
            "name_en",
            "product_group",
            "family",
            "base_uom",
            "is_active",
            "created_at",
            "updated_at",
        ]


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = [
            "id",
            "company",
            "code",
            "name_fa",
            "name_en",
            "subtype",
            "traceability_mode",
            "base_uom",
            "reorder_point",
            "safety_stock",
            "min_stock",
            "max_stock",
            "lead_time_days",
            "shelf_life_days",
            "is_hazardous",
            "msds_ref",
            "is_active",
            "created_at",
            "updated_at",
        ]
