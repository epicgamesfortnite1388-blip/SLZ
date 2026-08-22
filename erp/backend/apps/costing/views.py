"""Costing API: read-only cost-layer history and WA valuation reports."""

from __future__ import annotations

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.viewsets import AuditedModelViewSet
from apps.costing import services
from apps.costing.models import CostLayer
from apps.costing.serializers import CostLayerSerializer


class CostLayerViewSet(AuditedModelViewSet):
    """Read-only cost layer history. Layers are posted by services, not by API."""

    http_method_names = ["get", "head", "options"]

    queryset = CostLayer.objects.all().select_related("company", "material")
    serializer_class = CostLayerSerializer
    required_permission = "costing.layer.view"
    permission_map = {}
    filterset_fields = ["company", "material", "layer_type", "date"]
    search_fields = ["reference_type", "notes"]

    def get_queryset(self):
        """Derived scoping: each cost layer's company must match the user."""
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            return qs
        ids = user.company_memberships.values_list("company_id", flat=True)
        return qs.filter(company_id__in=ids)

    def _resolve_company(self, request):
        """Pick the company from query param or single membership."""
        import uuid as uuid_module

        from apps.core.exceptions import AuthorizationError, ValidationError
        from apps.organization.models import Company

        user = request.user
        requested = request.query_params.get("company")
        member_ids = set(user.company_memberships.values_list("company_id", flat=True))
        if user.is_superuser and requested:
            try:
                return Company.objects.get(pk=uuid_module.UUID(requested))
            except (ValueError, Company.DoesNotExist):
                pass
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
            "Multiple companies available — pass ?company=<id>.",
            code="costing.company_required",
        )

    @action(detail=False, methods=["get"], url_path="wa-cost")
    def wa_cost(self, request):
        """Get the WA unit cost for one material as of a date."""
        company = self._resolve_company(request)
        material_id = request.query_params.get("material")
        as_of = request.query_params.get("as_of")
        from apps.catalog.models import Material

        material = Material.objects.filter(id=material_id, company=company).first()
        if material is None:
            from rest_framework import status as http_status

            return Response({"error": "Material not found."}, status=http_status.HTTP_404_NOT_FOUND)
        wa = services.wa_unit_cost(company=company, material=material, as_of_date=as_of)
        return Response(
            {"material_id": str(material.id), "wa_unit_cost": services._fmt(wa), "as_of": as_of}
        )

    @action(detail=False, methods=["get"], url_path="summary")
    def costing_summary(self, request):
        """Per-material valuation summary."""
        company = self._resolve_company(request)
        as_of = request.query_params.get("as_of")
        rows = services.cost_summary(company, as_of_date=as_of)
        return Response(rows)
