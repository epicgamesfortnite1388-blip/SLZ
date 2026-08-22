"""Procurement — Purchase Requisitions & Purchase Orders (Task 009).

This app owns the *commercial-document* layer of purchasing: the internal
request to buy (**Purchase Requisition**) and the external commitment to a
supplier (**Purchase Order**). Both are transactional documents with a **status
lifecycle (state machine)** — deliberately NOT the ``VersionedRoot`` /
``Revision`` pattern used by BOM/Routing/Quality, because a purchase document is
a single evolving instance, not a set of immutable versions.

Scope discipline (see docs/business-analysis/business-processes.md §5.6,
docs/reconciliation/current-to-future-system.md, docs/requirements/
do-not-build-yet.md, skill 05):

* A requisition and a purchase order each carry a MANUAL ``number`` (unique per
  company). No auto-numbering scheme is invented (product/document coding is
  OPEN, #14) — the business supplies the number.
* The PO lifecycle here is **truncated before goods receipt**:
  ``DRAFT → APPROVED → SENT → CLOSED`` (+ ``CANCELLED``). The documented downstream
  states ``PARTIALLY_RECEIVED / RECEIVED / (QC)`` belong to the two-stage goods
  receipt (SR-09), which is GATED on the stock/traceability layer (Q-046, #17/#18)
  and is NOT built here.
* Lines are editable only while their header is DRAFT (enforced in the
  serializer/service layer) — an approved/sent document is a commitment.

Deliberately NOT built (OPEN gates — do-not-build-yet):
* Goods receipt / GRN + two-stage temp→QC→definitive receipt (SR-09, #17) — needs
  the gated stock/traceability layer (Q-046, #18).
* MRP / auto-generation of requisitions from demand (#14 / row 14) — needs the
  gated demand + stock layer.
* RFQ / supplier-quotation comparison / sourcing policy (OPEN process) — a PO
  references a supplier directly; no bidding workflow.
* Approval hierarchy & monetary thresholds engine (#7, Q-054/056, DR-032) — the
  approve action is a single manual transition gated by the ``*.manage``
  permission; NO threshold rules are hard-coded.
* Import / foreign-trade documents, sanctions-screening workflow, FX conversion
  (later Trade phase) — a ``currency`` code and manual ``unit_price`` are captured;
  there is NO FX engine and NO valuation.
* Supplier invoice / payment / AP (Finance, #23) and material valuation (#1/#2).
"""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from apps.core.models import SoftDeleteModel


class PurchaseRequisitionStatus(models.TextChoices):
    """Requisition lifecycle. Editable only in DRAFT; terminal in
    REJECTED/CANCELLED. APPROVED is the hand-off point to sourcing (a PO)."""

    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"


class PurchaseOrderStatus(models.TextChoices):
    """Purchase-order lifecycle, truncated BEFORE goods receipt (SR-09 gated).

    ``SENT`` means issued to the supplier; ``CLOSED`` is a manual administrative
    close. Receipt-driven states are intentionally absent."""

    DRAFT = "DRAFT", "Draft"
    APPROVED = "APPROVED", "Approved"
    SENT = "SENT", "Sent"
    CLOSED = "CLOSED", "Closed"
    CANCELLED = "CANCELLED", "Cancelled"


class PurchaseRequisition(SoftDeleteModel):
    """Internal request to purchase materials. Company-scoped (DR-040); ``site``
    optional. ``number`` is a MANUAL business number, unique per company."""

    company = models.ForeignKey(
        "organization.Company",
        on_delete=models.PROTECT,
        related_name="purchase_requisitions",
    )
    site = models.ForeignKey(
        "organization.Site",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="purchase_requisitions",
    )
    number = models.CharField(max_length=40)
    status = models.CharField(
        max_length=16,
        choices=PurchaseRequisitionStatus.choices,
        default=PurchaseRequisitionStatus.DRAFT,
        db_index=True,
    )
    requested_by = models.ForeignKey(
        "hr.Employee",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="purchase_requisitions",
    )
    need_by_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "procurement_purchase_requisition"
        ordering = ["company", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"],
                name="uq_purchase_requisition_company_number",
            ),
        ]

    def __str__(self) -> str:
        return f"PR {self.number} [{self.status}]"

    @property
    def is_editable(self) -> bool:
        """Header + lines may be mutated only while DRAFT."""
        return self.status == PurchaseRequisitionStatus.DRAFT


