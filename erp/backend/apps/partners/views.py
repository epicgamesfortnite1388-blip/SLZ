"""Thin viewsets for partners master data (audited via ``AuditedModelViewSet``)."""

from __future__ import annotations

from apps.core.viewsets import AuditedModelViewSet
from apps.partners.models import Address, Contact, Customer, Partner, Supplier
from apps.partners.serializers import (
    AddressSerializer,
    ContactSerializer,
    CustomerSerializer,
    PartnerSerializer,
    SupplierSerializer,
)


class PartnerViewSet(AuditedModelViewSet):
    queryset = Partner.objects.all().select_related("company")
    serializer_class = PartnerSerializer
    permission_map = {
        "POST": "partners.partner.manage",
        "PUT": "partners.partner.manage",
        "PATCH": "partners.partner.manage",
        "DELETE": "partners.partner.manage",
    }
    required_permission = "partners.partner.view"
    filterset_fields = [
        "company",
        "is_customer",
        "is_supplier",
        "is_sanctioned",
        "is_active",
    ]
    search_fields = ["code", "name_fa", "name_en", "legal_name", "national_id"]


class CustomerViewSet(AuditedModelViewSet):
    queryset = Customer.objects.all().select_related("partner", "sales_line")
    serializer_class = CustomerSerializer
    permission_map = {
        "POST": "partners.partner.manage",
        "PUT": "partners.partner.manage",
        "PATCH": "partners.partner.manage",
        "DELETE": "partners.partner.manage",
    }
    required_permission = "partners.partner.view"
    filterset_fields = ["partner", "sales_line", "requires_coa"]


class SupplierViewSet(AuditedModelViewSet):
    queryset = Supplier.objects.all().select_related("partner")
    serializer_class = SupplierSerializer
    permission_map = {
        "POST": "partners.partner.manage",
        "PUT": "partners.partner.manage",
        "PATCH": "partners.partner.manage",
        "DELETE": "partners.partner.manage",
    }
    required_permission = "partners.partner.view"
    filterset_fields = ["partner", "is_approved"]


class ContactViewSet(AuditedModelViewSet):
    queryset = Contact.objects.all().select_related("partner")
    serializer_class = ContactSerializer
    permission_map = {
        "POST": "partners.contact.manage",
        "PUT": "partners.contact.manage",
        "PATCH": "partners.contact.manage",
        "DELETE": "partners.contact.manage",
    }
    required_permission = "partners.contact.view"
    filterset_fields = ["partner", "kind", "is_primary"]
    search_fields = ["name", "email", "phone"]


class AddressViewSet(AuditedModelViewSet):
    queryset = Address.objects.all().select_related("partner")
    serializer_class = AddressSerializer
    permission_map = {
        "POST": "partners.address.manage",
        "PUT": "partners.address.manage",
        "PATCH": "partners.address.manage",
        "DELETE": "partners.address.manage",
    }
    required_permission = "partners.address.view"
    filterset_fields = ["partner", "kind", "is_primary"]
    search_fields = ["line1", "city", "province", "postal_code"]
