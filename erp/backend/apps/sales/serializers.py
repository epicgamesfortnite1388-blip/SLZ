"""Serializers for Sales — Customer Orders.

Business/lifecycle rules live in ``apps.sales.services`` (status transitions) and
the DB (unique numbers, referential integrity); these serializers validate wire
shape and the DRAFT-only editability of child lines so clients get clean 4xx
errors instead of 500s. ``status`` is read-only on the header — it changes only
through the dedicated status actions.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.core.exceptions import ConflictError
from apps.core.validation import PositiveDecimalField
from apps.sales.models import SalesOrder, SalesOrderLine


class SalesOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = [
            "id",
            "company",
            "site",
            "number",
            "customer",
            "status",
            "order_date",
            "requested_date",
            "currency",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status"]

    def validate(self, attrs):
        company = attrs.get("company", getattr(self.instance, "company", None))
        site = attrs.get("site", getattr(self.instance, "site", None))
        customer = attrs.get("customer", getattr(self.instance, "customer", None))
        errors = {}
        if company and site and site.company_id != company.id:
            errors["site"] = "Site must belong to the order company."
        if company and customer and customer.partner.company_id != company.id:
            errors["customer"] = "Customer must belong to the order company."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class SalesOrderLineSerializer(serializers.ModelSerializer):
    """Order child line. Two invariants are enforced here:

    * **Commitment immutability** — a line may not be attached to / moved onto a
      non-DRAFT order (a confirmed order is a commitment).
    * **Snapshot referential integrity** (analogous to the production order
      guard, DR-040 multi-company) — the ordered ``customer_product`` must belong
      to the order's own company, and to the same customer the order is for. This
      is a pure data-integrity invariant, not an invented business rule: it only
      forbids internally-contradictory documents (customer A's product on
      customer B's order, or another company's product leaking onto the order).
    """

    def _target_parent(self, attrs):
        return attrs.get("order") or getattr(self.instance, "order", None)

    def _resolved(self, attrs, field):
        if field in attrs:
            return attrs[field]
        return getattr(self.instance, field, None)

    def validate(self, attrs):
        parent = self._target_parent(attrs)
        if parent is not None and not parent.is_editable:
            raise ConflictError(
                "The parent order is not in DRAFT; it can no longer be edited.",
                code="document_not_editable",
            )

        customer_product = self._resolved(attrs, "customer_product")
        errors = {}
        if parent is not None and customer_product is not None:
            if customer_product.company_id != parent.company_id:
                errors["customer_product"] = (
                    "Customer product belongs to a different company than the " "order."
                )
            # ``order.customer`` is a partners.Customer (role extension); its
            # ``partner`` is the party the CustomerProduct is tied to.
            elif customer_product.customer_id != parent.customer.partner_id:
                errors["customer_product"] = (
                    "Customer product belongs to a different customer than the " "order."
                )

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    class Meta:
        model = SalesOrderLine
        fields = [
            "id",
            "order",
            "sequence",
            "customer_product",
            "quantity",
            "uom",
            "unit_price",
            "notes",
            "created_at",
            "updated_at",
        ]

    # An ordered quantity of zero or less is internally contradictory.
    quantity = PositiveDecimalField()
