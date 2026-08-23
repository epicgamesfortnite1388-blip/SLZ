"""Serializers for inventory masters and traceability execution records."""

from __future__ import annotations

from rest_framework import serializers

from apps.inventory.models import (
    GenealogyLink,
    StockMovement,
    TraceabilityUnit,
    Warehouse,
    WarehouseAccess,
)


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


class TraceabilityUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = TraceabilityUnit
        fields = [
            "id",
            "company",
            "material",
            "customer_product_id",
            "parent",
            "unit_type",
            "identifier",
            "quantity",
            "uom",
            "weight",
            "length",
            "width",
            "core",
            "notes",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        company = attrs.get("company", getattr(self.instance, "company", None))
        material = attrs.get("material", getattr(self.instance, "material", None))
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        uom = attrs.get("uom", getattr(self.instance, "uom", None))
        unit_type = attrs.get("unit_type", getattr(self.instance, "unit_type", None))
        customer_product_id = attrs.get(
            "customer_product_id", getattr(self.instance, "customer_product_id", None)
        )
        errors = {}
        if material is not None and company is not None and material.company_id != company.id:
            errors["material"] = "Material must belong to the same company."
        if parent is not None and company is not None and parent.company_id != company.id:
            errors["parent"] = "Parent unit must belong to the same company."
        if (
            uom is None
            and attrs.get("quantity", getattr(self.instance, "quantity", None)) is not None
        ):
            errors["uom"] = "A UoM is required when quantity is provided."
        if material is not None and unit_type != "PALLET":
            expected = {
                "BATCH": "BATCH",
                "SERIALIZED_ROLL": "ROLL",
                "CARTON": "CARTON",
            }.get(material.traceability_mode)
            if expected is not None and unit_type != expected:
                errors["unit_type"] = "Unit type does not match the material traceability mode."
        if customer_product_id is not None and unit_type != "PALLET":
            from apps.engineering.models import CustomerProduct

            product = CustomerProduct.objects.filter(id=customer_product_id).first()
            if product is None:
                errors["customer_product_id"] = "Customer product does not exist."
            elif product.traceability_mode == "SERIALIZED_ROLL" and unit_type != "ROLL":
                errors["unit_type"] = "Unit type does not match the product traceability mode."
            elif product.traceability_mode == "CARTON" and unit_type != "CARTON":
                errors["unit_type"] = "Unit type does not match the product traceability mode."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class GenealogyLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenealogyLink
        fields = [
            "id",
            "parent",
            "child",
            "production_order_id",
            "operation_label",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        child = attrs.get("child", getattr(self.instance, "child", None))
        if parent is not None and child is not None:
            if parent.company_id != child.company_id:
                raise serializers.ValidationError(
                    "Parent and child must belong to the same company."
                )
            if parent.id == child.id:
                raise serializers.ValidationError("A traceability unit cannot be its own ancestor.")
        return attrs


class StockMovementSerializer(serializers.ModelSerializer):
    reference_type = serializers.CharField(
        required=False,
        allow_blank=True,
        default="inventory.Adjustment",
        max_length=120,
    )

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "company",
            "warehouse",
            "traceability_unit",
            "material",
            "direction",
            "quantity",
            "uom",
            "reference_type",
            "reference_id",
            "notes",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        company = attrs.get("company", getattr(self.instance, "company", None))
        warehouse = attrs.get("warehouse", getattr(self.instance, "warehouse", None))
        unit = attrs.get("traceability_unit", getattr(self.instance, "traceability_unit", None))
        material = attrs.get("material", getattr(self.instance, "material", None))
        uom = attrs.get("uom", getattr(self.instance, "uom", None))
        errors = {}
        if warehouse is not None and company is not None and warehouse.company_id != company.id:
            errors["warehouse"] = "Warehouse must belong to the same company."
        if unit is not None and company is not None and unit.company_id != company.id:
            errors["traceability_unit"] = "Traceability unit must belong to the same company."
        if material is not None and company is not None and material.company_id != company.id:
            errors["material"] = "Material must belong to the same company."
        if unit is None and material is None:
            errors["material"] = "A movement must identify a material or traceability unit."
        if uom is None:
            errors["uom"] = "A movement UoM is required."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs
