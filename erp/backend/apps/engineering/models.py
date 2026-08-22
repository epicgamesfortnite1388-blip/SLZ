"""Product Engineering — the versioned technical specification (Task 005 core).

Scope (see docs/reconciliation/master-data-impact.md R-MD-09/13, skills/04):
A packaging product is NOT a flat SKU. It is a customer-specific, versioned
technical specification. This app owns the engineering spine:

* ``CustomerProduct`` — durable customer-specific identity (``VersionedRoot``);
  its ``code`` is a plain business number kept separate from the UUID PK. The
  SKU-DERIVATION service (SR-01) and product coding scheme are OPEN
  (Q-019 / NQ-005, do-not-build-yet #14) — NOT built here; ``code`` is entered.
* ``SpecificationRevision`` — the immutable versioned spec (``Revision``). The
  MECHANICAL lifecycle (draft -> activate -> supersede) lives in ``services``;
  the spec-revision *trigger rule* and *approver hierarchy* are OPEN
  (Q-024, do-not-build-yet #7/#13) — NOT built here.
* ``SpecLayer`` — ordered material structure (e.g. PET12 / ADH / AL7 / PE80).
* ``SpecColor`` — per-color ink formulation (main + optional alternative ink).
* ``SpecParameter`` — typed, extensible attributes (tolerances, marking,
  packaging, custom customer specs) so new requirements need no code change
  (FR-007).

* ``ToolingAsset`` — the SR-03 first-class **cliché / sheet (برگ) / set (دست)**
  printing-tooling asset: a company-scoped identity with **usage-life counters**
  and an optional link to its dedicated **cliché store** (SR-10 CLICHE
  warehouse). Confirmed identity + usage-life ONLY — the tooling COST model
  (customer-paid vs amortized) is OPEN (Q-004/036, do-not-build-yet #5) and NOT
  modelled here; automatic usage increment from a work-order confirmation is the
  gated execution layer (Q-046) and is deferred.

OPEN values stay nullable/configurable — no invented tolerance defaults
(Q-022), no hard-coded bag-type list (Q-014/020), no tooling cost model (#5).
Artwork revisions are DEFERRED to a later Task 005 phase (a separate linked
lifecycle); ``ToolingAsset.customer_product`` is the concrete confirmed link
available until the artwork model lands.
"""

from __future__ import annotations

from django.db import models

from apps.core.models import SoftDeleteModel
from apps.core.versioning import Revision, VersionedRoot


class CustomerProduct(VersionedRoot):
    """Durable, customer-specific product identity ("customer X's 1kg pouch").

    Stable across specification revisions. Company-scoped (DR-040) and tied to a
    customer Partner. ``code`` is a manual business number — the SKU-derivation
    service (SR-01, Q-019) is OPEN and deliberately not implemented.
    """

    company = models.ForeignKey(
        "organization.Company",
        on_delete=models.PROTECT,
        related_name="customer_products",
    )
    customer = models.ForeignKey(
        "partners.Partner",
        on_delete=models.PROTECT,
        related_name="customer_products",
    )
    code = models.CharField(max_length=60)
    name_fa = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    product_group = models.ForeignKey(
        "catalog.ProductGroup",
        on_delete=models.PROTECT,
        related_name="customer_products",
    )
    family = models.ForeignKey(
        "catalog.ProductFamily",
        on_delete=models.PROTECT,
        related_name="customer_products",
    )
    base_uom = models.ForeignKey(
        "catalog.UnitOfMeasure",
        on_delete=models.PROTECT,
        related_name="customer_products",
    )
    # Finished bags/pouches are carton-tracked; film products are roll/pallet
    # tracked. The setting is explicit per customer product and nullable while
    # older master records are classified.
    traceability_mode = models.CharField(
        max_length=20,
        choices=(
            ("SERIALIZED_ROLL", "Serialized roll"),
            ("CARTON", "Carton"),
        ),
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "engineering_customer_product"
        ordering = ["company", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "code"],
                name="uq_customer_product_company_code",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name_fa}"


class SpecFormat(models.TextChoices):
    ROLL_STOCK = "ROLL_STOCK", "Roll stock (رول)"
    FINISHED_BAG = "FINISHED_BAG", "Finished bag (کیسه)"
    SHEET = "SHEET", "Sheet (ورق)"


class PrintProcess(models.TextChoices):
    NONE = "NONE", "No print"
    FLEXO_SURFACE = "FLEXO_SURFACE", "Flexo — surface"
    FLEXO_REVERSE = "FLEXO_REVERSE", "Flexo — reverse"


class SurfaceFinish(models.TextChoices):
    NONE = "NONE", "None"
    MATTE = "MATTE", "Matte"
    GLOSS = "GLOSS", "Gloss"


