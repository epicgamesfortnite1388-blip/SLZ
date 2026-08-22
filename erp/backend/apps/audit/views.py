"""Read-only audit API."""

from __future__ import annotations

from rest_framework import mixins, serializers, viewsets

from apps.audit.models import AuditLog
from apps.identity.permissions import require_permission


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "timestamp",
            "actor",
            "actor_label",
            "action",
            "entity_type",
            "entity_id",
            "before_state",
            "after_state",
            "correlation_id",
            "metadata",
        ]


class AuditLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Audit is append-only; the API exposes read access only."""

    queryset = AuditLog.objects.all().select_related("actor")
    serializer_class = AuditLogSerializer
    permission_classes = [require_permission("audit.log.view")]
    filterset_fields = ["action", "entity_type", "entity_id", "actor", "correlation_id"]
    ordering_fields = ["timestamp", "action"]
    search_fields = ["entity_type", "entity_id", "actor_label"]
