from __future__ import annotations

from rest_framework import serializers

from apps.core.viewsets import AuditedModelViewSet
from apps.organization.models import Company, Department, Site, SiteCapability


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "code", "name_en", "name_fa", "is_active", "created_at", "updated_at"]


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = [
            "id",
            "company",
            "code",
            "name_en",
            "name_fa",
            "timezone",
            "is_active",
            "created_at",
            "updated_at",
        ]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = [
            "id",
            "site",
            "code",
            "name_en",
            "name_fa",
            "parent",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        """Hierarchy integrity: a parent must live on the same site and must
        never create a cycle (self-parent or a deeper A→B→A loop). Enforced on
        create AND update — the edit UI makes reparenting a routine operation.
        An explicit null parent (``"parent" in attrs``) always clears; an
        omitted parent on PATCH falls back to the instance's current one so a
        site change cannot silently strand it cross-site."""
        instance = getattr(self, "instance", None)
        site = attrs.get("site") or (instance.site if instance is not None else None)
        if "parent" in attrs:
            parent = attrs["parent"]
        elif instance is not None:
            parent = instance.parent
        else:
            parent = None

        if parent is not None:
            if site is None or parent.site_id != site.pk:
                raise serializers.ValidationError(
                    {"parent": "A department's parent must belong to the same site."}
                )
            seen = {instance.pk} if instance is not None else set()
            node = parent
            while node is not None:
                if node.pk in seen:
                    raise serializers.ValidationError(
                        {"parent": "This parent assignment would create a cycle."}
                    )
                seen.add(node.pk)
                node = node.parent
        return attrs


class CompanyViewSet(AuditedModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_map = {
        "POST": "organization.company.manage",
        "PUT": "organization.company.manage",
        "PATCH": "organization.company.manage",
        "DELETE": "organization.company.manage",
    }
    required_permission = "organization.company.view"

    def get_queryset(self):
        """Members see only companies they belong to (Q-055);
        superusers see every company."""
        user = self.request.user
        if user.is_superuser or not getattr(user, "is_authenticated", False):
            return super().get_queryset()
        return Company.objects.filter(memberships__user=user)

    def perform_create(self, serializer):
        """Bootstrap rule (Q-055): whoever creates a company becomes its
        first member — otherwise they would immediately lose sight of the
        record they just made."""
        from apps.identity.models import CompanyMembership

        super().perform_create(serializer)
        company = getattr(serializer.instance, "pk", None) and serializer.instance
        if company is not None:
            CompanyMembership.objects.get_or_create(user=self.request.user, company=company)

    search_fields = ["code", "name_en", "name_fa"]


class SiteViewSet(AuditedModelViewSet):
    queryset = Site.objects.all().select_related("company")
    serializer_class = SiteSerializer
    permission_map = {
        "POST": "organization.site.manage",
        "PUT": "organization.site.manage",
        "PATCH": "organization.site.manage",
        "DELETE": "organization.site.manage",
    }
    required_permission = "organization.site.view"
    filterset_fields = ["company", "is_active"]
    search_fields = ["code", "name_en", "name_fa"]


class DepartmentViewSet(AuditedModelViewSet):
    queryset = Department.objects.all().select_related("site")
    serializer_class = DepartmentSerializer
    permission_map = {
        "POST": "organization.department.manage",
        "PUT": "organization.department.manage",
        "PATCH": "organization.department.manage",
        "DELETE": "organization.department.manage",
    }
    required_permission = "organization.department.view"
    company_scope_lookup = "site__company"
    filterset_fields = ["site", "parent", "is_active"]
    search_fields = ["code", "name_en", "name_fa"]


class SiteCapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteCapability
        fields = [
            "id",
            "site",
            "capability",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]


class SiteCapabilityViewSet(AuditedModelViewSet):
    """Site production-capability declarations (SR-15). Audited master data."""

    queryset = SiteCapability.objects.all().select_related("site", "site__company")
    serializer_class = SiteCapabilitySerializer
    permission_map = {
        "POST": "organization.sitecapability.manage",
        "PUT": "organization.sitecapability.manage",
        "PATCH": "organization.sitecapability.manage",
        "DELETE": "organization.sitecapability.manage",
    }
    required_permission = "organization.sitecapability.view"
    company_scope_lookup = "site__company"
    filterset_fields = ["site", "capability", "is_active"]
    search_fields = ["capability", "notes"]
