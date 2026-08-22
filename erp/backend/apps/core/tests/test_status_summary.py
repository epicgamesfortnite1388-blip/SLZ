"""Status-summary report tests (order book counts).

The ``StatusSummaryMixin`` exposes ``GET <prefix>/summary/`` on the four
transactional document views. It only counts rows that exist — no status
semantics are introduced. These tests pin: aggregation over real rows,
zero-filling of every declared choice, query-param filtering parity with the
list endpoint, and each module's ``*.view`` RBAC gate.
"""

from __future__ import annotations

from django.test import TestCase

from apps.core.tests.factories import auth_client, grant, make_company, make_site, make_user
from apps.partners.models import Customer, Partner

ENDPOINTS = {
    "sales": ("sales.order.view", "/api/v1/sales/orders/summary/"),
    "purchase_order": ("procurement.order.view", "/api/v1/procurement/orders/summary/"),
    "requisition": (
        "procurement.requisition.view",
        "/api/v1/procurement/requisitions/summary/",
    ),
    "production": ("production.order.view", "/api/v1/production/orders/summary/"),
}


class StatusSummaryTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.site = make_site(company=self.company)
        # User created after the company so the factory's default membership
        # covers it (Q-055 scoping).
        self.user = make_user()

    def _make_sales_orders(self):
        """Two sales orders in different statuses, persisted directly."""
        from apps.sales.models import SalesOrder

        partner = Partner.objects.create(
            company=self.company, code="C-SUM", name_fa="مشتری", is_customer=True
        )
        customer = Customer.objects.create(partner=partner)
        so1 = SalesOrder.objects.create(
            company=self.company,
            site=self.site,
            customer=customer,
            number="SO-SUM-000001",
            status="DRAFT",
        )
        so2 = SalesOrder.objects.create(
            company=self.company,
            site=self.site,
            customer=customer,
            number="SO-SUM-000002",
            status="CONFIRMED",
        )
        return so1, so2

    def test_sales_summary_counts_real_rows_and_zero_fills_choices(self):
        self._make_sales_orders()
        grant(self.user, ENDPOINTS["sales"][0])
        resp = auth_client(self.user).get(ENDPOINTS["sales"][1])
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertEqual(body["total"], 2)
        self.assertEqual(body["by_status"]["DRAFT"], 1)
        self.assertEqual(body["by_status"]["CONFIRMED"], 1)
        # Every declared status choice is present, zero-filled.
        self.assertIn("CLOSED", body["by_status"])
        self.assertEqual(body["by_status"]["CLOSED"], 0)
        self.assertEqual(sum(body["by_status"].values()), body["total"])

    def test_summary_honours_the_same_filters_as_the_list(self):
        self._make_sales_orders()
        grant(self.user, ENDPOINTS["sales"][0])
        resp = auth_client(self.user).get(ENDPOINTS["sales"][1], {"status": "DRAFT"})
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["by_status"]["DRAFT"], 1)

    def test_each_summary_endpoint_is_gated_by_its_module_view_permission(self):
        for module, (_perm, url) in ENDPOINTS.items():
            with self.subTest(module=module):
                resp = auth_client(self.user).get(url)
                self.assertEqual(resp.status_code, 403)

    def test_remaining_document_summaries_are_wired(self):
        """PO / PR / production summaries respond zero-filled once permitted."""
        grant(self.user, *[perm for perm, _ in ENDPOINTS.values()])
        client = auth_client(self.user)
        for module, (_perm, url) in ENDPOINTS.items():
            if module == "sales":
                continue
            with self.subTest(module=module):
                resp = client.get(url)
                self.assertEqual(resp.status_code, 200, resp.content)
                body = resp.json()
                self.assertEqual(body["total"], 0)
                self.assertTrue(all(v == 0 for v in body["by_status"].values()))