class SpecificationRevision(Revision):
    """An immutable versioned snapshot of a customer product's engineering spec.

    ``revision_number`` is monotonic per ``root``. Content is editable ONLY while
    ``status == DRAFT`` (foundation rule); activation supersedes the prior ACTIVE
    revision. The header carries CONFIRMED dimensional/format/print attributes;
    everything extensible lives in child rows. Tolerances are nullable — SLZ's
    default tolerances are OPEN (Q-022), never invented here.
    """

    root = models.ForeignKey(
        CustomerProduct, on_delete=models.PROTECT, related_name="specifications"
    )

    # Format & dimensions (CONFIRMED attributes; tolerances OPEN -> nullable).
    spec_format = models.CharField(
        max_length=16, choices=SpecFormat.choices, default=SpecFormat.ROLL_STOCK
    )
    # bag_type list is OPEN (Q-014/020) -> free-form, NOT a hard-coded enum.
    bag_type = models.CharField(max_length=60, blank=True, default="")
    width_mm = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    width_tol_low = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    width_tol_high = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    length_mm = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    length_tol_low = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    length_tol_high = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    gusset_mm = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)

    # Printing & finishing (CONFIRMED; flexo confirmed process).
    print_process = models.CharField(
        max_length=16, choices=PrintProcess.choices, default=PrintProcess.NONE
    )
    number_of_colors = models.PositiveSmallIntegerField(null=True, blank=True)
    has_lamination = models.BooleanField(default=False)
    has_cold_seal = models.BooleanField(default=False)
    surface_finish = models.CharField(
        max_length=8, choices=SurfaceFinish.choices, default=SurfaceFinish.NONE
    )

    class Meta:
        db_table = "engineering_specification_revision"
        ordering = ["root", "revision_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["root", "revision_number"],
                name="uq_spec_revision_root_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.root_id} v{self.revision_number} [{self.status}]"


class LayerFunction(models.TextChoices):
    SUBSTRATE = "SUBSTRATE", "Substrate"
    ADHESIVE = "ADHESIVE", "Adhesive"
    SEALANT = "SEALANT", "Sealant"
    BARRIER = "BARRIER", "Barrier"
    PRINT = "PRINT", "Print layer"
    OTHER = "OTHER", "Other"


class SpecLayer(SoftDeleteModel):
    """One layer of the ordered material structure (per-layer micron + tolerance).

    Editable only while the parent revision is DRAFT (enforced in the service
    layer). ``material`` references the material master (PROTECT — never erase
    history).
    """

    revision = models.ForeignKey(
        SpecificationRevision, on_delete=models.CASCADE, related_name="layers"
    )
    sequence = models.PositiveSmallIntegerField()
    material = models.ForeignKey(
        "catalog.Material", on_delete=models.PROTECT, related_name="spec_layers"
    )
    function = models.CharField(
        max_length=16, choices=LayerFunction.choices, default=LayerFunction.SUBSTRATE
    )
    micron = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    micron_tol_low = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    micron_tol_high = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)

    class Meta:
        db_table = "engineering_spec_layer"
        ordering = ["revision", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["revision", "sequence"], name="uq_spec_layer_revision_sequence"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.revision_id} L{self.sequence}:{self.material_id}"


class SpecColor(SoftDeleteModel):
    """Per-color ink formulation for a printed spec (main + optional alternative).

    ``ink``/``alternative_ink`` must reference INK-subtype materials (validated in
    the serializer). Ink/solvent formulation formulas beyond identity are OPEN and
    not computed here.
    """

    revision = models.ForeignKey(
        SpecificationRevision, on_delete=models.CASCADE, related_name="colors"
    )
    sequence = models.PositiveSmallIntegerField()
    color_name = models.CharField(max_length=120)
    ink = models.ForeignKey(
        "catalog.Material", on_delete=models.PROTECT, related_name="spec_colors"
    )
    alternative_ink = models.ForeignKey(
        "catalog.Material",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="spec_colors_alternative",
    )
    coverage_pct = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    delta_e_tol = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)

    class Meta:
        db_table = "engineering_spec_color"
        ordering = ["revision", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["revision", "sequence"], name="uq_spec_color_revision_sequence"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.revision_id} C{self.sequence}:{self.color_name}"


class ParamDatatype(models.TextChoices):
    TEXT = "TEXT", "Text"
    NUMBER = "NUMBER", "Number"
    BOOL = "BOOL", "Boolean"


