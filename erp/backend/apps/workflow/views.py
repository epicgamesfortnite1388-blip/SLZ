from __future__ import annotations

from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.viewsets import AuditedModelViewSet
from apps.identity.permissions import HasPermission
from apps.workflow.models import (
    ApprovalStep,
    StepDecision,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowState,
)
from apps.workflow.services import cancel_workflow, record_decision


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDefinition
        fields = [
            "id",
            "code",
            "name_en",
            "name_fa",
            "approval_mode",
            "config",
            "is_active",
        ]


class ApprovalStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalStep
        fields = ["id", "sequence", "approver", "decision", "comment", "decided_at"]


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    steps = ApprovalStepSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowInstance
        fields = [
            "id",
            "definition",
            "entity_type",
            "entity_id",
            "state",
            "steps",
            "created_at",
        ]


class DecisionSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class WorkflowDefinitionViewSet(AuditedModelViewSet):
    """CRUD over approval-workflow *definitions* (engine configuration).

    Writes route through the audited service layer like every other master
    write, so creating/editing a definition lands in the audit trail
    (``entity_type`` ``workflow.WorkflowDefinition``). The definition only
    describes the approval *shape*; no business routing rule is hard-coded
    (do-not-build-yet #7).
    """

    queryset = WorkflowDefinition.objects.all()
    serializer_class = WorkflowDefinitionSerializer
    permission_map = {
        "POST": "workflow.definition.manage",
        "PUT": "workflow.definition.manage",
        "PATCH": "workflow.definition.manage",
        "DELETE": "workflow.definition.manage",
    }
    required_permission = "workflow.definition.view"
    company_scope_lookup = None


class WorkflowInstanceViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = WorkflowInstance.objects.all().select_related("definition").prefetch_related("steps")
    serializer_class = WorkflowInstanceSerializer
    permission_classes = [HasPermission]
    filterset_fields = ["state", "entity_type", "entity_id", "definition"]

    def get_permissions(self):
        """Authorize per action.

        ``decision`` is self-guarding (the service only lets an assigned,
        still-pending approver act) and ``mine`` only ever exposes the caller's
        own steps, so both require authentication only. Reading the full
        register requires ``workflow.instance.view``; cancelling another user's
        workflow requires ``workflow.instance.manage``. This keeps the generic
        engine usable by approvers without granting them the broad view/manage
        rights, and closes the prior gap where any authenticated user could
        cancel any workflow.
        """
        if self.action in ("decision", "mine"):
            self.required_permission = None
            self.allow_any_authenticated = True
        elif self.action == "cancel":
            self.required_permission = "workflow.instance.manage"
            self.allow_any_authenticated = False
        else:
            self.required_permission = "workflow.instance.view"
        self.permission_map = None
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        """The caller's personal approval inbox: open instances on which the
        requesting user still has a PENDING step."""
        qs = (
            self.get_queryset()
            .filter(
                state__in=[WorkflowState.SUBMITTED, WorkflowState.UNDER_REVIEW],
                steps__approver=request.user,
                steps__decision=StepDecision.PENDING,
            )
            .distinct()
        )
        page = self.paginate_queryset(qs)
        target = page if page is not None else qs
        serializer = self.get_serializer(target, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="decision")
    def decision(self, request, pk=None):
        instance = self.get_object()
        payload = DecisionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        instance = record_decision(
            instance=instance,
            approver=request.user,
            approve=payload.validated_data["approve"],
            comment=payload.validated_data.get("comment", ""),
        )
        return Response(WorkflowInstanceSerializer(instance).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        instance = self.get_object()
        instance = cancel_workflow(
            instance=instance,
            actor=request.user,
            reason=request.data.get("reason", ""),
        )
        return Response(WorkflowInstanceSerializer(instance).data)
