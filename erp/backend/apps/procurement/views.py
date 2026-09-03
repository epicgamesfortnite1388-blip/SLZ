"""Thin viewsets for Procurement — Requisitions & Purchase Orders (audited via
``AuditedModelViewSet``).

Standard audited CRUD for headers and lines; document *status transitions* are
POST ``@action`` endpoints that delegate to ``apps.procurement.services`` so the
state machine lives in one place. Header edit/delete and child-line writes are
blocked once the document leaves DRAFT (guarded here + in serializers). Status
actions require the ``*.manage`` permission (POST → manage in ``permission_map``).
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.viewsets import AuditedModelViewSet, StatusSummaryMixin
from apps.procurement import services
from apps.procurement.models import (
    GoodsReceipt,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseOrderStatus,
    PurchaseRequisition,
    PurchaseRequisitionLine,
    PurchaseRequisitionStatus,
)
from apps.procurement.serializers import (
    GoodsReceiptCreateSerializer,
    GoodsReceiptSerializer,
    PurchaseOrderLineSerializer,
    PurchaseOrderSerializer,
    PurchaseRequisitionLineSerializer,
    PurchaseRequisitionSerializer,
)

PR = PurchaseRequisitionStatus
PO = PurchaseOrderStatus
_PR_ENTITY = "procurement.PurchaseRequisition"
_PO_ENTITY = "procurement.PurchaseOrder"


class PurchaseRequisitionViewSet(StatusSummaryMixin, AuditedModelViewSet):
    queryset = PurchaseRequisition.objects.all().select_related("company", "site", "requested_by")
    serializer_class = PurchaseRequisitionSerializer
    permission_map = {
        "POST": "procurement.requisition.manage",
        "PUT": "procurement.requisition.manage",
        "PATCH": "procurement.requisition.manage",
        "DELETE": "procurement.requisition.manage",
    }
    required_permission = "procurement.requisition.view"
    filterset_fields = ["company", "site", "status", "requested_by"]
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
            entity_type=_PR_ENTITY,
            to_status=to_status,
            allowed_from=allowed_from,
            actor=request.user,
        )
        return Response(self.get_serializer(document).data)

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        return self._transition(request, to_status=PR.SUBMITTED, allowed_from=[PR.DRAFT])

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        return self._transition(request, to_status=PR.APPROVED, allowed_from=[PR.SUBMITTED])

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        return self._transition(request, to_status=PR.REJECTED, allowed_from=[PR.SUBMITTED])

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        return self._transition(
            request,
            to_status=PR.CANCELLED,
            allowed_from=[PR.DRAFT, PR.SUBMITTED, PR.APPROVED],
        )


class PurchaseRequisitionLineViewSet(AuditedModelViewSet):
    company_scope_lookup = "requisition__company"
    queryset = PurchaseRequisitionLine.objects.all().select_related(
        "requisition", "material", "uom"
    )
    serializer_class = PurchaseRequisitionLineSerializer
    permission_map = {
        "POST": "procurement.requisition.manage",
        "PUT": "procurement.requisition.manage",
        "PATCH": "procurement.requisition.manage",
        "DELETE": "procurement.requisition.manage",
    }
    required_permission = "procurement.requisition.view"
    filterset_fields = ["requisition", "material"]

    def perform_destroy(self, instance):
        services.assert_document_editable(instance.requisition)
        super().perform_destroy(instance)


class PurchaseOrderViewSet(StatusSummaryMixin, AuditedModelViewSet):
    queryset = PurchaseOrder.objects.all().select_related("company", "site", "supplier")
    serializer_class = PurchaseOrderSerializer
    permission_map = {
        "POST": "procurement.order.manage",
        "PUT": "procurement.order.manage",
        "PATCH": "procurement.order.manage",
        "DELETE": "procurement.order.manage",
    }
    required_permission = "procurement.order.view"
    filterset_fields = ["company", "site", "supplier", "status"]
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

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        return self._transition(request, to_status=PO.APPROVED, allowed_from=[PO.DRAFT])

    @action(detail=True, methods=["post"], url_path="send")
    def send(self, request, pk=None):
        return self._transition(request, to_status=PO.SENT, allowed_from=[PO.APPROVED])

    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        return self._transition(request, to_status=PO.CLOSED, allowed_from=[PO.SENT])

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        return self._transition(
            request,
            to_status=PO.CANCELLED,
            allowed_from=[PO.DRAFT, PO.APPROVED, PO.SENT],
        )


class PurchaseOrderLineViewSet(AuditedModelViewSet):
    company_scope_lookup = "order__company"
    queryset = PurchaseOrderLine.objects.all().select_related(
        "order", "material", "uom", "requisition_line"
    )
    serializer_class = PurchaseOrderLineSerializer
    permission_map = {
        "POST": "procurement.order.manage",
        "PUT": "procurement.order.manage",
        "PATCH": "procurement.order.manage",
        "DELETE": "procurement.order.manage",
    }
    required_permission = "procurement.order.view"
    filterset_fields = ["order", "material"]

    def perform_destroy(self, instance):
        services.assert_document_editable(instance.order)
        super().perform_destroy(instance)


class GoodsReceiptViewSet(AuditedModelViewSet):
    """Immutable goods receipts: list / retrieve / post. No edit or delete."""

    http_method_names = ["get", "post", "head", "options"]

    queryset = (
        GoodsReceipt.objects.all().select_related(
            "company", "warehouse", "supplier", "purchase_order"
        )
        # Prefetch the nested line FKs the list serializer reads (avoids N+1
        # on GRN lists).
        .prefetch_related(
            "lines",
            "lines__po_line",
            "lines__material",
            "lines__uom",
            "lines__traceability_unit",
        )
    )
    company_scope_lookup = "company"
    serializer_class = GoodsReceiptSerializer
    permission_map = {"POST": "procurement.grn.manage"}
    required_permission = "procurement.grn.view"
    filterset_fields = ["company", "warehouse", "supplier", "purchase_order", "status"]
    search_fields = ["number", "notes"]

    def perform_create(self, serializer):
        actor = getattr(self.request, "user", None)
        grn = services.create_goods_receipt(serializer, actor=actor)
        serializer.instance = grn

    def create(self, request, *args, **kwargs):
        """Return the fully-populated receipt (with lines) after posting."""
        from django.db import IntegrityError

        from apps.core.exceptions import ConflictError

        create_serializer = GoodsReceiptCreateSerializer(
            data=request.data, context={"request": request}
        )
        create_serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(create_serializer)
        except IntegrityError as exc:
            if "nonce" in str(exc).lower():
                raise ConflictError(
                    "Duplicate submission detected — this goods receipt has already been posted.",
                    code="duplicate_request",
                ) from exc
            raise
        grn = create_serializer.instance
        read_serializer = GoodsReceiptSerializer(grn, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)
