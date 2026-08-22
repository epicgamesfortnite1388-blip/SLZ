"""HasPermission must fail closed when a view declares no permission.

Regression guard: previously an undeclared ``required_permission`` silently
granted every authenticated user access. Views must now declare a permission
or explicitly opt in with ``allow_any_authenticated = True``.
"""

from __future__ import annotations

from django.test import TestCase

from apps.core.tests.factories import auth_client, make_user
from apps.identity.permissions import HasPermission


class _UndeclaredView:
    permission_classes = [HasPermission]


class _OptInView(_UndeclaredView):
    allow_any_authenticated = True


class FailClosedPermissionTests(TestCase):
    def setUp(self):
        self.user = make_user()
        # Deliberately NO permissions granted.
        self.client = auth_client(self.user)

    def test_undeclared_permission_denies_authenticated_user(self):
        response = self.client.get("/api/v1/workflow/instances/")
        self.assertEqual(response.status_code, 403, response.content)

    def test_opt_in_view_still_allows_authenticated_user(self):
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = Request(factory.get("/"))
        request.user = self.user

        view = _OptInView()
        self.assertTrue(HasPermission().has_permission(request, view))

        undeclared = _UndeclaredView()
        self.assertFalse(HasPermission().has_permission(request, undeclared))
