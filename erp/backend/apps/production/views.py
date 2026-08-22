"""Production API: work orders plus execution postings."""

from __future__ import annotations

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.exceptions import ConflictError
from apps.core.viewsets import AuditedModelViewSet, StatusSummaryMixin
from apps.production import services
from apps.production.models import (
    MaterialIssue,
    ProductionOrder,
    ProductionOrderStatus,
    ProductionOutput,
)
from apps.production.serializers import (
    MaterialIssueSerializer,
    ProductionOrderSerializer,
    ProductionOutputSerializer,
)

PO = ProductionOrderStatus
_PO_ENTITY = "production.ProductionOrder"


class ProductionOrderViewSet(StatusSummaryMixin, AuditedModelViewSet):
    queryset = ProductionOrder.objects.all().select_related(
        "company",
        "site",
        "customer_product",
        "spec_revision",
        "bom_revision",
        "routing_revision",
        "sales_order_line",
        "uom",
    )
    serializer_class = ProductionOrderSerializer
    permission_map = {
        "POST": "production.order.manage",
        "PUT": "production.order.manage",
        "PATCH": "production.order.manage",
        "DELETE": "production.order.manage",
    }
    required_permission = "production.order.view"
    filterset_fields = [
        "company",
        "site",
        "customer_product",
        "spec_revision",
        "sales_order_line",
        "status",
    ]
    search_fields = ["number", "notes"]

    def perform_update(self, serializer):
        services.assert_document_editable(self.get_object())
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        services.assert_document_editable(instance)
        super().perform_destroy(instance)

    def _transition(self, request, *, to_status, allowed_from):
        document = self.get_object()
        services.transition(
            document=document,
            entity_type=_PO_ENTITY,
            to_status=to_status,
            allowed_from=allowed_from,
            actor=request.user,
        )
        return Response(self.get_serializer(document).data)

    @action(detail=True, methods=["post"], url_path="release")
    def release(self, request, pk=None):
        return self._transition(request, to_status=PO.RELEASED, allowed_from=[PO.DRAFT])

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        return self._transition(request, to_status=PO.COMPLETED, allowed_from=[PO.RELEASED])

    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        return self._transition(request, to_status=PO.CLOSED, allowed_from=[PO.COMPLETED])

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        return self._transition(
            request, to_status=PO.CANCELLED, allowed_from=[PO.DRAFT, PO.RELEASED, PO.COMPLETED]
        )


class MaterialIssueViewSet(AuditedModelViewSet):
    company_scope_lookup = "production_order__company"
    queryset = MaterialIssue.objects.all().select_related(
        "production_order", "material", "traceability_unit", "warehouse", "uom"
    )
    serializer_class = MaterialIssueSerializer
    permission_map = {"POST": "production.execution.manage"}
    required_permission = "production.execution.view"
    filterset_fields = ["production_order", "material", "traceability_unit", "method", "warehouse"]

    def perform_create(self, serializer):
        services.create_material_issue(serializer, actor=self.request.user)

    def perform_update(self, serializer):
        raise ConflictError("Material issues are append-only.", code="append_only")

    def perform_destroy(self, instance):
        raise ConflictError("Material issues are append-only.", code="append_only")


class ProductionOutputViewSet(AuditedModelViewSet):
    company_scope_lookup = "production_order__company"
    queryset = ProductionOutput.objects.all().select_related(
        "production_order", "traceability_unit", "warehouse", "uom"
    )
    serializer_class = ProductionOutputSerializer
    permission_map = {"POST": "production.execution.manage"}
    required_permission = "production.execution.view"
    filterset_fields = ["production_order", "traceability_unit", "warehouse"]

    def perform_create(self, serializer):
        services.create_production_output(serializer, actor=self.request.user)

    def perform_update(self, serializer):
        raise ConflictError("Production outputs are append-only.", code="append_only")

    def perform_destroy(self, instance):
        raise ConflictError("Production outputs are append-only.", code="append_only")
