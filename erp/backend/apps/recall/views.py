"""Recall viewsets — recall records, affected units, exposure, transitions."""

from __future__ import annotations

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.viewsets import AuditedModelViewSet
from apps.recall import services
from apps.recall.models import Recall, RecallAffectedUnit
from apps.recall.serializers import RecallAffectedUnitSerializer, RecallSerializer

_PERM = "recall.recall.manage"
_VIEW = "recall.recall.view"


class RecallViewSet(AuditedModelViewSet):
    queryset = (
        Recall.objects.all().select_related("company", "initiated_by").order_by("-created_at")
    )
    serializer_class = RecallSerializer
    permission_map = {m: _PERM for m in ("POST", "PUT", "PATCH", "DELETE")}
    required_permission = _VIEW
    filterset_fields = ["company", "status", "severity"]
    search_fields = ["code", "reason", "notes"]

    def perform_update(self, serializer):
        recall = self.get_object()
        if recall.is_terminal:
            from apps.core.exceptions import BusinessRuleError

            raise BusinessRuleError(
                "A closed or cancelled recall cannot be edited.", code="recall_terminal"
            )
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if instance.is_terminal:
            from apps.core.exceptions import BusinessRuleError

            raise BusinessRuleError(
                "A closed or cancelled recall cannot be deleted.", code="recall_terminal"
            )
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        recall = self.get_object()
        to_status = request.data.get("status")
        if not to_status:
            from apps.core.exceptions import ValidationError

            raise ValidationError("A target status is required.", details={"status": ["Required."]})
        recall = services.transition(recall=recall, to_status=to_status, actor=request.user)
        return Response(self.get_serializer(recall).data)

    @action(detail=True, methods=["get"], url_path="exposure")
    def exposure(self, request, pk=None):
        recall = self.get_object()
        return Response(services.compute_exposure(recall))


class RecallAffectedUnitViewSet(AuditedModelViewSet):
    queryset = RecallAffectedUnit.objects.all().select_related("recall", "traceability_unit")
    serializer_class = RecallAffectedUnitSerializer
    permission_map = {m: _PERM for m in ("POST", "PUT", "PATCH", "DELETE")}
    required_permission = _VIEW
    company_scope_lookup = "recall__company"
    filterset_fields = ["recall", "traceability_unit"]
