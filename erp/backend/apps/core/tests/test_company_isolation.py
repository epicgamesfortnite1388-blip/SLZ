"""Cross-company isolation regression tests (Q-055).

Confirmed policy: a user may belong to **multiple** companies; visibility is
company-granular; memberships are IT-administered. These tests pin the
enforcement contract on the shared base viewset:

* list/detail exclude other companies' rows (fail closed: no memberships ⇒
  nothing);
* writes that would place a row outside the caller's memberships are rejected;
* indirect children inherit isolation through their parent chain;
* creating a company makes its creator a member (bootstrap rule);
* superusers bypass scoping.
"""

from __future__ import annotations

from django.test import TestCase

from apps.core.tests.factories import auth_client, grant, make_company, make_site, make_user
from apps.identity.models import CompanyMembership


def _only_member_of(user, company) -> None:
    """Reduce ``user`` to a single-company membership."""
    CompanyMembership.objects.filter(user=user).exclude(company=company).delete()


class CrossCompanyIsolationTests(TestCase):
    """Company A user must never reach Company B records."""

    def setUp(self):
        # Company B first, so the Company-A user does NOT auto-join it.
        self.company_b = make_company(code="BBBB")
        self.company_a = make_company(code="AAAA")
        make_site(company=self.company_a)

        self.insider = make_user(email="a@slz.test")
        _only_member_of(self.insider, self.company_a)

        self.outsider_b = make_user(email="b@slz.test")
        _only_member_of(self.outsider_b, self.company_b)

    def _make_partner(self, company, code):
        from apps.partners.models import Partner

        return Partner.objects.create(company=company, code=code, name_fa="شریک", is_customer=True)

    def test_detail_of_foreign_record_returns_enveloped_404(self):
        partner_b = self._make_partner(self.company_b, "P-B")
        grant(self.insider, "partners.partner.view")
        resp = auth_client(self.insider).get(f"/api/v1/partners/partners/{partner_b.id}/")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"]["type"], "NotFoundError")

    def test_list_excludes_foreign_rows(self):
        self._make_partner(self.company_a, "P-A")
        self._make_partner(self.company_b, "P-B")
        grant(self.insider, "partners.partner.view")
        resp = auth_client(self.insider).get("/api/v1/partners/partners/")
        codes = [row["code"] for row in resp.json()["results"]]
        self.assertIn("P-A", codes)
        self.assertNotIn("P-B", codes)

    def test_update_of_foreign_record_is_rejected(self):
        partner_b = self._make_partner(self.company_b, "P-B")
        grant(self.insider, "partners.partner.view", "partners.partner.manage")
        resp = auth_client(self.insider).patch(
            f"/api/v1/partners/partners/{partner_b.id}/",
            {"name_en": "Hijacked"},
            format="json",
        )
        # Scoped queryset hides the row entirely ⇒ 404 (no existence leak).
        # 403 is equally acceptable if the object were resolvable.
        self.assertIn(resp.status_code, (403, 404))
        partner_b.refresh_from_db()
        self.assertNotEqual(partner_b.name_en, "Hijacked")

    def test_delete_of_foreign_record_is_rejected(self):
        partner_b = self._make_partner(self.company_b, "P-B")
        grant(self.insider, "partners.partner.manage")
        resp = auth_client(self.insider).delete(f"/api/v1/partners/partners/{partner_b.id}/")
        self.assertIn(resp.status_code, (403, 404))
        self.assertTrue(type(partner_b).all_objects.filter(pk=partner_b.pk).exists())

    def test_create_into_foreign_company_is_rejected(self):
        from apps.partners.models import Partner

        grant(self.insider, "partners.partner.manage")
        resp = auth_client(self.insider).post(
            "/api/v1/partners/partners/",
            {
                "company": str(self.company_b.id),
                "code": "P-X",
                "name_fa": "x",
                "is_customer": True,
            },
            format="json",
        )
        self.assertIn(resp.status_code, (403, 404), resp.content)
        self.assertFalse(Partner.objects.filter(code="P-X").exists())


class ChildLineIsolationTests(TestCase):
    """Lines inherit isolation through their parent order."""

    def setUp(self):
        self.company_b = make_company(code="BBBB")
        self.company_a = make_company(code="AAAA")
        from apps.identity.models import CompanyMembership
        from apps.partners.models import Customer, Partner

        partner_b = Partner.objects.create(
            company=self.company_b, code="C-B", name_fa="شریک ب", is_customer=True
        )
        customer_b = Customer.objects.create(partner=partner_b)
        from apps.sales.models import SalesOrder

        self.order_b = SalesOrder.objects.create(
            company=self.company_b,
            site=None,
            customer=customer_b,
            number="SO-ISO-1",
            status="DRAFT",
        )
        self.insider = make_user(email="a2@slz.test")
        CompanyMembership.objects.filter(user=self.insider).exclude(company=self.company_a).delete()

    def test_line_for_foreign_order_is_never_created(self):
        grant(self.insider, "sales.order.view", "sales.order.manage")
        resp = auth_client(self.insider).post(
            "/api/v1/sales/order-lines/",
            {"order": str(self.order_b.id), "sequence": 1, "quantity": "1"},
            format="json",
        )
        # Foreign order invisible ⇒ serializer cannot resolve it (400) or the
        # write is rejected outright (403/404). Never 2xx.
        self.assertIn(resp.status_code, (400, 403, 404))
        self.assertFalse(self.order_b.lines.exists())


class CompanyBootstrapRuleTests(TestCase):
    """Whoever creates a company becomes its first member."""

    def test_creator_gets_membership_and_sees_their_company(self):
        admin = make_user(email="creator@slz.test")
        grant(admin, "organization.company.view", "organization.company.manage")
        client = auth_client(admin)

        # The creator has no memberships yet → list is empty.
        self.assertEqual(client.get("/api/v1/organization/companies/").json()["count"], 0)

        created = client.post(
            "/api/v1/organization/companies/",
            {"code": "NEWCO", "name_en": "New Co", "name_fa": "جدید"},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.content)

        listing = client.get("/api/v1/organization/companies/").json()
        self.assertEqual(listing["count"], 1)
        self.assertEqual(listing["results"][0]["code"], "NEWCO")


class FailClosedTests(TestCase):
    """No memberships ⇒ nothing is visible, even with permissions granted."""

    def test_zero_membership_user_sees_nothing(self):
        from apps.identity.models import CompanyMembership

        make_company(code="ZZZ")
        user = make_user(email="nomember@slz.test")
        CompanyMembership.objects.filter(user=user).delete()
        grant(user, "organization.company.view")

        resp = auth_client(user).get("/api/v1/organization/companies/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 0)

    def test_superuser_bypasses_scoping(self):
        from apps.core.tests.factories import make_superuser

        make_company(code="ANY")
        admin = make_superuser()
        grant(admin, "organization.company.view")
        resp = auth_client(admin).get("/api/v1/organization/companies/")
        self.assertGreaterEqual(resp.json()["count"], 1)
