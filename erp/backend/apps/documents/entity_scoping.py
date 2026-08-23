"""Resolve the owning company of a generic (entity_type, entity_id) reference.

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
