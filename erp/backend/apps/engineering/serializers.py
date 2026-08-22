"""Serializers for Product Engineering (shape + input validation only).

Business/lifecycle rules live in ``apps.engineering.services``; these serializers
validate wire shape and a few input invariants (ink subtype, revision
editability) so clients get clean 4xx errors instead of 500s.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import Material, MaterialSubtype
from apps.core.exceptions import ConflictError
from apps.engineering.models import (
    CustomerProduct,
    SpecColor,
    SpecificationRevision,
    SpecLayer,
    SpecParameter,
    ToolingAsset,
)
from apps.inventory.models import WarehouseStoreType


class CustomerProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProduct
        fields = [
            "id",
            "company",
            "customer",
            "code",
            "name_fa",
            "name_en",
            "product_group",
            "family",
            "base_uom",
            "is_active",
            "created_at",
            "updated_at",
        ]


class SpecificationRevisionSerializer(serializers.ModelSerializer):
    """Read + DRAFT-create. ``root`` and header fields are writable on create;
    ``revision_number``/``status``/effective dates are managed by the service."""

    class Meta:
        model = SpecificationRevision
        fields = [
            "id",
            "root",
            "revision_number",
            "status",
            "effective_from",
            "effective_to",
            "change_reason",
            "spec_format",
            "bag_type",
            "width_mm",
            "width_tol_low",
            "width_tol_high",
            "length_mm",
            "length_tol_low",
            "length_tol_high",
            "gusset_mm",
            "print_process",
            "number_of_colors",
            "has_lamination",
            "has_cold_seal",
            "surface_finish",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "revision_number",
            "status",
            "effective_from",
            "effective_to",
        ]


def _require_ink(material: Material, field_name: str) -> None:
    if material is not None and material.subtype != MaterialSubtype.INK:
        raise serializers.ValidationError({field_name: "Material must be of subtype INK."})


class _ChildOfRevisionSerializer(serializers.ModelSerializer):
    """Base for spec child rows: forbid attaching/moving to a non-DRAFT revision."""

    def _target_revision(self, attrs) -> SpecificationRevision:
        revision = attrs.get("revision") or getattr(self.instance, "revision", None)
        return revision

    def validate(self, attrs):
        revision = self._target_revision(attrs)
        if revision is not None and not revision.is_editable:
            raise ConflictError(
                "The specification revision is not in DRAFT; create a new "
                "revision before editing its content.",
                code="revision_not_editable",
            )
        return attrs


class SpecLayerSerializer(_ChildOfRevisionSerializer):
    class Meta:
        model = SpecLayer
        fields = [
            "id",
            "revision",
            "sequence",
            "material",
            "function",
            "micron",
            "micron_tol_low",
            "micron_tol_high",
            "created_at",
            "updated_at",
        ]


class SpecColorSerializer(_ChildOfRevisionSerializer):
    class Meta:
        model = SpecColor
        fields = [
            "id",
            "revision",
            "sequence",
            "color_name",
            "ink",
            "alternative_ink",
            "coverage_pct",
            "delta_e_tol",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        ink = attrs.get("ink") or getattr(self.instance, "ink", None)
        alt = attrs.get("alternative_ink") or getattr(self.instance, "alternative_ink", None)
        _require_ink(ink, "ink")
        _require_ink(alt, "alternative_ink")
        return attrs


class SpecParameterSerializer(_ChildOfRevisionSerializer):
    class Meta:
        model = SpecParameter
        fields = [
            "id",
            "revision",
            "key",
            "datatype",
            "value_text",
            "value_number",
            "value_bool",
            "unit",
            "tol_low",
            "tol_high",
            "created_at",
            "updated_at",
        ]


class ToolingAssetSerializer(serializers.ModelSerializer):
    """Read + create/update for cliché / sheet / set tooling assets (SR-03).

    ``status`` is managed by the retire/reactivate service actions, so it is
    read-only here. Integrity checks keep the asset inside its company boundary
    and pin a linked warehouse to a CLICHE store (SR-10).
    """

    is_life_exceeded = serializers.BooleanField(read_only=True)

    class Meta:
        model = ToolingAsset
        fields = [
            "id",
            "company",
            "customer",
            "customer_product",
            "code",
            "name_fa",
            "name_en",
            "tooling_type",
            "status",
            "usage_life_limit",
            "usage_count",
            "warehouse",
            "notes",
            "is_life_exceeded",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status"]

    def validate(self, attrs):
        # Resolve effective values across create (attrs) and partial update.
        def _eff(name):
            if name in attrs:
                return attrs[name]
            return getattr(self.instance, name, None)

        company = _eff("company")
        customer = _eff("customer")
        customer_product = _eff("customer_product")
        warehouse = _eff("warehouse")

        if warehouse is not None:
            if company is not None and warehouse.company_id != company.id:
                raise serializers.ValidationError(
                    {"warehouse": "Warehouse must belong to the same company."}
                )
            if warehouse.store_type != WarehouseStoreType.CLICHE:
                raise serializers.ValidationError(
                    {"warehouse": "Warehouse must be a cliché (CLICHE) store."}
                )

        if customer_product is not None:
            if company is not None and customer_product.company_id != company.id:
                raise serializers.ValidationError(
                    {"customer_product": "Product must belong to the same company."}
                )
            if customer is not None and customer_product.customer_id != customer.id:
                raise serializers.ValidationError(
                    {"customer_product": "Product must belong to the same customer."}
                )
        return attrs
