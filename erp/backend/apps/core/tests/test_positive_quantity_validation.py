"""Boundary validation: document quantities must be strictly positive.

Guards against zero/negative quantities leaking onto commercial documents
(sales/procurement lines), production orders, and BOM lines — internally
contradictory data that would corrupt downstream costing/fulfilment.
"""

from __future__ import annotations

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from apps.manufacturing.serializers import BomLineSerializer
from apps.procurement.serializers import (
    PurchaseOrderLineSerializer,
    PurchaseRequisitionLineSerializer,
)
from apps.production.serializers import ProductionOrderSerializer
from apps.sales.serializers import SalesOrderLineSerializer

CASES = [
    (SalesOrderLineSerializer, "quantity"),
    (PurchaseRequisitionLineSerializer, "quantity"),
    (PurchaseOrderLineSerializer, "quantity"),
    (ProductionOrderSerializer, "planned_quantity"),
    (BomLineSerializer, "quantity_per_output"),
]

INVALID_VALUES = ["0", "-1", "0.000000", "-0.001"]


class PositiveQuantityValidationTests(SimpleTestCase):
    def _assert_rejected(self, serializer_cls, field, value):
        serializer = serializer_cls(data={field: value})
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            pass
        self.assertIn(field, serializer.errors, f"{serializer_cls.__name__} accepted {value!r}")

    def test_zero_and_negative_quantities_rejected(self):
        for serializer_cls, field in CASES:
            for value in INVALID_VALUES:
                self._assert_rejected(serializer_cls, field, value)

    def test_bom_scrap_pct_negative_rejected(self):
        serializer = BomLineSerializer(data={"scrap_pct": "-0.5"})
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            pass
        self.assertIn("scrap_pct", serializer.errors)
