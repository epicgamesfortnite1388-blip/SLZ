"""One-shot applier for attachment cross-company isolation (Q-055).

Applies every file change for the fix in one process so concurrent editor
buffers cannot revert individual pieces between steps. Idempotent per file.
"""

from __future__ import annotations

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(BASE, "apps", "documents")


def read(p: str) -> str:
    return io.open(p, encoding="utf-8").read()


def write(p: str, s: str) -> None:
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def must_replace(path: str, old: str, new: str, tag: str) -> None:
    s = read(path)
    if new in s and old not in s:
        print(f"[{tag}] already applied")
        return
    if old not in s:
        raise SystemExit(f"[{tag}] ANCHOR NOT FOUND in {path}")
    write(path, s.replace(old, new, 1))
    print(f"[{tag}] applied")


# ---------------------------------------------------------------- entity_scoping
SCOPING = '''"""Resolve the owning company of a generic (entity_type, entity_id) reference.

The attachment register is generic: rows point at any business entity via a
dotted type label plus UUID. Q-055 company isolation therefore cannot be a
simple FK filter -- the target's company must be resolved through the same
relationship chain the scoped viewsets use.

Only entity types listed in ``ENTITY_COMPANY_PATHS`` are accepted for upload;
anything else is rejected rather than silently stored unscoped (fail closed).
"""

from __future__ import annotations

from typing import Optional

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db.models import Model

from apps.core.exceptions import NotFoundError, ValidationError

# entity_type -> (model "app.Model", attribute walk from the instance to the
# company pk). Keep in sync with the viewsets' company_scope_lookup values.
ENTITY_COMPANY_PATHS: dict[str, tuple[str, str]] = {
    "partners.Partner": ("partners.Partner", "company_id"),
    "sales.SalesOrder": ("sales.SalesOrder", "company_id"),
    "procurement.PurchaseOrder": ("procurement.PurchaseOrder", "company_id"),
    "procurement.PurchaseRequisition": ("procurement.PurchaseRequisition", "company_id"),
    "production.ProductionOrder": ("production.ProductionOrder", "company_id"),
    "engineering.CustomerProduct": ("engineering.CustomerProduct", "company_id"),
    "engineering.ToolingAsset": ("engineering.ToolingAsset", "company_id"),
    "manufacturing.BillOfMaterials": (
        "manufacturing.BillOfMaterials",
        "spec_revision__root__company_id",
    ),
    "manufacturing.Routing": ("manufacturing.Routing", "spec_revision__root__company_id"),
    "quality.QualityPlan": ("quality.QualityPlan", "spec_revision__root__company_id"),
}


def resolve_company_id(entity_type: str, entity_id: str) -> Optional[int]:
    """Company pk owning ``entity_id``, or ``None`` when the type is unknown."""
    entry = ENTITY_COMPANY_PATHS.get(entity_type)
    if entry is None:
        raise ValidationError(
            f"Attachments cannot be pinned to '{entity_type}'.",
            code="documents.entity.unsupported",
            details={"allowed": sorted(ENTITY_COMPANY_PATHS)},
        )
    model_path, walk = entry
    try:
        obj = apps.get_model(*model_path.split(".")).objects.get(pk=entity_id)
    except (ObjectDoesNotExist, ValueError, TypeError, DjangoValidationError) as exc:
        # DjangoValidationError covers UUIDField's "not a valid UUID" error,
        # which is not a ValueError subclass; all map to a clean 404.
        raise NotFoundError("The referenced record does not exist.") from exc

    current = obj
    for segment in walk.split("__"):
        current = getattr(current, segment)
    return current
'''

write(os.path.join(DOCS, "entity_scoping.py"), SCOPING)
print("[entity_scoping] written")

