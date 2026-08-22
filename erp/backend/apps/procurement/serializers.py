"""Serializers for Procurement — Requisitions & Purchase Orders.

Business/lifecycle rules live in ``apps.procurement.services`` (status
transitions) and the DB (unique numbers, referential integrity); these
serializers validate wire shape and the DRAFT-only editability of child lines so
clients get clean 4xx errors instead of 500s. ``status`` is read-only on the
headers — it changes only through the dedicated status actions.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import Material, UnitOfMeasure
from apps.core.exceptions import ConflictError
from apps.core.validation import PositiveDecimalField
from apps.inventory.models import TraceabilityUnitType, Warehouse
from apps.organization.models import Company
from apps.partners.models import Supplier
from apps.procurement.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseRequisition,
    PurchaseRequisitionLine,
)


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequisition
        fields = [
            "id",
            "company",
            "site",
            "number",
            "status",
            "requested_by",
            "need_by_date",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status"]

    def validate(self, attrs):
        company = attrs.get("company", getattr(self.instance, "company", None))
        site = attrs.get("site", getattr(self.instance, "site", None))
        errors = {}
        if company and site and site.company_id != company.id:
            errors["site"] = "Site must belong to the requisition company."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "company",
            "site",
            "number",
            "supplier",
            "status",
            "order_date",
            "expected_date",
            "currency",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status"]

    def validate(self, attrs):
        company = attrs.get("company", getattr(self.instance, "company", None))
        site = attrs.get("site", getattr(self.instance, "site", None))
        supplier = attrs.get("supplier", getattr(self.instance, "supplier", None))
        errors = {}
        if company and site and site.company_id != company.id:
            errors["site"] = "Site must belong to the order company."
        if company and supplier and supplier.partner.company_id != company.id:
            errors["supplier"] = "Supplier must belong to the order company."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class _LineOfDocumentSerializer(serializers.ModelSerializer):
    """Base for document child lines. Enforces two invariants:

    * **Commitment immutability** — a line may not be attached to / moved onto a
      non-DRAFT header (a confirmed document is a commitment).
    * **Snapshot referential integrity** (DR-040 multi-company) — every FK a
      subclass declares in ``company_scoped_material`` must belong to the same
      company as the parent header. This is a pure data-integrity invariant (it
      only forbids internally-contradictory documents / cross-company leakage),
      not an invented business rule. Subclasses set ``parent_field`` and may
      override ``_validate_references``.
    """

    parent_field: str = ""

    def _target_parent(self, attrs):
        return attrs.get(self.parent_field) or getattr(self.instance, self.parent_field, None)

    def _resolved(self, attrs, field):
        if field in attrs:
            return attrs[field]
        return getattr(self.instance, field, None)

    def _validate_references(self, attrs, parent, errors):
        """Hook: subclasses add referential-integrity checks into ``errors``."""
        return

    def validate(self, attrs):
        parent = self._target_parent(attrs)
        if parent is not None and not parent.is_editable:
            raise ConflictError(
                "The parent document is not in DRAFT; it can no longer be " "edited.",
                code="document_not_editable",
            )
        errors = {}
        self._validate_references(attrs, parent, errors)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class PurchaseRequisitionLineSerializer(_LineOfDocumentSerializer):
    parent_field = "requisition"

    def _validate_references(self, attrs, parent, errors):
        material = self._resolved(attrs, "material")
        if parent is not None and material is not None:
            if material.company_id != parent.company_id:
                errors["material"] = (
                    "Material belongs to a different company than the " "requisition."
                )

    class Meta:
        model = PurchaseRequisitionLine
        fields = [
            "id",
            "requisition",
            "sequence",
            "material",
            "quantity",
            "uom",
            "notes",
            "created_at",
            "updated_at",
        ]

    # A requisition quantity of zero or less is internally contradictory.
    quantity = PositiveDecimalField()


class PurchaseOrderLineSerializer(_LineOfDocumentSerializer):
    parent_field = "order"

    def _validate_references(self, attrs, parent, errors):
        material = self._resolved(attrs, "material")
        if parent is not None and material is not None:
            if material.company_id != parent.company_id:
                errors["material"] = "Material belongs to a different company than the order."
        requisition_line = self._resolved(attrs, "requisition_line")
        if parent is not None and requisition_line is not None:
            if requisition_line.requisition.company_id != parent.company_id:
                errors["requisition_line"] = (
                    "Requisition line belongs to a different company than the " "order."
                )

    class Meta:
        model = PurchaseOrderLine
        fields = [
            "id",
            "order",
            "sequence",
            "material",
            "quantity",
            "uom",
            "unit_price",
            "requisition_line",
            "notes",
            "created_at",
            "updated_at",
        ]

    # An ordered quantity of zero or less is internally contradictory.
    quantity = PositiveDecimalField()


class GoodsReceiptLineInputSerializer(serializers.Serializer):
    """One received line; the service creates the traceability unit."""

    po_line = serializers.PrimaryKeyRelatedField(
        queryset=PurchaseOrderLine.objects.all(), required=False, allow_null=True
    )
    material = serializers.PrimaryKeyRelatedField(queryset=Material.objects.all())
    quantity = PositiveDecimalField()
    uom = serializers.PrimaryKeyRelatedField(queryset=UnitOfMeasure.objects.all())
    traceability_unit_type = serializers.ChoiceField(choices=TraceabilityUnitType.choices)


class GoodsReceiptCreateSerializer(serializers.Serializer):
    """Wire shape for posting a goods receipt (atomic service create)."""

    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all())
    supplier = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(), required=False, allow_null=True
    )
    purchase_order = serializers.PrimaryKeyRelatedField(
        queryset=PurchaseOrder.objects.all(), required=False, allow_null=True
    )
    number = serializers.CharField(max_length=40)
    received_at = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    lines = GoodsReceiptLineInputSerializer(many=True)

    def validate(self, attrs):
        company = attrs["company"]
        warehouse = attrs["warehouse"]
        supplier = attrs.get("supplier")
        purchase_order = attrs.get("purchase_order")
        errors = {}
        if warehouse.company_id != company.id:
            errors["warehouse"] = "Warehouse must belong to the receipt company."
        if supplier is not None and supplier.partner.company_id != company.id:
            errors["supplier"] = "Supplier must belong to the receipt company."
        if purchase_order is not None and purchase_order.company_id != company.id:
            errors["purchase_order"] = "Purchase order must belong to the receipt company."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class GoodsReceiptLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsReceiptLine
        fields = ["id", "grn", "po_line", "material", "quantity", "uom", "traceability_unit"]
        read_only_fields = fields


class GoodsReceiptSerializer(serializers.ModelSerializer):
    lines = GoodsReceiptLineSerializer(many=True, read_only=True)

    class Meta:
        model = GoodsReceipt
        fields = [
            "id",
            "company",
            "warehouse",
            "supplier",
            "purchase_order",
            "number",
            "status",
            "received_at",
            "notes",
            "lines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
