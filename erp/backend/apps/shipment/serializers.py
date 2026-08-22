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
    lines = ShipmentLineInputSerializer(many=True)


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
