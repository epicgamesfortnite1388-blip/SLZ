"""SiteCapability tests: audited master-data write + uniqueness + RBAC."""

from __future__ import annotations

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.core.tests.factories import auth_client, grant, make_site, make_user
from apps.organization.models import SiteCapability


class SiteCapabilityApiTests(TestCase):
    def setUp(self):
        self.site = make_site()
        self.user = make_user()
        grant(
            self.user,
            "organization.sitecapability.view",
            "organization.sitecapability.manage",
        )
        self.client = auth_client(self.user)

    def test_create_capability_persists_and_audits(self):
        resp = self.client.post(
            "/api/v1/organization/site-capabilities/",
            {"site": str(self.site.id), "capability": "FLEXO_PRINTING"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        cap = SiteCapability.objects.get(site=self.site, capability="FLEXO_PRINTING")
        # SiteCapabilityViewSet routes writes through the audited service.
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="organization.SiteCapability",
                entity_id=str(cap.id),
            ).exists()
        )

    def test_capability_unique_per_site(self):
        SiteCapability.objects.create(site=self.site, capability="SLITTING")
        dup = self.client.post(
            "/api/v1/organization/site-capabilities/",
            {"site": str(self.site.id), "capability": "SLITTING"},
            format="json",
        )
        self.assertEqual(dup.status_code, 400, dup.content)


class SiteCapabilityPermissionTests(TestCase):
    def setUp(self):
        self.site = make_site()

    def test_view_only_user_cannot_create(self):
        user = make_user(email="viewer@slz.test")
        grant(user, "organization.sitecapability.view")
        client = auth_client(user)
        resp = client.post(
            "/api/v1/organization/site-capabilities/",
            {"site": str(self.site.id), "capability": "SLITTING"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403, resp.content)
