"""Thin viewsets for Manufacturing — BOM & Routing (audited via
``AuditedModelViewSet``).

BOM/Routing revision *creation* and *activation* delegate to
``apps.manufacturing.services`` so the (shared) versioning lifecycle stays in
one place; everything else is standard audited CRUD. Child rows
(bom lines / routing operations) are editable only while their revision is
DRAFT (enforced in serializers). Mirrors ``apps.engineering.views``.
"""

from __future__ import annotations

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.viewsets import AuditedModelViewSet
from apps.manufacturing import services
from apps.manufacturing.models import (
    BillOfMaterials,
    BomLine,
    BomRevision,
    Machine,
    Routing,
    RoutingOperation,
    RoutingRevision,
    WorkCenter,
)
from apps.manufacturing.serializers import (
    BillOfMaterialsSerializer,
    BomLineSerializer,
    BomRevisionSerializer,
    MachineSerializer,
    RoutingOperationSerializer,
    RoutingRevisionSerializer,
    RoutingSerializer,
    WorkCenterSerializer,
)


class WorkCenterViewSet(AuditedModelViewSet):
    queryset = WorkCenter.objects.all().select_related("company", "site")
    serializer_class = WorkCenterSerializer
    permission_map = {
        "POST": "manufacturing.workcenter.manage",
        "PUT": "manufacturing.workcenter.manage",
        "PATCH": "manufacturing.workcenter.manage",
        "DELETE": "manufacturing.workcenter.manage",
    }
    required_permission = "manufacturing.workcenter.view"
    filterset_fields = ["company", "site", "is_active"]
    search_fields = ["code", "name_fa", "name_en"]


class MachineViewSet(AuditedModelViewSet):
    queryset = Machine.objects.all().select_related("company", "site", "work_center")
    serializer_class = MachineSerializer
    permission_map = {
        "POST": "manufacturing.machine.manage",
        "PUT": "manufacturing.machine.manage",
        "PATCH": "manufacturing.machine.manage",
        "DELETE": "manufacturing.machine.manage",
    }
    required_permission = "manufacturing.machine.view"
    filterset_fields = ["company", "site", "work_center", "is_active"]
    search_fields = ["code", "name_fa", "name_en"]


class BillOfMaterialsViewSet(AuditedModelViewSet):
    queryset = BillOfMaterials.objects.all().select_related("spec_revision", "output_material")
    serializer_class = BillOfMaterialsSerializer
    permission_map = {
        "POST": "manufacturing.bom.manage",
        "PUT": "manufacturing.bom.manage",
        "PATCH": "manufacturing.bom.manage",
        "DELETE": "manufacturing.bom.manage",
    }
    required_permission = "manufacturing.bom.view"
    filterset_fields = ["spec_revision", "output_material", "is_active"]


class BomRevisionViewSet(AuditedModelViewSet):
    queryset = BomRevision.objects.all().select_related("root")
    serializer_class = BomRevisionSerializer
    permission_map = {
        "POST": "manufacturing.bom.manage",
        "PUT": "manufacturing.bom.manage",
        "PATCH": "manufacturing.bom.manage",
        "DELETE": "manufacturing.bom.manage",
    }
    required_permission = "manufacturing.bom.view"
    filterset_fields = ["root", "status"]

    def perform_create(self, serializer):
        actor = getattr(self.request, "user", None)
        data = dict(serializer.validated_data)
        root = data.pop("root")
        revision = services.create_revision_draft(
            revision_model=BomRevision,
            entity_type="manufacturing.BomRevision",
            root=root,
            actor=actor,
            **data,
        )
        serializer.instance = revision

    def perform_update(self, serializer):
        services.assert_revision_editable(self.get_object())
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        services.assert_revision_editable(instance)
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        revision = self.get_object()
        services.activate_revision(
            revision=revision,
            entity_type="manufacturing.BomRevision",
            actor=request.user,
        )
        return Response(self.get_serializer(revision).data)


class BomLineViewSet(AuditedModelViewSet):
    queryset = BomLine.objects.all().select_related("revision", "material", "uom")
    serializer_class = BomLineSerializer
    permission_map = {
        "POST": "manufacturing.bom.manage",
        "PUT": "manufacturing.bom.manage",
        "PATCH": "manufacturing.bom.manage",
        "DELETE": "manufacturing.bom.manage",
    }
    required_permission = "manufacturing.bom.view"
    filterset_fields = ["revision", "material"]

    def perform_destroy(self, instance):
        # Serializers guard create/update; DELETE bypasses them, so gate it too.
        services.assert_revision_editable(instance.revision)
        super().perform_destroy(instance)


class RoutingViewSet(AuditedModelViewSet):
    queryset = Routing.objects.all().select_related("spec_revision")
    serializer_class = RoutingSerializer
    permission_map = {
        "POST": "manufacturing.routing.manage",
        "PUT": "manufacturing.routing.manage",
        "PATCH": "manufacturing.routing.manage",
        "DELETE": "manufacturing.routing.manage",
    }
    required_permission = "manufacturing.routing.view"
    filterset_fields = ["spec_revision", "is_active"]


class RoutingRevisionViewSet(AuditedModelViewSet):
    queryset = RoutingRevision.objects.all().select_related("root")
    serializer_class = RoutingRevisionSerializer
    permission_map = {
        "POST": "manufacturing.routing.manage",
        "PUT": "manufacturing.routing.manage",
        "PATCH": "manufacturing.routing.manage",
        "DELETE": "manufacturing.routing.manage",
    }
    required_permission = "manufacturing.routing.view"
    filterset_fields = ["root", "status"]

    def perform_create(self, serializer):
        actor = getattr(self.request, "user", None)
        data = dict(serializer.validated_data)
        root = data.pop("root")
        revision = services.create_revision_draft(
            revision_model=RoutingRevision,
            entity_type="manufacturing.RoutingRevision",
            root=root,
            actor=actor,
            **data,
        )
        serializer.instance = revision

    def perform_update(self, serializer):
        services.assert_revision_editable(self.get_object())
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        services.assert_revision_editable(instance)
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        revision = self.get_object()
        services.activate_revision(
            revision=revision,
            entity_type="manufacturing.RoutingRevision",
            actor=request.user,
        )
        return Response(self.get_serializer(revision).data)


class RoutingOperationViewSet(AuditedModelViewSet):
    queryset = RoutingOperation.objects.all().select_related(
        "revision", "work_center", "output_material"
    )
    serializer_class = RoutingOperationSerializer
    permission_map = {
        "POST": "manufacturing.routing.manage",
        "PUT": "manufacturing.routing.manage",
        "PATCH": "manufacturing.routing.manage",
        "DELETE": "manufacturing.routing.manage",
    }
    required_permission = "manufacturing.routing.view"
    filterset_fields = ["revision", "work_center"]

    def perform_destroy(self, instance):
        # Serializers guard create/update; DELETE bypasses them, so gate it too.
        services.assert_revision_editable(instance.revision)
        super().perform_destroy(instance)
