"""Planning viewsets — reorder-policy CRUD + the read-only planning run."""

from __future__ import annotations

from dataclasses import asdict

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.viewsets import AuditedModelViewSet
from apps.planning import services
from apps.planning.models import PlanningPolicy
from apps.planning.serializers import PlanningPolicySerializer


class PlanningPolicyViewSet(AuditedModelViewSet):
    queryset = PlanningPolicy.objects.all().select_related(
        "company", "warehouse", "material", "customer_product", "preferred_supplier"
    )
    serializer_class = PlanningPolicySerializer
    permission_map = {
        "POST": "planning.policy.manage",
        "PUT": "planning.policy.manage",
        "PATCH": "planning.policy.manage",
        "DELETE": "planning.policy.manage",
    }
    required_permission = "planning.policy.view"
    filterset_fields = ["company", "warehouse", "material", "customer_product", "is_active"]

    def get_permissions(self):
        if self.action == "run":
            self.required_permission = "planning.suggestion.view"
            self.permission_map = None
        else:
            self.required_permission = "planning.policy.view"
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="run")
    def run(self, request):
        """Run the planning engine for the current company (optional warehouse)."""
        company_id = getattr(request, "company_id", None)
        from apps.organization.models import Company

        if company_id is None:
            if request.user.is_superuser:
                company = Company.objects.first()
            else:
                memberships = list(request.user.company_memberships.all())
                company = memberships[0].company if memberships else None
        else:
            company = Company.objects.filter(pk=company_id).first()
        if company is None:
            return Response({"rows": [], "summary": services.summary_rows([])})

        warehouse = request.query_params.get("warehouse")
        warehouse_obj = None
        if warehouse:
            from apps.inventory.models import Warehouse

            warehouse_obj = Warehouse.objects.filter(pk=warehouse, company=company).first()
        rows = services.run_planning(company, warehouse=warehouse_obj)
        return Response(
            {
                "rows": [asdict(r) for r in rows],
                "summary": services.summary_rows(rows),
            }
        )
