"""Document upload / metadata / secure download API.

Q-055: attachments inherit the company of the entity they are pinned to. The
target must be an attachable type (see ``ENTITY_COMPANY_PATHS``), must exist,
and must belong to one of the caller's companies; listing/download/delete are
scoped to the same set (fail closed for unscoped legacy rows).
"""

from __future__ import annotations

from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import StreamingHttpResponse
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.audit.services import record_audit
from apps.core.exceptions import NotFoundError
from apps.documents.entity_scoping import resolve_company_id
from apps.documents.models import Attachment
from apps.documents.serializers import AttachmentSerializer, AttachmentUploadSerializer
from apps.documents.storage import storage
from apps.documents.validators import build_storage_key, quoted_header_filename, validate_upload
from apps.identity.permissions import HasPermission


class AttachmentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [HasPermission]
    permission_map = {"DELETE": "documents.attachment.delete"}
    required_permission = "documents.attachment.view"
    filterset_fields = ["entity_type", "entity_id", "content_type"]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """Company-isolated attachment register (Q-055). Rows without a
        resolvable company are invisible to non-superusers (fail closed)."""
        qs = self.queryset.all()
        user = self.request.user
        if not getattr(user, "is_authenticated", False):
            return qs.none()
        if user.is_superuser:
            return qs
        ids = set(user.company_memberships.values_list("company_id", flat=True))
        return qs.filter(Q(company_id__in=ids)) if ids else qs.none()

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        serializer = AttachmentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        uploaded = payload["file"]

        # Resolve the target's company BEFORE touching storage: unknown types
        # and foreign-company targets are rejected outright (Q-055).
        company_id = resolve_company_id(payload["entity_type"], payload["entity_id"])
        if not request.user.is_superuser:
            allowed = {
                str(i)
                for i in request.user.company_memberships.values_list("company_id", flat=True)
            }
            if str(company_id) not in allowed:
                from apps.core.exceptions import AuthorizationError

                raise AuthorizationError("The target record belongs to another company.")

        validate_upload(uploaded)
        checksum = Attachment.compute_checksum(uploaded)
        key = build_storage_key(payload["entity_type"], payload["entity_id"], uploaded.name)
        stored_key = storage.save(key, ContentFile(uploaded.read()))

        attachment = Attachment.objects.create(
            entity_type=payload["entity_type"],
            entity_id=payload["entity_id"],
            company_id=company_id,
            original_filename=uploaded.name,
            content_type=getattr(uploaded, "content_type", "") or "",
            size_bytes=uploaded.size,
            checksum_sha256=checksum,
            storage_key=stored_key,
            description=payload.get("description", ""),
            created_by=request.user,
        )
        record_audit(
            action="CREATE",
            entity_type="documents.Attachment",
            entity_id=str(attachment.pk),
            actor=request.user,
            metadata={"linked_to": f"{attachment.entity_type}#{attachment.entity_id}"},
        )
        return Response(AttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        attachment = self.get_object()  # enforces view permission + queryset
        if not storage.exists(attachment.storage_key):
            raise NotFoundError("The stored file is missing.")
        file_handle = storage.open(attachment.storage_key, "rb")
        response = StreamingHttpResponse(
            file_handle,
            content_type=attachment.content_type or "application/octet-stream",
        )
        # Force download with the safe original name; never expose storage_key.
        # The name is header-escaped so it cannot break out of the quoted-string.
        response["Content-Disposition"] = (
            f'attachment; filename="{quoted_header_filename(attachment.original_filename)}"'
        )
        response["Content-Length"] = attachment.size_bytes
        return response

    def perform_destroy(self, instance):
        # Soft-delete the metadata; retain bytes for traceability/recovery.
        record_audit(
            action="DELETE",
            entity_type="documents.Attachment",
            entity_id=str(instance.pk),
            actor=self.request.user,
        )
        instance.delete()
