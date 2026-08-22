"""Serializers for partners master data (shape + input validation only)."""

from __future__ import annotations

from rest_framework import serializers

from apps.partners.models import Address, Contact, Customer, Partner, Supplier


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = [
            "id",
            "company",
            "code",
            "name_fa",
            "name_en",
            "legal_name",
            "national_id",
            "economic_code",
            "is_customer",
            "is_supplier",
            "is_sanctioned",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        # Mirror the DB CheckConstraint so clients get a clean 400, not a 500.
        is_customer = attrs.get(
            "is_customer",
            getattr(self.instance, "is_customer", False),
        )
        is_supplier = attrs.get(
            "is_supplier",
            getattr(self.instance, "is_supplier", False),
        )
        if not (is_customer or is_supplier):
            raise serializers.ValidationError("A partner must be a customer, a supplier, or both.")
        return attrs


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "partner",
            "sales_line",
            "delivery_tolerance_pct",
            "requires_coa",
            "notes",
            "created_at",
            "updated_at",
        ]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id",
            "partner",
            "is_approved",
            "evaluation_score",
            "lead_time_days",
            "notes",
            "created_at",
            "updated_at",
        ]


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "partner",
            "name",
            "title",
            "kind",
            "email",
            "phone",
            "is_primary",
            "created_at",
            "updated_at",
        ]


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "partner",
            "kind",
            "line1",
            "line2",
            "city",
            "province",
            "postal_code",
            "country",
            "is_primary",
            "created_at",
            "updated_at",
        ]