class SpecParameter(SoftDeleteModel):
    """Typed, extensible spec attribute (FR-007).

    Covers toleranced attributes, per-level marking, packaging/delivery spec and
    arbitrary customer-specific requirements without schema changes. Numeric
    values use ``value_number`` (Decimal) with optional unit + tolerance; text and
    boolean values use their own columns.
    """

    revision = models.ForeignKey(
        SpecificationRevision, on_delete=models.CASCADE, related_name="parameters"
    )
    key = models.CharField(max_length=120)
    datatype = models.CharField(
        max_length=8, choices=ParamDatatype.choices, default=ParamDatatype.TEXT
    )
    value_text = models.CharField(max_length=500, blank=True, default="")
    value_number = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    value_bool = models.BooleanField(null=True, blank=True)
    unit = models.CharField(max_length=30, blank=True, default="")
    tol_low = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    tol_high = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = "engineering_spec_parameter"
        ordering = ["revision", "key"]
        constraints = [
            models.UniqueConstraint(
                fields=["revision", "key"], name="uq_spec_parameter_revision_key"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.revision_id}:{self.key}"


class ToolingType(models.TextChoices):
    """The printing-tooling identities SLZ issues ID cards for (SR-03).

    Cliché / sheet (برگ) / set (دست) are the three tooling grains SLZ tracks.
    Adding a grain is adding a choice, not code.
    """

    CLICHE = "CLICHE", "Cliché (کلیشه)"
    SHEET = "SHEET", "Sheet (برگ)"
    SET = "SET", "Set (دست)"


class ToolingStatus(models.TextChoices):
    """Lifecycle of a tooling asset — kept intentionally minimal.

    A generic active/retired lifecycle; no worn/scrap sub-states are invented
    (that would presuppose the OPEN usage-life-exhaustion policy). Transitions
    are driven by the ``services`` retire/reactivate use-cases so every change is
    audited (EntityUpdated).
    """

    ACTIVE = "ACTIVE", "Active"
    RETIRED = "RETIRED", "Retired"


class ToolingAsset(SoftDeleteModel):
    """A cliché / sheet / set printing-tooling asset (SR-03).

    A first-class, company-scoped (DR-040) asset tied to a customer and,
    optionally, to the specific ``CustomerProduct`` it prints. It carries
    **usage-life counters** (``usage_life_limit`` / ``usage_count``) and may live
    in a dedicated **cliché store** (SR-10 ``WarehouseStoreType.CLICHE``).

    Scope discipline: this is the CONFIRMED identity + usage-life layer only.
    The tooling **cost model** (customer-paid vs amortized) is OPEN (Q-004/036,
    do-not-build-yet #5) and is deliberately NOT modelled. Automatic
    ``usage_count`` increment on a work-order/operation confirmation belongs to
    the gated execution layer (Q-046) and is deferred; ``usage_count`` is plain
    audited master data here.
    """

    company = models.ForeignKey(
        "organization.Company",
        on_delete=models.PROTECT,
        related_name="tooling_assets",
    )
    customer = models.ForeignKey(
        "partners.Partner",
        on_delete=models.PROTECT,
        related_name="tooling_assets",
    )
    # Optional link to the specific product this tooling prints. Kept nullable
    # because the artwork model (which formally binds tooling to a design) is a
    # deferred later phase; a set may also be created before its product exists.
    customer_product = models.ForeignKey(
        CustomerProduct,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="tooling_assets",
    )
    code = models.CharField(max_length=60)
    name_fa = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    tooling_type = models.CharField(
        max_length=10, choices=ToolingType.choices, default=ToolingType.CLICHE
    )
    status = models.CharField(
        max_length=10, choices=ToolingStatus.choices, default=ToolingStatus.ACTIVE
    )
    # Usage-life: the limit is OPEN in *how* it is measured (impressions? runs?)
    # so it stays nullable — never invent a default. ``usage_count`` is the
    # recorded usage so far.
    usage_life_limit = models.PositiveIntegerField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    # Dedicated cliché store (SR-10). Optional; validated to be a CLICHE store
    # in the same company by the serializer. A location pointer only — no stock
    # quantity/movement (that is the gated Q-046 layer).
    warehouse = models.ForeignKey(
        "inventory.Warehouse",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="tooling_assets",
    )
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "engineering_tooling_asset"
        ordering = ["company", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "code"],
                name="uq_tooling_asset_company_code",
            ),
        ]

    @property
    def is_life_exceeded(self) -> bool:
        """True once recorded usage reaches the configured life limit.

        A pure arithmetic helper (no invented policy): if no limit is set the
        asset is never considered exceeded.
        """
        return self.usage_life_limit is not None and self.usage_count >= self.usage_life_limit

    def __str__(self) -> str:
        return f"{self.code} — {self.name_fa}"
