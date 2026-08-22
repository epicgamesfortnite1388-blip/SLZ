"""Reusable serializer field factories for wire-shape validation.

``PositiveDecimalField`` rejects zero and negative quantities at the API
boundary so documents (order lines, BOM lines, production orders) can never
carry internally-contradictory amounts. This mirrors the DB-level positivity
pattern already used by ``ck_uom_conversion_factor_positive``.
"""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers


def PositiveDecimalField(max_digits=18, decimal_places=6, **kwargs):
    """A decimal field that must be strictly greater than zero.

    ``min_value`` is the smallest representable value at ``decimal_places``, so
    any accepted value is > 0.
    """
    quantum = Decimal(1).scaleb(-decimal_places)
    return serializers.DecimalField(
        max_digits=max_digits,
        decimal_places=decimal_places,
        min_value=quantum,
        **kwargs,
    )
