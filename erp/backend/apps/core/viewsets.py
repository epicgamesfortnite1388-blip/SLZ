"""Shared DRF viewset bases for master data.

``AuditedModelViewSet`` wires every create/update/delete through
``apps.core.service`` so master-data mutations are transactional and audited
without each module re-implementing the plumbing. Views stay thin: validation
lives in serializers/model ``clean``; the write boundary lives here.

Company isolation (Q-055): non-superusers only ever see rows whose company is
among their memberships. ``company_scope_lookup`` states the ORM path from the
viewset's model to ``organization.Company`` (override for child models such as
lines, or set ``None`` for models with no company dimension). Writes that would
place a record outside the caller's memberships are rejected **before** save.
"""

from __future__ import annotations

from django.db.models import Count, Q
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
    already exist.
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
    permission_classes = [HasPermission]

    #: ORM lookup from this model to ``organization.Company``; ``None`` marks a
    #: model with no company dimension (platform/global surfaces).
    company_scope_lookup: str | None = "company"

    def _member_company_ids(self) -> set:
        user = self.request.user
        return set(user.company_memberships.values_list("company_id", flat=True))

    def _scoped_queryset(self):
        lookup = self.company_scope_lookup
        if lookup is None:
            return self.queryset
        user = self.request.user
        if not getattr(user, "is_authenticated", False):
            return self.queryset.none()
        if user.is_superuser:
            return self.queryset
        ids = self._member_company_ids()
        return self.queryset.filter(Q(**{f"{lookup}__in": ids})) if ids else self.queryset.none()

    def get_queryset(self):
        """Row-level company isolation: members see only their companies' rows;
        no memberships ⇒ nothing at all (fail closed)."""
        return self._scoped_queryset()

    def _assert_company_allowed(self, company_id) -> None:
        if company_id is None or self.request.user.is_superuser:
            return
        allowed = {str(i) for i in self._member_company_ids()}
        if str(company_id) not in allowed:
            from apps.core.exceptions import AuthorizationError

            raise AuthorizationError("The record belongs to another company.")

    @staticmethod
    def _walk_company_id(start_obj, segments):
        """Resolve ``a__b__company`` style paths through FK attributes."""
        obj = start_obj
        for seg in segments:
            if obj is None:
                return None
            obj = getattr(obj, seg, None)
        return obj.pk if obj is not None else None

    def _company_id_for(self, serializer=None, instance=None):
        """Company id for an in-flight write.

        Direct-company models: payload value wins, else the live instance.
        Indirect models: take the FIRST relation segment of the lookup from the
        payload (create) or live instance (update), then walk the remaining
        segments through the database.
        """
        lookup = self.company_scope_lookup
        if lookup is None:
            return None
        if "__" not in lookup:
            if serializer is not None:
                direct = self._payload_company_id(serializer)
                if direct is not None:
                    return direct
            return getattr(instance, "company_id", None)

        segments = lookup.split("__")
        first_obj = None
        if serializer is not None:
            first_obj = serializer.validated_data.get(segments[0])
        if first_obj is None and instance is not None:
            first_obj = getattr(instance, segments[0], None)
        return self._walk_company_id(first_obj, segments[1:])

    @staticmethod
    def _payload_company_id(serializer):
        """Company id out of validated data (instance or PK forms)."""
        company = serializer.validated_data.get("company")
        if company is None:
            return None
        return getattr(company, "pk", company)

    def perform_create(self, serializer):
        # Reject BEFORE anything is persisted.
        self._assert_company_allowed(self._company_id_for(serializer=serializer, instance=None))
        actor = getattr(self.request, "user", None)
        service.create_from_serializer(serializer, actor=actor)

    def perform_update(self, serializer):
        self._assert_company_allowed(
            self._company_id_for(serializer=serializer, instance=serializer.instance)
        )
        actor = getattr(self.request, "user", None)
        service.update_from_serializer(serializer, actor=actor)

    def perform_destroy(self, instance):
        self._assert_company_allowed(self._company_id_for(instance=instance))
        actor = getattr(self.request, "user", None)
        service.delete_instance(instance, actor=actor)
