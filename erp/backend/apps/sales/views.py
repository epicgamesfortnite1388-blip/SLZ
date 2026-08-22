"""Thin viewsets for Sales — Customer Orders (audited via ``AuditedModelViewSet``).

Standard audited CRUD for the order header and its lines; the document *status
transitions* are POST ``@action`` endpoints that delegate to ``apps.sales.services``
so the state machine lives in one place. Header edit/delete and child-line writes
are blocked once the order leaves DRAFT (guarded here + in serializers). Status
actions require the ``sales.order.manage`` permission (POST → manage in
``permission_map``).
"""

from __future__ import annotations

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.viewsets import AuditedModelViewSet, StatusSummaryMixin
from apps.sales import services
from apps.sales.models import SalesOrder, SalesOrderLine, SalesOrderStatus
from apps.sales.serializers import SalesOrderLineSerializer, SalesOrderSerializer

SO = SalesOrderStatus
_SO_ENTITY = "sales.SalesOrder"


class SalesOrderViewSet(StatusSummaryMixin, AuditedModelViewSet):
    queryset = SalesOrder.objects.all().select_related("company", "site", "customer")
    serializer_class = SalesOrderSerializer
    permission_map = {
        "POST": "sales.order.manage",
        "PUT": "sales.order.manage",
        "PATCH": "sales.order.manage",
        "DELETE": "sales.order.manage",
    }
    required_permission = "sales.order.view"
    filterset_fields = ["company", "site", "customer", "status"]
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
            entity_type=_SO_ENTITY,
            to_status=to_status,
            allowed_from=allowed_from,
            actor=request.user,
        )
        return Response(self.get_serializer(document).data)

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        return self._transition(request, to_status=SO.CONFIRMED, allowed_from=[SO.DRAFT])

    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        return self._transition(request, to_status=SO.CLOSED, allowed_from=[SO.CONFIRMED])

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        return self._transition(
            request,
            to_status=SO.CANCELLED,
            allowed_from=[SO.DRAFT, SO.CONFIRMED],
        )


class SalesOrderLineViewSet(AuditedModelViewSet):
    queryset = SalesOrderLine.objects.all().select_related("order", "customer_product", "uom")
    serializer_class = SalesOrderLineSerializer
    permission_map = {
        "POST": "sales.order.manage",
        "PUT": "sales.order.manage",
        "PATCH": "sales.order.manage",
        "DELETE": "sales.order.manage",
    }
    required_permission = "sales.order.view"
    filterset_fields = ["order", "customer_product"]

    def perform_destroy(self, instance):
        services.assert_document_editable(instance.order)
        super().perform_destroy(instance)
