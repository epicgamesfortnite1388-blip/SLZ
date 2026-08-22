"""Serializers for Production — Work Orders.

Business/lifecycle rules live in ``apps.production.services`` (status
transitions) and the DB (unique numbers, referential integrity); this serializer
validates wire shape plus a few cross-field **integrity invariants** (not
business policy) so a production order is always an internally consistent
snapshot of the definition it is built to: the pinned engineering/BOM/routing
revisions must belong to the product being made, and every reference must stay
inside the order's own company (DR-040 multi-company). ``status`` is read-only on
the header — it changes only through the dedicated status actions.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.core.validation import PositiveDecimalField
from apps.production.models import ProductionOrder


class ProductionOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrder
        fields = [
            "id",
            "company",
            "site",
            "number",
            "customer_product",
            "spec_revision",
            "bom_revision",
            "routing_revision",
            "sales_order_line",
            "status",
            "planned_quantity",
            "uom",
            "scheduled_start",
            "scheduled_end",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status"]

    # A planned quantity of zero or less is internally contradictory.
    planned_quantity = PositiveDecimalField()

    def validate(self, attrs):
        """Enforce snapshot integrity (referential, not business policy).

        These are data-integrity invariants — a production order that builds
        product X must pin a specification revision *of* product X, any pinned
        BOM/Routing revision must be built for that same spec revision, and all
        references must belong to the order's company. None of this invents an
        OPEN business rule: BOM/Routing remain optional (Q-026) and no revision
        *status* is required at draft time.
        """

        def resolved(field):
            if field in attrs:
                return attrs[field]
            return getattr(self.instance, field, None)

        company = resolved("company")
        site = resolved("site")
        customer_product = resolved("customer_product")
        spec_revision = resolved("spec_revision")
        bom_revision = resolved("bom_revision")
        routing_revision = resolved("routing_revision")

        errors = {}

        if company is not None and customer_product is not None:
            if customer_product.company_id != company.id:
                errors["customer_product"] = (
                    "Customer product belongs to a different company than the " "order."
                )

        if company is not None and site is not None:
            if site.company_id != company.id:
                errors["site"] = "Site belongs to a different company than the order."

        if spec_revision is not None and customer_product is not None:
            if spec_revision.root_id != customer_product.id:
                errors["spec_revision"] = (
                    "Specification revision does not belong to the customer "
                    "product being produced."
                )

        if bom_revision is not None and spec_revision is not None:
            if bom_revision.root.spec_revision_id != spec_revision.id:
                errors["bom_revision"] = (
                    "BOM revision is not built for this specification revision."
                )

        if routing_revision is not None and spec_revision is not None:
            if routing_revision.root.spec_revision_id != spec_revision.id:
                errors["routing_revision"] = (
                    "Routing revision is not built for this specification " "revision."
                )

        if errors:
            raise serializers.ValidationError(errors)
        return attrs
