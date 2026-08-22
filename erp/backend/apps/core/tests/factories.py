"""Shared test helpers."""

from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from django.db import DEFAULT_DB_ALIAS, connections
from rest_framework.test import APIClient

from apps.identity.models import Permission, Role, RolePermission, UserRole

logger = logging.getLogger(__name__)

User = get_user_model()


class OnCommitExecutingClient(APIClient):
    """APIClient that executes ``transaction.on_commit`` callbacks.

    Under ``TestCase`` no real COMMIT occurs, so callbacks registered through
    ``atomic_with_events`` (audit trail, notifications) would never run. Each
    request's post-commit callbacks are drained exactly as the framework would
    after a real COMMIT, so side effects behave as in production.
    """

    def generic(
        self, method, path, data="", content_type="application/octet-stream", secure=False, **extra
    ):
        conn = connections[DEFAULT_DB_ALIAS]
        captured: list = []
        old = conn.run_on_commit
        conn.run_on_commit = captured
        try:
            response = super().generic(method, path, data, content_type, secure, **extra)
            while captured:
                batch_count = len(captured)
                for _sids, func, robust in captured:
                    if robust:
                        try:
                            func()
                        except Exception:
                            logger.exception("on_commit callback failed")
                    else:
                        func()
                del captured[:batch_count]
            return response
        finally:
            conn.run_on_commit = old


def make_user(email="user@slz.test", password="pass1234", **extra):
    return User.objects.create_user(email=email, password=password, **extra)


def make_superuser(email="admin@slz.test", password="pass1234"):
    return User.objects.create_superuser(email=email, password=password)


def grant(user, *permission_codes):
    # Each grant() call creates a role unique to this user so permissions never
    # leak between test users through a shared global role.
    existing = list(UserRole.objects.filter(user=user).values_list("role_id", flat=True))
    if not existing:
        role = Role.objects.create(
            code=f"test_role_{user.pk}",
            name_en="Test",
            name_fa="تست",
        )
        UserRole.objects.create(user=user, role=role)
    else:
        role = Role.objects.get(pk=existing[0])
    for code in permission_codes:
        perm, _ = Permission.objects.get_or_create(
            code=code, defaults={"module": code.split(".", 1)[0]}
        )
        RolePermission.objects.get_or_create(role=role, permission=perm)
    return role


def auth_client(user) -> APIClient:
    client = OnCommitExecutingClient()
    client.force_authenticate(user=user)
    return client


def make_company(code="SLZ", name_en="Lafaf Zarrin", name_fa="لفاف زرین"):
    from apps.organization.models import Company

    return Company.objects.create(code=code, name_en=name_en, name_fa=name_fa)


def make_site(company=None, code="TEH", name_en="Tehran", name_fa="تهران"):
    from apps.organization.models import Site

    company = company or make_company()
    return Site.objects.create(company=company, code=code, name_en=name_en, name_fa=name_fa)
