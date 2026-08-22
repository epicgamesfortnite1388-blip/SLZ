"""Thin viewset for the minimal Employee master (audited)."""

from __future__ import annotations

from apps.core.viewsets import AuditedModelViewSet
from apps.hr.models import Employee
from apps.hr.serializers import EmployeeSerializer


class EmployeeViewSet(AuditedModelViewSet):
    queryset = Employee.objects.all().select_related("company", "site", "department", "user")
    serializer_class = EmployeeSerializer
    permission_map = {m: "hr.employee.manage" for m in ("POST", "PUT", "PATCH", "DELETE")}
    required_permission = "hr.employee.view"
    filterset_fields = ["company", "site", "department", "is_active"]
    search_fields = [
        "employee_code",
        "first_name_fa",
        "last_name_fa",
        "first_name_en",
        "last_name_en",
        "job_title",
    ]
