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
    filterset_fields = ["site", "capability", "is_active"]
    search_fields = ["capability", "notes"]
