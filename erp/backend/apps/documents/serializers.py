from __future__ import annotations

from rest_framework import serializers

from apps.documents.models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            "id",
            "entity_type",
            "entity_id",
            "original_filename",
            "content_type",
            "size_bytes",
            "checksum_sha256",
            "description",
            "download_url",
            "created_at",
            "created_by",
        ]
        read_only_fields = fields

    def get_download_url(self, obj) -> str:
        return f"/api/v1/documents/attachments/{obj.pk}/download/"


class AttachmentUploadSerializer(serializers.Serializer):
    entity_type = serializers.CharField(max_length=100)
    entity_id = serializers.CharField(max_length=64)
    file = serializers.FileField()
    description = serializers.CharField(
        max_length=500, required=False, allow_blank=True, default=""
    )
