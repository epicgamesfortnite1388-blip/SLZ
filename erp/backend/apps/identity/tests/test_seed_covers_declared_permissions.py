"""RBAC drift guard: every permission code declared on a viewset
(``required_permission`` / ``permission_map``) must exist in the canonical
seed catalogue (``PLATFORM_PERMISSIONS``).

A code that is declared but never seeded can never be granted, so any role —
including Admin — would get 403 on that endpoint. This usually goes unnoticed
until runtime because tests typically grant codes ad hoc. This test fails at
CI time instead.
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

from django.apps import apps
from django.test import TestCase

from apps.identity.management.commands.seed_rbac import PLATFORM_PERMISSIONS


def _declared_permission_codes() -> set[str]:
    """Collect permission codes declared across every ``apps.*.views`` module."""
    codes: set[str] = set()
    for config in apps.get_app_configs():
        if not config.name.startswith("apps."):
            continue
        module_path = Path(config.path) / "views.py"
        if not module_path.exists():
            continue
        module = importlib.import_module(f"{config.name}.views")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            required = getattr(obj, "required_permission", None)
            if isinstance(required, str):
                codes.add(required)
            permission_map = getattr(obj, "permission_map", None)
            if isinstance(permission_map, dict):
                for code in permission_map.values():
                    if isinstance(code, str):
                        codes.add(code)
    return codes


class SeedCoversDeclaredPermissionsTests(TestCase):
    def test_every_declared_code_exists_in_the_seed_catalogue(self):
        seeded = {code for code, _en, _fa in PLATFORM_PERMISSIONS}
        declared = _declared_permission_codes()
        self.assertTrue(
            declared,
            "No declared permission codes found — the scan regressed.",
        )
        unseeded = sorted(declared - seeded)
        self.assertEqual(
            [],
            unseeded,
            "Permission codes declared on viewsets but absent from "
            "seed_rbac.PLATFORM_PERMISSIONS (they can never be granted): "
            f"{unseeded}",
        )

    def test_declared_codes_keep_the_module_resource_action_shape(self):
        for code in sorted(_declared_permission_codes()):
            parts = code.split(".")
            self.assertEqual(
                3,
                len(parts),
                f"Permission code '{code}' does not follow "
                "module.resource.action; HasPermission and the admin UI "
                "group by module.",
            )
