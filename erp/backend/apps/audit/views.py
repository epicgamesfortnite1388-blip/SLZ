"""Read-only audit API — company-scoped (Q-055)."""

from __future__ import annotations

from rest_framework import serializers

from apps.audit.models import AuditLog
from apps.core.viewsets import AuditedModelViewSet
from apps.identity.permissions import require_permission


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "timestamp",
            "actor",
            "actor_label",
            "company",
            "action",
            "entity_type",
            "entity_id",
            "before_state",
            "after_state",
            "correlation_id",
            "metadata",
        ]


class AuditLogViewSet(AuditedModelViewSet):
    """Append-only audit trail — list and retrieve only.

    Company isolation: non-superusers only see audit entries belonging to
    their companies. Platform events (login/logout — company=NULL) are
    visible to all authenticated users.
    """

    http_method_names = ["get", "head", "options"]
    queryset = AuditLog.objects.all().select_related("actor", "company")
    serializer_class = AuditLogSerializer
    company_scope_lookup = "company"
    permission_classes = [require_permission("audit.log.view")]
    filterset_fields = [
        "action",
        "entity_type",
        "entity_id",
        "actor",
        "company",
        "correlation_id",
    ]
    ordering_fields = ["timestamp", "action"]
    search_fields = ["entity_type", "entity_id", "actor_label"]

    def get_queryset(self):
        """Return the user's company-scoped rows *plus* any platform-level
        (company=NULL) audit events, which are visible to all authenticated
        users."""
        qs = super().get_queryset()  # company-scoped rows
        # Include rows with no company (platform events) for all users.
        return qs | AuditLog.objects.filter(company__isnull=True).select_related("actor", "company")