class PurchaseRequisitionLine(SoftDeleteModel):
    """One requested material + quantity. Editable only while the parent
    requisition is DRAFT (guarded in the serializer/service layer)."""

    requisition = models.ForeignKey(
        PurchaseRequisition, on_delete=models.CASCADE, related_name="lines"
    )
    sequence = models.PositiveSmallIntegerField()
    material = models.ForeignKey(
        "catalog.Material", on_delete=models.PROTECT, related_name="requisition_lines"
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    uom = models.ForeignKey(
        "catalog.UnitOfMeasure",
        on_delete=models.PROTECT,
        related_name="requisition_lines",
    )
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "procurement_purchase_requisition_line"
        ordering = ["requisition", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["requisition", "sequence"],
                name="uq_pr_line_requisition_sequence",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.requisition_id} L{self.sequence}:{self.material_id}"


class PurchaseOrder(SoftDeleteModel):
    """Commitment to buy from a supplier. Company-scoped (DR-040); ``site``
    optional. ``number`` is a MANUAL business number, unique per company.

    ``currency`` is a plain ISO code (default IRR) captured for the record only —
    there is NO FX conversion or valuation here (later Trade/Finance phases)."""

    company = models.ForeignKey(
        "organization.Company",
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    site = models.ForeignKey(
        "organization.Site",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    number = models.CharField(max_length=40)
    supplier = models.ForeignKey(
        "partners.Supplier", on_delete=models.PROTECT, related_name="purchase_orders"
    )
    status = models.CharField(
        max_length=16,
        choices=PurchaseOrderStatus.choices,
        default=PurchaseOrderStatus.DRAFT,
        db_index=True,
    )
    order_date = models.DateField(null=True, blank=True)
    expected_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="IRR")
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "procurement_purchase_order"
        ordering = ["company", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"],
                name="uq_purchase_order_company_number",
            ),
        ]

    def __str__(self) -> str:
        return f"PO {self.number} [{self.status}]"

    @property
    def is_editable(self) -> bool:
        """Header + lines may be mutated only while DRAFT."""
        return self.status == PurchaseOrderStatus.DRAFT


class PurchaseOrderLine(SoftDeleteModel):
    """One ordered material + quantity (and optional unit price). Editable only
    while the parent order is DRAFT.

    ``unit_price`` is nullable — no pricing is invented (supplier price lists /
    valuation are OPEN, #1/#2). ``requisition_line`` optionally records provenance
    (which requisition line this fulfils); it is SET_NULL so the PO survives if
    the source requisition line is later removed."""

    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    sequence = models.PositiveSmallIntegerField()
    material = models.ForeignKey(
        "catalog.Material", on_delete=models.PROTECT, related_name="purchase_order_lines"
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    uom = models.ForeignKey(
        "catalog.UnitOfMeasure",
        on_delete=models.PROTECT,
        related_name="purchase_order_lines",
    )
    unit_price = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    requisition_line = models.ForeignKey(
        PurchaseRequisitionLine,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="purchase_order_lines",
    )
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "procurement_purchase_order_line"
        ordering = ["order", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "sequence"],
                name="uq_po_line_order_sequence",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.order_id} L{self.sequence}:{self.material_id}"


class GoodsReceiptStatus(models.TextChoices):
    """Receipts are immutable execution records (like stock movements).

    A receipt is created directly in ``POSTED`` state: the posting atomically
    creates traceability units and IN stock movements. Corrections happen
    through new, reversing documents - never by editing history.
    """

    POSTED = "POSTED", "Posted"
    VOIDED = "VOIDED", "Voided (reversal pending)"


class GoodsReceipt(SoftDeleteModel):
    """Goods receipt note (SR-09): received materials against a PO.

    Created directly in POSTED state through the sanctioned service; lines
    are immutable. ``purchase_order`` is optional so unplanned receipts are
    possible, but when present every line must reference one of its lines
    and over-receipt is blocked.
    """

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="goods_receipts"
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse", on_delete=models.PROTECT, related_name="goods_receipts"
    )
    supplier = models.ForeignKey(
        "partners.Supplier",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="goods_receipts",
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="goods_receipts",
    )
    number = models.CharField(max_length=40)
    status = models.CharField(
        max_length=10,
        choices=GoodsReceiptStatus.choices,
        default=GoodsReceiptStatus.POSTED,
    )
    received_at = models.DateField()
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "procurement_goods_receipt"
        ordering = ["-received_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["company", "number"], name="uq_grn_company_number"),
        ]

    def __str__(self) -> str:
        return f"GRN {self.number}"


class GoodsReceiptLine(SoftDeleteModel):
    """One received material line; creates a traceability unit on posting."""

    grn = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name="lines")
    po_line = models.ForeignKey(
        PurchaseOrderLine,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="receipt_lines",
    )
    material = models.ForeignKey(
        "catalog.Material", on_delete=models.PROTECT, related_name="receipt_lines"
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    uom = models.ForeignKey(
        "catalog.UnitOfMeasure", on_delete=models.PROTECT, related_name="grn_lines"
    )
    traceability_unit = models.ForeignKey(
        "inventory.TraceabilityUnit",
        on_delete=models.PROTECT,
        related_name="receipt_lines",
    )

    class Meta:
        db_table = "procurement_goods_receipt_line"
        ordering = ["grn", "pk"]
        constraints = [
            models.CheckConstraint(check=Q(quantity__gt=0), name="ck_grn_line_quantity_positive"),
        ]
