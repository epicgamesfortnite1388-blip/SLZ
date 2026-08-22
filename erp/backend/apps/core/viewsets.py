"""Shared DRF viewset bases for master data.

``AuditedModelViewSet`` wires every create/update/delete through
``apps.core.service`` so master-data mutations are transactional and audited
without each module re-implementing the plumbing. Views stay thin: validation
lives in serializers/model ``clean``; the write boundary lives here.
"""

from __future__ import annotations

from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core import service
from apps.identity.permissions import HasPermission


class StatusSummaryMixin:
    """Adds ``GET <prefix>/summary/`` — per-status counts for document views.

    Aggregates over the same filtered queryset the list endpoint exposes, so
    RBAC and any query-param filters apply identically. Every status choice the
    model declares is returned zero-filled, giving consumers a stable breakdown
    without inventing any business semantics — this only counts rows that
    already exist. Reports built on it (order book, dashboard strips) therefore
    depend solely on confirmed document state machines.
    """

    status_field = "status"

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request, *args, **kwargs):
        model = self.queryset.model
        field = model._meta.get_field(self.status_field)
        choices = [value for value, _label in getattr(field, "choices", None) or []]
        counts = dict(
            self.filter_queryset(self.get_queryset())
            .values_list(self.status_field)
            .annotate(total=Count("id"))
        )
        return Response(
            {
                "total": sum(counts.values()),
                "by_status": {choice: counts.get(choice, 0) for choice in choices},
            }
        )


class AuditedModelViewSet(viewsets.ModelViewSet):
    """``ModelViewSet`` whose writes emit lifecycle events (→ audit trail).

    Subclasses declare ``queryset``, ``serializer_class`` and the RBAC
    ``permission_map``/``required_permission`` exactly as the platform convention
    (``module.resource.action``).
    """

    permission_classes = [HasPermission]

    def perform_create(self, serializer):
        actor = getattr(self.request, "user", None)
        service.create_from_serializer(serializer, actor=actor)

    def perform_update(self, serializer):
        actor = getattr(self.request, "user", None)
        service.update_from_serializer(serializer, actor=actor)

    def perform_destroy(self, instance):
        actor = getattr(self.request, "user", None)
        service.delete_instance(instance, actor=actor)
