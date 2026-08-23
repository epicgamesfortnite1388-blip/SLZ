"""One-shot patcher: point policy-test uploads at a real partner (Q-055)."""

from __future__ import annotations

import io
import os

TARGET = os.path.join(os.path.dirname(__file__), "apps", "documents", "tests", "test_documents_policy.py")

s = io.open(TARGET, encoding="utf-8").read()

old_setup = (
    "    def setUp(self):\n"
    "        self.user = make_user()\n"
)
new_setup = (
    "    def setUp(self):\n"
    "        self.company = make_company()\n"
    "        self.partner = Partner.objects.create(\n"
    '            company=self.company, code="P-9", name_fa="\u0634\u0631\u06cc\u06a9", is_customer=True\n'
    "        )\n"
    "        self.user = make_user()\n"
)
assert old_setup in s, "setup anchor missing"
s = s.replace(old_setup, new_setup, 1)

old_up = (
    '                "entity_type": "sales.SalesOrder",\n'
    '                "entity_id": "SO-9",\n'
)
new_up = (
    '                "entity_type": "partners.Partner",\n'
    '                "entity_id": str(self.partner.id),\n'
)
count = s.count(old_up)
assert count == 2, f"upload anchors: {count}"
s = s.replace(old_up, new_up)

old_imports = "from apps.core.tests.factories import auth_client, grant, make_user\n"
new_imports = (
    "from apps.core.tests.factories import auth_client, grant, make_company, make_user\n"
    "from apps.partners.models import Partner\n"
)
assert old_imports in s
s = s.replace(old_imports, new_imports, 1)

io.open(TARGET, "w", encoding="utf-8", newline="\n").write(s)
print("POLICY-PATCHED")
