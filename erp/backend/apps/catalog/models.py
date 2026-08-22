"""Catalog master data: units of measure, product taxonomy, product & material.

Scope note (Task 004) — see docs/reconciliation/master-data-impact.md:
* Product is a THIN classified master (identity + taxonomy + base UoM). The rich
  versioned specification, formulations, drawings, marking, cliché and the
  SKU-derivation service are DEFERRED to Product Engineering (Task 005, SR-01/02).
  Do NOT add spec/BOM/price/stock fields here.
* Material carries a subtype discriminator (SR-04 / DR-042) because MRP,
  formulation and QC treat resin/ink/solvent/regrind distinctly. Planning
  numbers (reorder/safety/lead-time) are optional and configurable — MRP logic
  itself is a later phase.
* Multi-level taxonomy type -> class -> family + product group (SR-02 / DR-044).
"""

from __future__ import annotations

from django.db import models

from apps.core.models import SoftDeleteModel


class UomDimension(models.TextChoices):
    COUNT = "COUNT", "Count"
    LENGTH = "LENGTH", "Length"
    AREA = "AREA", "Area"
    MASS = "MASS", "Mass"
    VOLUME = "VOLUME", "Volume"
    TIME = "TIME", "Time"


class UnitOfMeasure(SoftDeleteModel):
    code = models.CharField(max_length=20, unique=True)
    name_fa = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120, blank=True, default="")
    dimension = models.CharField(max_length=12, choices=UomDimension.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "catalog_uom"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class UomConversion(SoftDeleteModel):
    """1 ``from_uom`` = ``factor`` x ``to_uom`` (both must share a dimension)."""

    from_uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT, related_name="conversions_from"
    )
    to_uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT, related_name="conversions_to"
    )
    factor = models.DecimalField(max_digits=20, decimal_places=8)

    class Meta:
        db_table = "catalog_uom_conversion"
        constraints = [
            models.UniqueConstraint(fields=["from_uom", "to_uom"], name="uq_uom_conversion_pair"),
            models.CheckConstraint(
                check=~models.Q(from_uom=models.F("to_uom")),
                name="ck_uom_conversion_distinct",
            ),
            models.CheckConstraint(
                check=models.Q(factor__gt=0), name="ck_uom_conversion_factor_positive"
            ),
        ]

    def __str__(self) -> str:
        return f"1 {self.from_uom_id} = {self.factor} {self.to_uom_id}"


class ProductGroup(SoftDeleteModel):
    """Top commercial grouping; also structures sales lines & CRM (SR-02)."""

    code = models.CharField(max_length=40, unique=True)
    name_fa = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "catalog_product_group"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class ProductType(SoftDeleteModel):
    """Level 1 of the taxonomy (نوع)."""

    code = models.CharField(max_length=40, unique=True)
    name_fa = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "catalog_product_type"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class ProductClass(SoftDeleteModel):
    """Level 2 of the taxonomy (طبقه), under a ProductType."""

    product_type = models.ForeignKey(ProductType, on_delete=models.PROTECT, related_name="classes")
    code = models.CharField(max_length=40)
    name_fa = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "catalog_product_class"
        ordering = ["product_type", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["product_type", "code"], name="uq_product_class_type_code"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product_type_id}/{self.code}"


class ProductFamily(SoftDeleteModel):
    """Level 3 of the taxonomy (خانواده), under a ProductClass."""

    product_class = models.ForeignKey(
        ProductClass, on_delete=models.PROTECT, related_name="families"
    )
    code = models.CharField(max_length=40)
    name_fa = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "catalog_product_family"
        ordering = ["product_class", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["product_class", "code"], name="uq_product_family_class_code"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product_class}/{self.code}"


class Product(SoftDeleteModel):
    """THIN classified product master (identity + taxonomy + base UoM).

    Company-scoped (DR-040). ``code`` is the human product/SKU number; in Task 005
    it will be *derived* by the SKU-generation service (SR-01), but here it is a
    plain, optional business number kept separate from the UUID PK. No spec / BOM /
    price / stock — those belong to Product Engineering / later domains.
    """

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="products"
    )
    code = models.CharField(max_length=60, blank=True, default="")
    name_fa = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    product_group = models.ForeignKey(
        ProductGroup, on_delete=models.PROTECT, related_name="products"
    )
    family = models.ForeignKey(ProductFamily, on_delete=models.PROTECT, related_name="products")
    base_uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name="products")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "catalog_product"
        ordering = ["company", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "code"],
                condition=~models.Q(code=""),
                name="uq_product_company_code",
            ),
        ]

    def __str__(self) -> str:
        return self.code or self.name_fa


class MaterialSubtype(models.TextChoices):
    """Material subtypes MRP/formulation/QC treat distinctly (SR-04 / DR-042)."""

    RESIN_MASTERBATCH = "RESIN_MASTERBATCH", "Resin / masterbatch"
    INK = "INK", "Ink (مرکب)"
    SOLVENT = "SOLVENT", "Solvent (حلال)"
    CONSUMABLE = "CONSUMABLE", "Consumable"
    PACKAGING = "PACKAGING", "Packaging"
    REGRIND = "REGRIND", "Regrind (recycled)"
    SEMI_FINISHED = "SEMI_FINISHED", "Semi-finished"
    FINISHED = "FINISHED", "Finished"


class Material(SoftDeleteModel):
    """Material master with a load-bearing subtype discriminator (SR-04).

    Planning attributes are OPTIONAL and configurable — no invented defaults;
    the MRP that consumes them is a later phase.
    """

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="materials"
    )
    code = models.CharField(max_length=60)
    name_fa = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    subtype = models.CharField(max_length=20, choices=MaterialSubtype.choices)
    base_uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name="materials")

    # Optional planning / handling attributes (R-MD-10) — nullable, no defaults.
    reorder_point = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    safety_stock = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    min_stock = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    max_stock = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    lead_time_days = models.PositiveIntegerField(null=True, blank=True)
    shelf_life_days = models.PositiveIntegerField(null=True, blank=True)
    is_hazardous = models.BooleanField(default=False)
    msds_ref = models.CharField(max_length=120, blank=True, default="")

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "catalog_material"
        ordering = ["company", "code"]
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="uq_material_company_code"),
        ]

    def __str__(self) -> str:
        return f"{self.code} ({self.subtype})"
