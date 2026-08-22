"""Inventory API: warehouses, traceability units, genealogy, and movements."""

from __future__ import annotations

from apps.core.exceptions import ConflictError
from apps.core.viewsets import AuditedModelViewSet
from apps.inventory.models import (
    GenealogyLink,
    StockMovement,
    TraceabilityUnit,
    Warehouse,
    WarehouseAccess,
)
from apps.inventory.serializers import (
    GenealogyLinkSerializer,
    StockMovementSerializer,
    TraceabilityUnitSerializer,
    WarehouseAccessSerializer,
    WarehouseSerializer,
)


class WarehouseViewSet(AuditedModelViewSet):
    queryset = Warehouse.objects.all().select_related("company", "site")
    serializer_class = WarehouseSerializer
    permission_map = {m: "inventory.warehouse.manage" for m in ("POST", "PUT", "PATCH", "DELETE")}
    required_permission = "inventory.warehouse.view"
    filterset_fields = ["company", "site", "store_type", "is_active"]
    search_fields = ["code", "name_fa", "name_en"]


class WarehouseAccessViewSet(AuditedModelViewSet):
    company_scope_lookup = "warehouse__company"
    queryset = WarehouseAccess.objects.all().select_related("warehouse", "user")
    serializer_class = WarehouseAccessSerializer
    permission_map = {
        m: "inventory.warehouseaccess.manage" for m in ("POST", "PUT", "PATCH", "DELETE")
    }
    required_permission = "inventory.warehouseaccess.view"
    company_scope_lookup = "warehouse__company"
    filterset_fields = ["warehouse", "user", "access_level"]


class TraceabilityUnitViewSet(AuditedModelViewSet):
    queryset = TraceabilityUnit.objects.all().select_related("company", "material", "parent", "uom")
    serializer_class = TraceabilityUnitSerializer
    permission_map = {
        m: "inventory.traceability.manage" for m in ("POST", "PUT", "PATCH", "DELETE")
    }
    required_permission = "inventory.traceability.view"
    filterset_fields = ["company", "material", "unit_type", "parent"]
    search_fields = ["identifier", "notes"]


class GenealogyLinkViewSet(AuditedModelViewSet):
    company_scope_lookup = "parent__company"
    queryset = GenealogyLink.objects.all().select_related("parent", "child")
    serializer_class = GenealogyLinkSerializer
    permission_map = {
        m: "inventory.traceability.manage" for m in ("POST", "PUT", "PATCH", "DELETE")
    }
    required_permission = "inventory.traceability.view"
    filterset_fields = ["parent", "child"]

    def perform_update(self, serializer):
        raise ConflictError("Genealogy links are append-only.", code="append_only")

    def perform_destroy(self, instance):
        raise ConflictError("Genealogy links are append-only.", code="append_only")


class StockMovementViewSet(AuditedModelViewSet):
    queryset = StockMovement.objects.all().select_related(
        "company", "warehouse", "traceability_unit", "material", "uom"
    )
    serializer_class = StockMovementSerializer
    permission_map = {"POST": "inventory.movement.manage"}
    required_permission = "inventory.movement.view"
    filterset_fields = [
        "company",
        "warehouse",
        "traceability_unit",
        "material",
        "direction",
        "reference_type",
    ]

    def perform_update(self, serializer):
        raise ConflictError("Stock movements are append-only.", code="append_only")

    def perform_destroy(self, instance):
        raise ConflictError("Stock movements are append-only.", code="append_only")
