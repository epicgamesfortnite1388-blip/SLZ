"""Thin viewsets for Product Engineering (audited via ``AuditedModelViewSet``).

Specification *creation* and *activation* delegate to
``apps.engineering.services`` so the versioning lifecycle stays in one place;
everything else is standard audited CRUD. Child rows (layers/colors/parameters)
are editable only while their revision is DRAFT (enforced in serializers).
"""

from __future__ import annotations

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.viewsets import AuditedModelViewSet
from apps.engineering import services
from apps.engineering.models import (
    CustomerProduct,
    SpecColor,
    SpecificationRevision,
    SpecLayer,
    SpecParameter,
    ToolingAsset,
)
from apps.engineering.serializers import (
    CustomerProductSerializer,
    SpecColorSerializer,
    SpecificationRevisionSerializer,
    SpecLayerSerializer,
    SpecParameterSerializer,
    ToolingAssetSerializer,
)


class CustomerProductViewSet(AuditedModelViewSet):
    queryset = CustomerProduct.objects.all().select_related(
        "company", "customer", "product_group", "family", "base_uom"
    )
    serializer_class = CustomerProductSerializer
    permission_map = {
        "POST": "engineering.customerproduct.manage",
        "PUT": "engineering.customerproduct.manage",
        "PATCH": "engineering.customerproduct.manage",
        "DELETE": "engineering.customerproduct.manage",
    }
    required_permission = "engineering.customerproduct.view"
    filterset_fields = ["company", "customer", "product_group", "family", "is_active"]
    search_fields = ["code", "name_fa", "name_en"]


class SpecificationRevisionViewSet(AuditedModelViewSet):
    queryset = SpecificationRevision.objects.all().select_related("root")
    serializer_class = SpecificationRevisionSerializer
    permission_map = {
        "POST": "engineering.specification.manage",
        "PUT": "engineering.specification.manage",
        "PATCH": "engineering.specification.manage",
        "DELETE": "engineering.specification.manage",
    }
    required_permission = "engineering.specification.view"
    filterset_fields = ["root", "status", "spec_format", "print_process"]

    def perform_create(self, serializer):
        actor = getattr(self.request, "user", None)
        data = dict(serializer.validated_data)
        root = data.pop("root")
        revision = services.create_specification_draft(root=root, actor=actor, **data)
        serializer.instance = revision

    def perform_update(self, serializer):
        # Header edits are allowed only while the revision is DRAFT.
        services.assert_revision_editable(self.get_object())
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        services.assert_revision_editable(instance)
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        revision = self.get_object()
        services.activate_specification(revision, actor=request.user)
        return Response(self.get_serializer(revision).data)


class _SpecChildViewSet(AuditedModelViewSet):
    """Base for spec child-row viewsets.

    Serializers already reject *attaching/moving* a child to a non-DRAFT
    revision (create/update), but DELETE does not run serializer validation.
    Without this guard a child row of an ACTIVE/SUPERSEDED (immutable) revision
    could be soft-deleted, silently mutating a frozen specification. Deletes are
    therefore gated by the same ``assert_revision_editable`` rule.
    """

    def perform_destroy(self, instance):
        services.assert_revision_editable(instance.revision)
        super().perform_destroy(instance)


class SpecLayerViewSet(_SpecChildViewSet):
    queryset = SpecLayer.objects.all().select_related("revision", "material")
    serializer_class = SpecLayerSerializer
    permission_map = {
        "POST": "engineering.specification.manage",
        "PUT": "engineering.specification.manage",
        "PATCH": "engineering.specification.manage",
        "DELETE": "engineering.specification.manage",
    }
    required_permission = "engineering.specification.view"
    filterset_fields = ["revision", "material", "function"]


class SpecColorViewSet(_SpecChildViewSet):
    queryset = SpecColor.objects.all().select_related("revision", "ink", "alternative_ink")
    serializer_class = SpecColorSerializer
    permission_map = {
        "POST": "engineering.specification.manage",
        "PUT": "engineering.specification.manage",
        "PATCH": "engineering.specification.manage",
        "DELETE": "engineering.specification.manage",
    }
    required_permission = "engineering.specification.view"
    filterset_fields = ["revision", "ink"]


class SpecParameterViewSet(_SpecChildViewSet):
    queryset = SpecParameter.objects.all().select_related("revision")
    serializer_class = SpecParameterSerializer
    permission_map = {
        "POST": "engineering.specification.manage",
        "PUT": "engineering.specification.manage",
        "PATCH": "engineering.specification.manage",
        "DELETE": "engineering.specification.manage",
    }
    required_permission = "engineering.specification.view"
    filterset_fields = ["revision", "datatype", "key"]


class ToolingAssetViewSet(AuditedModelViewSet):
    """Cliché / sheet / set tooling assets (SR-03) — audited CRUD + lifecycle.

    Standard audited CRUD for the confirmed identity + usage-life fields; the
    ``status`` flip is done through the ``retire``/``reactivate`` actions so it
    is guarded and audited (EntityUpdated) rather than free-form PATCHable.
    """

    queryset = ToolingAsset.objects.all().select_related(
        "company", "customer", "customer_product", "warehouse"
    )
    serializer_class = ToolingAssetSerializer
    permission_map = {
        "POST": "engineering.tooling.manage",
        "PUT": "engineering.tooling.manage",
        "PATCH": "engineering.tooling.manage",
        "DELETE": "engineering.tooling.manage",
    }
    required_permission = "engineering.tooling.view"
    filterset_fields = [
        "company",
        "customer",
        "customer_product",
        "tooling_type",
        "status",
        "warehouse",
    ]
    search_fields = ["code", "name_fa", "name_en"]

    @action(detail=True, methods=["post"], url_path="retire")
    def retire(self, request, pk=None):
        asset = services.retire_tooling(self.get_object(), actor=request.user)
        return Response(self.get_serializer(asset).data)

    @action(detail=True, methods=["post"], url_path="reactivate")
    def reactivate(self, request, pk=None):
        asset = services.reactivate_tooling(self.get_object(), actor=request.user)
        return Response(self.get_serializer(asset).data)
