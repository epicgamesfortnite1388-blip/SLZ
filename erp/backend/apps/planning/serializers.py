"""Planning serializers — reorder policies (shape + cross-company validation)."""

from __future__ import annotations

from rest_framework import serializers

from apps.planning.models import PlanningPolicy


class PlanningPolicySerializer(serializers.ModelSerializer):
    item_code = serializers.SerializerMethodField()
    item_name_fa = serializers.SerializerMethodField()
    item_type = serializers.SerializerMethodField()

    class Meta:
        model = PlanningPolicy
        fields = [
            "id",
            "company",
            "warehouse",
            "material",
            "customer_product",
            "item_code",
            "item_name_fa",
            "item_type",
            "reorder_point",
            "target_level",
            "safety_stock",
            "preferred_supplier",
            "lead_time_days",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            # Exactly one of the two is required — enforced in validate(); both
            # must stay optional so the error is the semantic one below.
            "material": {"required": False, "allow_null": True},
            "customer_product": {"required": False, "allow_null": True},
        }

    def get_item_code(self, obj) -> str:
        return obj.item_code

    def get_item_name_fa(self, obj) -> str:
        return obj.item_name_fa

    def get_item_type(self, obj) -> str:
        return obj.item_type

    def get_validators(self):
        # The model's conditional UniqueConstraints (material XOR
        # customer_product) would otherwise be auto-expanded into
        # UniqueTogetherValidators that demand BOTH item fields. Uniqueness is
        # enforced explicitly in validate() instead, matching the XOR rule.
        return []

    def validate(self, attrs):
        instance = self.instance
        company = attrs.get("company", getattr(instance, "company", None))
        warehouse = attrs.get("warehouse", getattr(instance, "warehouse", None))
        item_fields_present = any(k in attrs for k in ("material", "customer_product"))
        material = attrs.get("material", getattr(instance, "material", None))
        customer_product = attrs.get(
            "customer_product", getattr(instance, "customer_product", None)
        )
        supplier = attrs.get("preferred_supplier")
        errors = {}
        # Exactly one item kind: mandatory on create; on update only when the
        # item fields are touched (a reorder-point-only PATCH stays legal).
        if instance is None or item_fields_present:
            if bool(material) == bool(customer_product):
                errors["material"] = "Set exactly one of material or customer_product."
        # Warehouse must belong to the policy company.
        if company and warehouse and warehouse.company_id != company.id:
            errors["warehouse"] = "Warehouse must belong to the policy company."
        # Preferred supplier must belong to the company (when provided).
        if supplier is not None and supplier.partner.company_id != company.id:
            errors["preferred_supplier"] = "Supplier must belong to the policy company."
        # No duplicate policy for the same company + warehouse + item.
        if errors:
            raise serializers.ValidationError(errors)
        queryset = PlanningPolicy.objects.filter(company=company, warehouse=warehouse)
        if instance is not None:
            queryset = queryset.exclude(pk=instance.pk)
        if material is not None and queryset.filter(material=material).exists():
            raise serializers.ValidationError(
                {"material": "A policy already exists for this material in this warehouse."}
            )
        if (
            customer_product is not None
            and queryset.filter(customer_product=customer_product).exists()
        ):
            raise serializers.ValidationError(
                {
                    "customer_product": (
                        "A policy already exists for this product in this warehouse."
                    )
                }
            )
        return attrs
