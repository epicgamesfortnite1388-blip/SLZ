"""Sales — Sales Orders (Task 010).

This app owns the *commercial-document* layer of the sell side: the customer
**Sales Order** (SO), the demand origin for this made-to-order (MTO) business.
Like the procurement documents, an SO is a transactional instance with a
**status lifecycle (state machine)** — deliberately NOT the ``VersionedRoot`` /
``Revision`` pattern (that models engineering versions, not commercial paper).

Scope discipline (see docs/reconciliation/current-to-future-system.md rows 4/11/
12/25, docs/business-analysis/business-processes.md, docs/requirements/
do-not-build-yet.md):

* An SO carries a MANUAL ``number`` (unique per company). No auto-numbering is
  invented (document coding is OPEN, #14) — the business supplies the number.
* The SO lifecycle here is the generic, minimal commercial paper trail:
  ``DRAFT → CONFIRMED → CLOSED`` (+ ``CANCELLED``). ``CONFIRMED`` is the accepted
  commitment; ``CLOSED`` is a manual administrative close. NO approval-hierarchy
  or credit gate is encoded (that policy is OPEN, #7 / Finance).
* Lines are editable only while the header is DRAFT (a confirmed order is a
  commitment).

Deliberately NOT built (OPEN gates — do-not-build-yet):
* Sales Inquiry → Quotation / Proforma and the **pricing algorithm** (R-14, #11) —
  ``unit_price`` is a nullable manual field; NO price is derived or invented.
* ATP / promised delivery date from capacity + stock (SR-12, #12) —
  ``requested_date`` records only what the customer asked for, never a promise.
* Allocation / reservation / shipment / delivery note / invoicing — need the
  gated stock + traceability layer (Q-046, #18) and Finance (#23/#26).
* Credit management, settlement terms, over/under-delivery tolerance enforcement
  (DR-028; the tolerance field on ``partners.Customer`` is data only).
* Multi-level packaging & marking per order (SR-11, #25); new-vs-repeat routing
  to engineering (A-001, #4); drawing/proof customer-approval gate (R-16, #6).
"""

from __future__ import annotations

from django.db import models

from apps.core.models import SoftDeleteModel


class SalesOrderStatus(models.TextChoices):
    """Sales-order lifecycle. Editable only in DRAFT; terminal in CLOSED /
    CANCELLED. ``CONFIRMED`` is the accepted customer commitment; downstream
    fulfilment states (allocated / in production / shipped / delivered) are
    intentionally absent — they belong to the gated stock/production layers."""

    DRAFT = "DRAFT", "Draft"
    CONFIRMED = "CONFIRMED", "Confirmed"
    CLOSED = "CLOSED", "Closed"
    CANCELLED = "CANCELLED", "Cancelled"


class SalesOrder(SoftDeleteModel):
    """Customer order — the MTO demand origin. Company-scoped (DR-040); ``site``
    optional. ``number`` is a MANUAL business number, unique per company.

    ``currency`` is a plain ISO code (default IRR) captured for the record only —
    there is NO FX conversion, pricing algorithm, or valuation here."""

    company = models.ForeignKey(
        "organization.Company",
        on_delete=models.PROTECT,
        related_name="sales_orders",
    )
    site = models.ForeignKey(
        "organization.Site",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sales_orders",
    )
    number = models.CharField(max_length=40)
    customer = models.ForeignKey(
        "partners.Customer", on_delete=models.PROTECT, related_name="sales_orders"
    )
    status = models.CharField(
        max_length=16,
        choices=SalesOrderStatus.choices,
        default=SalesOrderStatus.DRAFT,
        db_index=True,
    )
    order_date = models.DateField(null=True, blank=True)
    # What the customer asked for — NOT an ATP/promised date (SR-12 gated).
    requested_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="IRR")
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "sales_sales_order"
        ordering = ["company", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"],
                name="uq_sales_order_company_number",
            ),
        ]

    def __str__(self) -> str:
        return f"SO {self.number} [{self.status}]"

    @property
    def is_editable(self) -> bool:
        """Header + lines may be mutated only while DRAFT."""
        return self.status == SalesOrderStatus.DRAFT


class SalesOrderLine(SoftDeleteModel):
    """One ordered customer product + quantity (and optional unit price).
    Editable only while the parent order is DRAFT.

    Ordered item is a ``engineering.CustomerProduct`` (the durable, customer-
    specific orderable identity that carries the versioned specification).
    ``unit_price`` is nullable — no pricing is invented (proforma/pricing is
    OPEN, R-14/#11)."""

    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="lines")
    sequence = models.PositiveSmallIntegerField()
    customer_product = models.ForeignKey(
        "engineering.CustomerProduct",
        on_delete=models.PROTECT,
        related_name="sales_order_lines",
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    uom = models.ForeignKey(
        "catalog.UnitOfMeasure",
        on_delete=models.PROTECT,
        related_name="sales_order_lines",
    )
    unit_price = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "sales_sales_order_line"
        ordering = ["order", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "sequence"],
                name="uq_so_line_order_sequence",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.order_id} L{self.sequence}:{self.customer_product_id}"
