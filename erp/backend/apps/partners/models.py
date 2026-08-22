"""Commercial partners master data (customers & suppliers).

A Partner is a company-scoped party (DR-040) that plays one or more roles —
customer and/or supplier — with attached contacts and addresses. Role-specific
data lives in the ``Customer``/``Supplier`` one-to-one extensions.

Scope note (Task 004): identity + roles + sanction flag + a supplier-evaluation
*stub* + a customer sales-line link only. CRM (leads/opportunities/complaints),
credit management, and settlement terms are DEFERRED (NQ-009 / finance phase).
Parametric values such as delivery tolerance (DR-028) stay nullable/configurable
— no invented defaults.
"""

from __future__ import annotations

from django.db import models

from apps.core.models import SoftDeleteModel


class Partner(SoftDeleteModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="partners"
    )
    code = models.CharField(max_length=40)
    name_fa = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    legal_name = models.CharField(max_length=255, blank=True, default="")
    national_id = models.CharField(max_length=30, blank=True, default="")
    economic_code = models.CharField(max_length=30, blank=True, default="")

    is_customer = models.BooleanField(default=False)
    is_supplier = models.BooleanField(default=False)
    # Sanction/FX awareness is a real SLZ constraint (NFR-022 / SR context).
    is_sanctioned = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "partner"
        ordering = ["company", "code"]
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="uq_partner_company_code"),
            models.CheckConstraint(
                check=models.Q(is_customer=True) | models.Q(is_supplier=True),
                name="ck_partner_has_role",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name_fa}"


class Customer(SoftDeleteModel):
    """Customer role extension of a Partner (R-MD-04)."""

    partner = models.OneToOneField(
        Partner, on_delete=models.CASCADE, related_name="customer_profile"
    )
    # Sales line = the product group a customer is handled under (drives CRM/RBAC).
    sales_line = models.ForeignKey(
        "catalog.ProductGroup",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="customers",
    )
    # DR-028 over/under-delivery tolerance is OPEN — kept configurable, no default.
    delivery_tolerance_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    requires_coa = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "partner_customer"

    def __str__(self) -> str:
        return f"Customer:{self.partner.code}"


class Supplier(SoftDeleteModel):
    """Supplier role extension of a Partner — evaluation stub only (R-MD-04)."""

    partner = models.OneToOneField(
        Partner, on_delete=models.CASCADE, related_name="supplier_profile"
    )
    is_approved = models.BooleanField(default=False)
    # Evaluation stub; full supplier-evaluation workflow is a later phase.
    evaluation_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    lead_time_days = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "partner_supplier"

    def __str__(self) -> str:
        return f"Supplier:{self.partner.code}"


class ContactKind(models.TextChoices):
    GENERAL = "GENERAL", "General"
    SALES = "SALES", "Sales"
    TECHNICAL = "TECHNICAL", "Technical"
    FINANCE = "FINANCE", "Finance"
    LOGISTICS = "LOGISTICS", "Logistics"


class Contact(SoftDeleteModel):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=120, blank=True, default="")
    kind = models.CharField(max_length=16, choices=ContactKind.choices, default=ContactKind.GENERAL)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=40, blank=True, default="")
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "partner_contact"
        ordering = ["partner", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.partner.code})"


class AddressKind(models.TextChoices):
    BILLING = "BILLING", "Billing"
    SHIPPING = "SHIPPING", "Shipping"
    OTHER = "OTHER", "Other"


class Address(SoftDeleteModel):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="addresses")
    kind = models.CharField(
        max_length=16, choices=AddressKind.choices, default=AddressKind.SHIPPING
    )
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=120, blank=True, default="")
    province = models.CharField(max_length=120, blank=True, default="")
    postal_code = models.CharField(max_length=20, blank=True, default="")
    country = models.CharField(max_length=2, default="IR")
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "partner_address"
        ordering = ["partner", "kind"]
        verbose_name_plural = "addresses"

    def __str__(self) -> str:
        return f"{self.get_kind_display()} — {self.partner.code}"
