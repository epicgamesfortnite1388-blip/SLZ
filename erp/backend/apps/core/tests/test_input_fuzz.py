"""Input fuzz regression tests: malformed identifiers, filters, pagination.

Pins the platform's behavior under hostile/malformed input so refactors of the
handler, pagination, or router layers cannot silently turn these into 500s:

* malformed / numeric / empty / nonexistent pks on detail endpoints resolve to
  the standard 404 ``NotFoundError`` envelope (never a raw 500 or HTML error);
* invalid filterset values produce a clean 400 ``ValidationError``;
* hostile search/ordering values are inert;
* pagination clamps ``page_size`` to the configured maximum.
"""

from __future__ import annotations

from django.test import TestCase

from apps.core.tests.factories import auth_client, grant, make_user

_VIEW_PERMS = [
    "organization.company.view",
    "partners.partner.view",
    "sales.order.view",
    "procurement.order.view",
    "production.order.view",
]

MALFORMED_PKS = ["not-a-uuid", "123", "%20", "../../etc/passwd"]


class DetailIdentifierFuzzTests(TestCase):
    """Detail endpoints must 404 (enveloped) on any unresolvable identifier."""

    def setUp(self):
        self.user = make_user()
        grant(self.user, *_VIEW_PERMS)
        self.client = auth_client(self.user)

    def _assert_not_found_envelope(self, url):
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404, url)
        body = resp.json()
        self.assertEqual(body["error"]["type"], "NotFoundError")
        self.assertIn("correlation_id", body["error"])

    def test_malformed_identifiers_across_modules_return_enveloped_404(self):
        bases = [
            "/api/v1/organization/companies/",
            "/api/v1/partners/partners/",
            "/api/v1/sales/orders/",
            "/api/v1/procurement/orders/",
            "/api/v1/production/orders/",
        ]
        for base in bases:
            for bad in MALFORMED_PKS:
                with self.subTest(base=base, pk=bad):
                    self._assert_not_found_envelope(f"{base}{bad}/")

    def test_nonexistent_but_valid_uuid_returns_enveloped_404(self):
        self._assert_not_found_envelope(
            "/api/v1/organization/companies/00000000-0000-0000-0000-000000000000/"
        )


class ListParameterFuzzTests(TestCase):
    """List endpoints must reject or neutralize hostile query parameters."""

    def setUp(self):
        self.user = make_user()
        grant(self.user, *_VIEW_PERMS)
        self.client = auth_client(self.user)
        self.url = "/api/v1/sales/orders/"

    def test_invalid_filterset_value_is_a_clean_400(self):
        resp = self.client.get(self.url, {"status": "HACKED"})
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertEqual(body["error"]["type"], "ValidationError")
        self.assertIn("status", body["error"]["details"])

    def test_injection_shaped_search_and_ordering_are_inert(self):
        resp = self.client.get(self.url, {"search": "' OR 1=1--"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["results"], [])
        resp = self.client.get(self.url, {"ordering": ";-DROP TABLE audit_log;--"})
        self.assertEqual(resp.status_code, 200)

    def test_page_size_is_clamped_to_the_configured_maximum(self):
        resp = self.client.get(self.url, {"page_size": 100000})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["page_size"], 200)

    def test_zero_page_size_falls_back_to_the_default(self):
        resp = self.client.get(self.url, {"page_size": 0})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["page_size"], 25)

    def test_out_of_range_pages_return_enveloped_404(self):
        for page in ("-1", "999999"):
            with self.subTest(page=page):
                resp = self.client.get(self.url, {"page": page})
                self.assertEqual(resp.status_code, 404)
                self.assertEqual(resp.json()["error"]["type"], "NotFoundError")
