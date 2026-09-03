"""Serializers for shipment — allocations and deliveries."""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import UnitOfMeasure
from apps.core.validation import PositiveDecimalField
from apps.inventory.models import TraceabilityUnit, Warehouse
from apps.organization.models import Company
from apps.partners.models import Customer
from apps.sales.models import SalesOrder, SalesOrderLine
from apps.shipment.models import Allocation, AllocationStatus, Shipment, ShipmentLine


class AllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allocation
        fields = [
            "id",
            "company",
            "sales_order_line",
            "traceability_unit",
            "quantity",
            "uom",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status"]

    quantity = PositiveDecimalField()

    def validate(self, attrs):
        comp = attrs.get("company", getattr(self.instance, "company", None))
        unit = attrs.get("traceability_unit", getattr(self.instance, "traceability_unit", None))
        sol = attrs.get("sales_order_line", getattr(self.instance, "sales_order_line", None))
        errors = {}
        if unit and comp and unit.company_id != comp.id:
            errors["traceability_unit"] = "Unit must belong to the same company."
        if sol and comp and sol.order.company_id != comp.id:
            errors["sales_order_line"] = "Order line must belong to the same company."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class ShipmentLineInputSerializer(serializers.Serializer):
    traceability_unit = serializers.PrimaryKeyRelatedField(queryset=TraceabilityUnit.objects.all())
    sales_order_line = serializers.PrimaryKeyRelatedField(
        queryset=SalesOrderLine.objects.all(), required=False, allow_null=True
    )
    allocation = serializers.PrimaryKeyRelatedField(
        queryset=Allocation.objects.filter(status=AllocationStatus.RESERVED),
        required=False,
        allow_null=True,
    )
    quantity = PositiveDecimalField()
    uom = serializers.PrimaryKeyRelatedField(queryset=UnitOfMeasure.objects.all())
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ShipmentCreateSerializer(serializers.Serializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all())
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    sales_order = serializers.PrimaryKeyRelatedField(
        queryset=SalesOrder.objects.all(), required=False, allow_null=True
    )
    number = serializers.CharField(max_length=40)
    shipped_at = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    # Client-supplied idempotency key; duplicates are rejected by the DB
    # unique constraint (mapped to 409 in the view).
    nonce = serializers.UUIDField(required=False, allow_null=True)
    lines = ShipmentLineInputSerializer(many=True)

    def validate(self, attrs):
        company = attrs["company"]
        warehouse = attrs["warehouse"]
        customer = attrs["customer"]
        sales_order = attrs.get("sales_order")
        errors = {}
        if warehouse.company_id != company.id:
            errors["warehouse"] = "Warehouse must belong to the shipment company."
        if customer.partner.company_id != company.id:
            errors["customer"] = "Customer must belong to the shipment company."
        if sales_order is not None and sales_order.company_id != company.id:
            errors["sales_order"] = "Sales order must belong to the shipment company."
        for i, line in enumerate(attrs.get("lines", [])):
            unit = line.get("traceability_unit")
            sol = line.get("sales_order_line")
            alloc = line.get("allocation")
            if unit and unit.company_id != company.id:
                errors.setdefault("lines", {}).setdefault(i, {})[
                    "traceability_unit"
                ] = "Unit must belong to the shipment company."
            if sol and sol.order.company_id != company.id:
                errors.setdefault("lines", {}).setdefault(i, {})[
                    "sales_order_line"
                ] = "Order line must belong to the shipment company."
            if alloc and alloc.company_id != company.id:
                errors.setdefault("lines", {}).setdefault(i, {})[
                    "allocation"
                ] = "Allocation must belong to the shipment company."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class ShipmentLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentLine
        fields = [
            "id",
            "shipment",
            "sales_order_line",
            "allocation",
            "traceability_unit",
            "quantity",
            "uom",
            "notes",
        ]
        read_only_fields = fields


class ShipmentSerializer(serializers.ModelSerializer):
    lines = ShipmentLineSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = [
            "id",
            "company",
            "sales_order",
            "customer",
            "warehouse",
            "number",
            "status",
            "shipped_at",
            "notes",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
