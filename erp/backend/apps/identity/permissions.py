"""RBAC permission classes for DRF.

Views declare a required permission code; ``HasPermission`` checks it against
the authenticated user's role-derived permissions, now scoped to the company
context from the ``X-SLZ-Company`` header (Q-055).  Superusers bypass. This is
the single choke point for authorization so business modules never re-implement
access logic.
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission


class HasPermission(BasePermission):
    """Require ``view.required_permission`` (a ``module.resource.action`` code).

    Views may also provide ``permission_map`` = {http_method: code} for
    per-verb requirements.

    Company-scoped RBAC (Q-055): if ``request.company_id`` is set (via the
    ``X-SLZ-Company`` header validated by ``CompanyContextMiddleware``), the
    permission check is scoped to that company — the user's global roles plus
    any roles assigned to that company are evaluated; roles assigned to
    *other* companies are excluded.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        code = None
        permission_map = getattr(view, "permission_map", None)
        if permission_map:
            code = permission_map.get(request.method)
        if code is None:
            code = getattr(view, "required_permission", None)
        if not code:
            # Fail closed: a view must either declare a permission or opt in to
            # authentication-only access with ``allow_any_authenticated = True``.
            # This prevents a forgotten declaration from silently exposing an
            # endpoint to every authenticated user.
            return bool(getattr(view, "allow_any_authenticated", False))
        company_id = getattr(request, "company_id", None)
        return user.has_permission_code(code, company_id=company_id)


def require_permission(code: str):
    """Factory building a permission class bound to a single code.

    Usage: ``permission_classes = [require_permission("identity.role.manage")]``.
    """

    class _Bound(HasPermission):
        def has_permission(self, request, view) -> bool:
            user = request.user
            if not user or not user.is_authenticated:
                return False
            if user.is_superuser:
                return True
            company_id = getattr(request, "company_id", None)
            return user.has_permission_code(code, company_id=company_id)

    _Bound.__name__ = f"RequirePermission_{code.replace('.', '_')}"
    return _Bound
