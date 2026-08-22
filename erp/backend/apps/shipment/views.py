"""Shipment API: allocations, releases, and deliveries."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.exceptions import ConflictError
from apps.core.viewsets import AuditedModelViewSet
from apps.shipment import services
from apps.shipment.models import Allocation, Shipment
from apps.shipment.serializers import (
    AllocationSerializer,
    ShipmentCreateSerializer,
    ShipmentSerializer,
)


class AllocationViewSet(AuditedModelViewSet):
    """List/create allocations. Release via POST /allocations/{id}/release/."""

    queryset = Allocation.objects.all().select_related(
        "company", "sales_order_line", "traceability_unit", "uom"
    )
    serializer_class = AllocationSerializer
    permission_map = {m: "shipment.allocation.manage" for m in ("POST", "PUT", "PATCH", "DELETE")}
    required_permission = "shipment.allocation.view"
    filterset_fields = [
        "company",
        "sales_order_line",
        "traceability_unit",
        "status",
    ]

    def perform_create(self, serializer):
        company = serializer.validated_data["company"]
        alloc = services.reserve(
            company=company,
            sales_order_line=serializer.validated_data["sales_order_line"],
            traceability_unit=serializer.validated_data["traceability_unit"],
            quantity=serializer.validated_data["quantity"],
            uom=serializer.validated_data["uom"],
            notes=serializer.validated_data.get("notes", ""),
            actor=self.request.user,
        )
        serializer.instance = alloc

    @action(detail=True, methods=["post"], url_path="release")
    def release_allocation(self, request, pk=None):
        alloc = self.get_object()
        services.release(alloc, actor=request.user)
        return Response(self.get_serializer(alloc).data)


class ShipmentViewSet(AuditedModelViewSet):
    """Immutable shipments: list / retrieve / post. No edit or delete."""

    http_method_names = ["get", "post", "head", "options"]

    queryset = (
        Shipment.objects.all()
        .select_related("company", "sales_order", "customer", "warehouse")
        .prefetch_related("lines")
    )
    serializer_class = ShipmentSerializer
    permission_map = {"POST": "shipment.delivery.manage"}
    required_permission = "shipment.delivery.view"
    filterset_fields = [
        "company",
        "sales_order",
        "customer",
        "warehouse",
        "status",
    ]
    search_fields = ["number", "notes"]

    def perform_create(self, serializer):
        s = services.create_shipment(serializer, actor=self.request.user)
        serializer.instance = s

    def create(self, request, *args, **kwargs):
        create_serializer = ShipmentCreateSerializer(
            data=request.data, context={"request": request}
        )
        create_serializer.is_valid(raise_exception=True)
        self.perform_create(create_serializer)
        shipment = create_serializer.instance
        read_serializer = ShipmentSerializer(shipment, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        raise ConflictError("Shipments are immutable.", code="append_only")

    def perform_destroy(self, instance):
        raise ConflictError("Shipments are immutable.", code="append_only")
