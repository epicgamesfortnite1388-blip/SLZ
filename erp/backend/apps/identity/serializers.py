"""Identity serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.identity.models import Permission, Role, User


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "code", "module", "description_en", "description_fa"]


class RoleSerializer(serializers.ModelSerializer):
    permission_codes = serializers.SlugRelatedField(
        source="permissions",
        slug_field="code",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Role
        fields = [
            "id",
            "code",
            "name_en",
            "name_fa",
            "description",
            "is_system",
            "permission_codes",
        ]


class UserSerializer(serializers.ModelSerializer):
    companies = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    roles = serializers.SlugRelatedField(slug_field="code", many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "full_name",
            "language",
            "timezone",
            "is_active",
            "is_staff",
            "is_superuser",
            "roles",
            "permissions",
            "companies",
            "date_joined",
        ]
        read_only_fields = ["is_staff", "is_superuser", "date_joined"]

    def get_permissions(self, obj) -> list[str]:
        return sorted(obj.permission_codes())

    def get_companies(self, obj) -> list[str]:
        """IDs of the companies this user is a member of (Q-055)."""
        return [str(m.company_id) for m in obj.company_memberships.select_related("company")]
