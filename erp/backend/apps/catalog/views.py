"""Thin viewsets for catalog master data (audited via ``AuditedModelViewSet``)."""

from __future__ import annotations

from apps.catalog.models import (
    Material,
    Product,
    ProductClass,
    ProductFamily,
    ProductGroup,
    ProductType,
    UnitOfMeasure,
    UomConversion,
)
from apps.catalog.serializers import (
    MaterialSerializer,
    ProductClassSerializer,
    ProductFamilySerializer,
    ProductGroupSerializer,
    ProductSerializer,
    ProductTypeSerializer,
    UnitOfMeasureSerializer,
    UomConversionSerializer,
)
from apps.core.viewsets import AuditedModelViewSet


class UnitOfMeasureViewSet(AuditedModelViewSet):
    queryset = UnitOfMeasure.objects.all()
    serializer_class = UnitOfMeasureSerializer
    permission_map = {m: "catalog.uom.manage" for m in ("POST", "PUT", "PATCH", "DELETE")}
    required_permission = "catalog.uom.view"
    company_scope_lookup = None
    filterset_fields = ["dimension", "is_active"]
    search_fields = ["code", "name_fa", "name_en"]


class UomConversionViewSet(AuditedModelViewSet):
    queryset = UomConversion.objects.all().select_related("from_uom", "to_uom")
    serializer_class = UomConversionSerializer
    permission_map = {m: "catalog.uom.manage" for m in ("POST", "PUT", "PATCH", "DELETE")}
    required_permission = "catalog.uom.view"
    company_scope_lookup = None
    filterset_fields = ["from_uom", "to_uom"]


class ProductGroupViewSet(AuditedModelViewSet):
    queryset = ProductGroup.objects.all()
    serializer_class = ProductGroupSerializer
    permission_map = {m: "catalog.productgroup.manage" for m in ("POST", "PUT", "PATCH", "DELETE")}
    required_permission = "catalog.productgroup.view"
    company_scope_lookup = None
    filterset_fields = ["is_active"]
    search_fields = ["code", "name_fa", "name_en"]


class ProductTypeViewSet(AuditedModelViewSet):
    queryset = ProductType.objects.all()
    serializer_class = ProductTypeSerializer
    permission_map = {
        m: "catalog.producttaxonomy.manage" for m in ("POST", "PUT", "PATCH", "DELETE")
    }
    required_permission = "catalog.producttaxonomy.view"
    company_scope_lookup = None
    filterset_fields = ["is_active"]
    search_fields = ["code", "name_fa", "name_en"]


class ProductClassViewSet(AuditedModelViewSet):
    queryset = ProductClass.objects.all().select_related("product_type")
    serializer_class = ProductClassSerializer
    permission_map = {
        m: "catalog.producttaxonomy.manage" for m in ("POST", "PUT", "PATCH", "DELETE")
    }
    required_permission = "catalog.producttaxonomy.view"
    company_scope_lookup = None
    filterset_fields = ["product_type", "is_active"]
    search_fields = ["code", "name_fa", "name_en"]


class ProductFamilyViewSet(AuditedModelViewSet):
    queryset = ProductFamily.objects.all().select_related(
        "product_class", "product_class__product_type"
    )
    serializer_class = ProductFamilySerializer
    permission_map = {
        m: "catalog.producttaxonomy.manage" for m in ("POST", "PUT", "PATCH", "DELETE")
    }
    required_permission = "catalog.producttaxonomy.view"
    company_scope_lookup = None
    filterset_fields = ["product_class", "is_active"]
    search_fields = ["code", "name_fa", "name_en"]


class ProductViewSet(AuditedModelViewSet):
    queryset = Product.objects.all().select_related(
        "company", "product_group", "family", "base_uom"
    )
    serializer_class = ProductSerializer
    permission_map = {m: "catalog.product.manage" for m in ("POST", "PUT", "PATCH", "DELETE")}
    required_permission = "catalog.product.view"
    filterset_fields = ["company", "product_group", "family", "is_active"]
    search_fields = ["code", "name_fa", "name_en"]


class MaterialViewSet(AuditedModelViewSet):
    queryset = Material.objects.all().select_related("company", "base_uom")
    serializer_class = MaterialSerializer
    permission_map = {m: "catalog.material.manage" for m in ("POST", "PUT", "PATCH", "DELETE")}
    required_permission = "catalog.material.view"
    filterset_fields = ["company", "subtype", "is_hazardous", "is_active"]
    search_fields = ["code", "name_fa", "name_en", "msds_ref"]
