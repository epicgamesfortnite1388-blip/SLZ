"""Thin viewsets for Quality — Characteristics & Quality Plans (audited via
``AuditedModelViewSet``).

Quality Plan revision *creation* and *activation* delegate to
``apps.quality.services`` so the (shared) versioning lifecycle stays in one
place; everything else is standard audited CRUD. Child rows (plan items) are
editable only while their revision is DRAFT (enforced in serializers). Mirrors
``apps.manufacturing.views``.
"""

from __future__ import annotations

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.exceptions import ConflictError
from apps.core.viewsets import AuditedModelViewSet
from apps.quality import services
from apps.quality.models import (
    QualityCharacteristic,
    QualityCheckResult,
    QualityPlan,
    QualityPlanItem,
    QualityPlanRevision,
)
from apps.quality.serializers import (
    QualityCharacteristicSerializer,
    QualityCheckResultSerializer,
    QualityPlanItemSerializer,
    QualityPlanRevisionSerializer,
    QualityPlanSerializer,
)


class QualityCharacteristicViewSet(AuditedModelViewSet):
    queryset = QualityCharacteristic.objects.all().select_related("company", "default_uom")
    serializer_class = QualityCharacteristicSerializer
    permission_map = {
        "POST": "quality.characteristic.manage",
        "PUT": "quality.characteristic.manage",
        "PATCH": "quality.characteristic.manage",
        "DELETE": "quality.characteristic.manage",
    }
    required_permission = "quality.characteristic.view"
    filterset_fields = ["company", "datatype", "is_active"]
    search_fields = ["code", "name_fa", "name_en", "method"]


class QualityPlanViewSet(AuditedModelViewSet):
    company_scope_lookup = "spec_revision__root__company"
    queryset = QualityPlan.objects.all().select_related("spec_revision")
    serializer_class = QualityPlanSerializer
    permission_map = {
        "POST": "quality.plan.manage",
        "PUT": "quality.plan.manage",
        "PATCH": "quality.plan.manage",
        "DELETE": "quality.plan.manage",
    }
    required_permission = "quality.plan.view"
    filterset_fields = ["spec_revision", "is_active"]


class QualityPlanRevisionViewSet(AuditedModelViewSet):
    company_scope_lookup = "root__spec_revision__root__company"
    queryset = QualityPlanRevision.objects.all().select_related("root")
    serializer_class = QualityPlanRevisionSerializer
    permission_map = {
        "POST": "quality.plan.manage",
        "PUT": "quality.plan.manage",
        "PATCH": "quality.plan.manage",
        "DELETE": "quality.plan.manage",
    }
    required_permission = "quality.plan.view"
    filterset_fields = ["root", "status"]

    def perform_create(self, serializer):
        actor = getattr(self.request, "user", None)
        data = dict(serializer.validated_data)
        root = data.pop("root")
        revision = services.create_revision_draft(
            revision_model=QualityPlanRevision,
            entity_type="quality.QualityPlanRevision",
            root=root,
            actor=actor,
            **data,
        )
        serializer.instance = revision

    def perform_update(self, serializer):
        services.assert_revision_editable(self.get_object())
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        services.assert_revision_editable(instance)
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        revision = self.get_object()
        services.activate_revision(
            revision=revision,
            entity_type="quality.QualityPlanRevision",
            actor=request.user,
        )
        return Response(self.get_serializer(revision).data)


class QualityPlanItemViewSet(AuditedModelViewSet):
    company_scope_lookup = "revision__root__spec_revision__root__company"
    queryset = QualityPlanItem.objects.all().select_related(
        "revision", "characteristic", "work_center"
    )
    serializer_class = QualityPlanItemSerializer
    permission_map = {
        "POST": "quality.plan.manage",
        "PUT": "quality.plan.manage",
        "PATCH": "quality.plan.manage",
        "DELETE": "quality.plan.manage",
    }
    required_permission = "quality.plan.view"
    filterset_fields = ["revision", "characteristic", "work_center"]


class QualityCheckResultViewSet(AuditedModelViewSet):
    """Append-only QC results: list / retrieve / post. No edit or delete."""

    http_method_names = ["get", "post", "head", "options"]

    company_scope_lookup = "plan_item__revision__root__spec_revision__root__company"
    queryset = QualityCheckResult.objects.all().select_related(
        "plan_item", "traceability_unit", "checked_by"
    )
    serializer_class = QualityCheckResultSerializer
    permission_map = {"POST": "quality.results.manage"}
    required_permission = "quality.results.view"
    filterset_fields = [
        "plan_item",
        "traceability_unit",
        "disposition",
    ]

    def perform_create(self, serializer):
        result = services.post_check_result(
            plan_item=serializer.validated_data["plan_item"],
            traceability_unit=serializer.validated_data["traceability_unit"],
            measured_value=serializer.validated_data["measured_value"],
            disposition=serializer.validated_data["disposition"],
            checked_at=serializer.validated_data["checked_at"],
            checked_by=serializer.validated_data.get("checked_by"),
            notes=serializer.validated_data.get("notes", ""),
            actor=self.request.user,
        )
        serializer.instance = result

    def perform_update(self, serializer):
        raise ConflictError("QC results are append-only.", code="append_only")

    def perform_destroy(self, instance):
        raise ConflictError("QC results are append-only.", code="append_only")
