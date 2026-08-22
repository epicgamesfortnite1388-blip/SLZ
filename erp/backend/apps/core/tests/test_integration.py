"""End-to-end integration test.

Exercises the full request pipeline in one flow:
authentication -> authorization (RBAC) -> DB write -> audit trail -> correlation
id propagation.
"""

from __future__ import annotations

from django.test import TestCase
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.core.tests.factories import grant, make_user
from apps.organization.models import Company


class EndToEndTests(TestCase):
    def test_full_request_pipeline(self):
        user = make_user(email="e2e@slz.test", password="pw12345678")
        grant(user, "organization.company.manage", "organization.company.view", "audit.log.view")

        client = APIClient()
        # 1. Authenticate via real login endpoint.
        login = client.post(
            "/api/v1/auth/login/",
            {"email": "e2e@slz.test", "password": "pw12345678"},
            format="json",
        )
        self.assertEqual(login.status_code, 200, login.content)
        access = login.json()["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        # 2. Authorized write with an explicit correlation id.
        create = client.post(
            "/api/v1/organization/companies/",
            {"code": "SLZ", "name_en": "Lafaf Zarrin", "name_fa": "لفاف زرین"},
            format="json",
            HTTP_X_CORRELATION_ID="corr-e2e-1",
        )
        self.assertEqual(create.status_code, 201, create.content)
        self.assertEqual(create["X-Correlation-ID"], "corr-e2e-1")

        # 3. DB write persisted.
        self.assertTrue(Company.objects.filter(code="SLZ").exists())

        # 4. Audit trail captured the login (correlation ids flow through).
        self.assertTrue(AuditLog.objects.filter(action="LOGIN").exists())

        # 5. Read back through the paginated list envelope.
        listing = client.get("/api/v1/organization/companies/")
        self.assertEqual(listing.status_code, 200)
        body = listing.json()
        for key in ("count", "total_pages", "page", "page_size", "results"):
            self.assertIn(key, body)
