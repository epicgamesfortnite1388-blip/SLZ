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
    set_permission_codes = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="Replace all permissions with this list of codes.",
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
            "set_permission_codes",
        ]

    def update(self, instance, validated_data):
        codes = validated_data.pop("set_permission_codes", None)
        instance = super().update(instance, validated_data)
        if codes is not None:
            perms = Permission.objects.filter(code__in=codes)
            instance.permissions.set(perms)
        return instance


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
        # Return the global permission codes (no company scoping).
        # Per-company permissions are surfaced under the nested
        # "permissions_by_company" key in /auth/me/.
        return sorted(obj.permission_codes())

    def get_companies(self, obj) -> list[str]:
        """IDs of the companies this user is a member of (Q-055)."""
        return [str(m.company_id) for m in obj.company_memberships.select_related("company")]
