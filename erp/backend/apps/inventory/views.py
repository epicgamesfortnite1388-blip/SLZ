"""Thin viewsets for inventory master data (audited via ``AuditedModelViewSet``).

No service layer is needed: these are plain audited CRUD masters (like
``catalog``/``partners``). The transactional inventory layer (movements, lots,
genealogy) that *would* need services is gated on Q-046 and not built here.
"""

from __future__ import annotations

from apps.core.viewsets import AuditedModelViewSet
from apps.inventory.models import Warehouse, WarehouseAccess
from apps.inventory.serializers import WarehouseAccessSerializer, WarehouseSerializer


class WarehouseViewSet(AuditedModelViewSet):
    queryset = Warehouse.objects.all().select_related("company", "site")
    serializer_class = WarehouseSerializer
    permission_map = {m: "inventory.warehouse.manage" for m in ("POST", "PUT", "PATCH", "DELETE")}
    required_permission = "inventory.warehouse.view"
    filterset_fields = ["company", "site", "store_type", "is_active"]
    search_fields = ["code", "name_fa", "name_en"]


class WarehouseAccessViewSet(AuditedModelViewSet):
    queryset = WarehouseAccess.objects.all().select_related("warehouse", "user")
    serializer_class = WarehouseAccessSerializer
    permission_map = {
        m: "inventory.warehouseaccess.manage" for m in ("POST", "PUT", "PATCH", "DELETE")
    }
    required_permission = "inventory.warehouseaccess.view"
    filterset_fields = ["warehouse", "user", "access_level"]