# ---------------------------------------------------------------------- models
MODELS = os.path.join(DOCS, "models.py")
must_replace(
    MODELS,
    "    entity_id = models.CharField(max_length=64, db_index=True)\n"
    '    original_filename = models.CharField(max_length=255)',
    "    entity_id = models.CharField(max_length=64, db_index=True)\n"
    "    # Resolved from the referenced entity at upload time (Q-055 company\n"
    "    # isolation); unresolvable targets are rejected at upload.\n"
    '    company = models.ForeignKey(\n'
    '        "organization.Company",\n'
    "        null=True,\n"
    "        blank=True,\n"
    "        on_delete=models.PROTECT,\n"
    '        related_name="attachments",\n'
    "    )\n"
    '    original_filename = models.CharField(max_length=255)',
    "models",
)

# ----------------------------------------------------------------------- views
VIEWS = os.path.join(DOCS, "views.py")

must_replace(
    VIEWS,
    '"""Document upload / metadata / secure download API."""',
    '"""Document upload / metadata / secure download API.\n'
    "\n"
    "Q-055: attachments inherit the company of the entity they are pinned to. The\n"
    "target must be an attachable type, must exist, and must belong to one of the\n"
    "caller's companies; listing/download/delete are scoped to the same set (fail\n"
    "closed for unscoped legacy rows).\n"
    '"""',
    "views.docstring",
)

must_replace(
    VIEWS,
    "from django.core.files.base import ContentFile\n",
    "from django.core.files.base import ContentFile\n"
    "from django.db.models import Q\n",
    "views.Q-import",
)

must_replace(
    VIEWS,
    "from apps.documents.entity_scoping import resolve_company_id\n",
    "",
    "views.resolver-import(noop)",
)
s = read(VIEWS)
if "resolve_company_id" not in s:
    must_replace(
        VIEWS,
        "from apps.documents.models import Attachment\n",
        "from apps.documents.entity_scoping import resolve_company_id\n"
        "from apps.documents.models import Attachment\n",
        "views.resolver-import",
    )

GET_QS_NEW = (
    "    parser_classes = [MultiPartParser, FormParser]\n"
    "\n"
    "    def get_queryset(self):\n"
    '        """Company-isolated attachment register (Q-055). Rows without a\n'
    "        resolvable company are invisible to non-superusers (fail closed).\"\"\"\n"
    "        qs = self.queryset.all()\n"
    "        user = self.request.user\n"
    '        if not getattr(user, "is_authenticated", False):\n'
    "            return qs.none()\n"
    "        if user.is_superuser:\n"
    "            return qs\n"
    '        ids = set(user.company_memberships.values_list("company_id", flat=True))\n'
    "        return qs.filter(Q(company_id__in=ids)) if ids else qs.none()\n"
)
must_replace(
    VIEWS,
    "    parser_classes = [MultiPartParser, FormParser]\n",
    GET_QS_NEW,
    "views.get_queryset",
)

CONTAIN_OLD = (
    "        uploaded = payload[\"file\"]\n"
    "\n"
    "        validate_upload(uploaded)\n"
)
CONTAIN_NEW = (
    "        uploaded = payload[\"file\"]\n"
    "\n"
    "        # Resolve the target's company BEFORE touching storage: unknown types\n"
    "        # and foreign-company targets are rejected outright (Q-055).\n"
    '        company_id = resolve_company_id(payload["entity_type"], payload["entity_id"])\n'
    "        if not request.user.is_superuser:\n"
    "            allowed = {\n"
    "                str(i)\n"
    '                for i in request.user.company_memberships.values_list("company_id", flat=True)\n'
    "            }\n"
    "            if str(company_id) not in allowed:\n"
    "                from apps.core.exceptions import AuthorizationError\n"
    "\n"
    '                raise AuthorizationError("The target record belongs to another company.")\n'
    "\n"
    "        validate_upload(uploaded)\n"
)
must_replace(VIEWS, CONTAIN_OLD, CONTAIN_NEW, "views.containment")

STAMP_OLD = (
    '            entity_id=payload["entity_id"],\n'
    "            original_filename=uploaded.name,"
)
STAMP_NEW = (
    '            entity_id=payload["entity_id"],\n'
    "            company_id=company_id,\n"
    "            original_filename=uploaded.name,"
)
must_replace(VIEWS, STAMP_OLD, STAMP_NEW, "views.stamp")

print("ALL APPLIED")
