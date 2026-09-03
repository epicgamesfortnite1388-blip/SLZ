"""Inventory API: warehouses, traceability units, genealogy, and movements."""

from __future__ import annotations

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.exceptions import ConflictError
from apps.core.viewsets import AuditedModelViewSet
from apps.inventory import services
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
    TransferMovementSerializer,
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

    def perform_create(self, serializer):
        """Direct POSTs are manual adjustments and MUST go through the
        sanctioned posting service so negative-stock and quarantine guards
        apply. Reference metadata is server-controlled to prevent spoofing
        real domain documents."""
        payload = serializer.validated_data
        self._assert_company_allowed(self._payload_company_id(serializer))
        movement = services.post_movement(
            company=payload["company"],
            warehouse=payload["warehouse"],
            direction=payload["direction"],
            quantity=payload["quantity"],
            uom=payload["uom"],
            material=payload.get("material"),
            traceability_unit=payload.get("traceability_unit"),
            reference_type="inventory.Adjustment",
            notes=payload.get("notes", ""),
            actor=self.request.user,
        )
        serializer.instance = movement

    def perform_update(self, serializer):
        raise ConflictError("Stock movements are append-only.", code="append_only")

    def perform_destroy(self, instance):
        raise ConflictError("Stock movements are append-only.", code="append_only")

    def get_queryset(self):
        """Company-scoped ledger rows (Q-055)."""
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            return qs
        ids = user.company_memberships.values_list("company_id", flat=True)
        return qs.filter(company_id__in=ids)

    def _member_company(self):
        """Resolve the company this ledger query addresses.

        Single-company members get their company automatically;
        multi-company users must pass ``company`` from their memberships.
        """
        import uuid as uuid_module

        from apps.core.exceptions import AuthorizationError, ValidationError
        from apps.organization.models import Company

        user = self.request.user
        requested = self.request.query_params.get("company")
        member_ids = set(user.company_memberships.values_list("company_id", flat=True))
        if requested:
            try:
                requested_id = uuid_module.UUID(requested)
            except ValueError as exc:
                raise ValidationError("Invalid company id.") from exc
            if requested_id not in member_ids:
                raise AuthorizationError("That company is not yours.")
            return Company.objects.get(pk=requested_id)
        if len(member_ids) == 1:
            return Company.objects.get(pk=next(iter(member_ids)))
        raise ValidationError(
            "Multiple companies available - pass ?company=<id>.",
            code="inventory.company_required",
        )

    @action(detail=False, methods=["get"], url_path="balances")
    def balances(self, request):
        """Derived on-hand quantities grouped by warehouse/material/unit."""
        company = self._member_company()
        rows = services.balances(
            company,
            material=request.query_params.get("material"),
            warehouse=request.query_params.get("warehouse"),
        )
        return Response(rows)

    @action(detail=False, methods=["get"], url_path="kardex")
    def kardex(self, request):
        """Chronological ledger history with running balance."""
        company = self._member_company()
        rows = services.kardex(
            company=company,
            traceability_unit=request.query_params.get("traceability_unit"),
            material=request.query_params.get("material"),
            warehouse=request.query_params.get("warehouse"),
        )
        return Response(rows)

    @action(detail=False, methods=["post"], url_path="transfer")
    def transfer(self, request):
        """POST /inventory/movements/transfer/ — atomic OUT+IN pair between
        two warehouses of the same company (negative-stock and quarantine
        guards apply at the source)."""
        serializer = TransferMovementSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        self._assert_company_allowed(payload["company"].pk)
        out, incoming = services.transfer_stock(
            company=payload["company"],
            from_warehouse=payload["from_warehouse"],
            to_warehouse=payload["to_warehouse"],
            quantity=payload["quantity"],
            uom=payload["uom"],
            material=payload.get("material"),
            traceability_unit=payload.get("traceability_unit"),
            notes=payload.get("notes", ""),
            actor=request.user,
        )
        return Response(
            {
                "from": StockMovementSerializer(out).data,
                "to": StockMovementSerializer(incoming).data,
            },
            status=201,
        )
