"""HR minimal Employee master tests: API CRUD, uniqueness, RBAC, audit."""

from __future__ import annotations

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.core.tests.factories import auth_client, grant, make_company, make_site, make_user
from apps.hr.models import Employee


class EmployeeApiTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.site = make_site(company=self.company)
        self.user = make_user()
        grant(self.user, "hr.employee.view", "hr.employee.manage")
        self.client = auth_client(self.user)

    def _payload(self, **overrides):
        data = {
            "company": str(self.company.id),
            "site": str(self.site.id),
            "employee_code": "EMP-001",
            "first_name_fa": "علی",
            "last_name_fa": "رضایی",
            "job_title": "اپراتور",
        }
        data.update(overrides)
        return data

    def test_create_employee_persists_and_audits(self):
        resp = self.client.post("/api/v1/hr/employees/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        emp = Employee.objects.get(employee_code="EMP-001")
        self.assertEqual(emp.created_by_id, self.user.id)
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="hr.Employee",
                entity_id=str(emp.id),
            ).exists()
        )

    def test_employee_code_unique_per_company(self):
        self.client.post("/api/v1/hr/employees/", self._payload(), format="json")
        dup = self.client.post("/api/v1/hr/employees/", self._payload(), format="json")
        self.assertEqual(dup.status_code, 400, dup.content)


class EmployeePermissionTests(TestCase):
    def setUp(self):
        self.company = make_company()

    def test_view_only_user_cannot_create(self):
        user = make_user(email="viewer@slz.test")
        grant(user, "hr.employee.view")
        client = auth_client(user)
        resp = client.post(
            "/api/v1/hr/employees/",
            {
                "company": str(self.company.id),
                "employee_code": "E1",
                "first_name_fa": "الف",
                "last_name_fa": "ب",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_unpermitted_user_cannot_list(self):
        user = make_user(email="nobody@slz.test")
        client = auth_client(user)
        resp = client.get("/api/v1/hr/employees/")
        self.assertEqual(resp.status_code, 403, resp.content)
