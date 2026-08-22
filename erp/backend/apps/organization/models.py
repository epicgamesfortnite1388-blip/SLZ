"""Organization model: Company -> Site -> Department.

Generic structural scaffolding only — no manufacturing/business semantics.
Bilingual names (fa/en) are first-class. Each entity carries an optional
``timezone`` so datetimes can be rendered per site.
"""

from __future__ import annotations

from django.db import models

from apps.core.models import SoftDeleteModel


class Company(SoftDeleteModel):
    code = models.CharField(max_length=30, unique=True)
    name_en = models.CharField(max_length=200)
    name_fa = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "org_company"
        ordering = ["code"]
        verbose_name_plural = "companies"

    def __str__(self) -> str:
        return self.name_en or self.code


class Site(SoftDeleteModel):
    """A physical facility/plant belonging to a company."""

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="sites")
    code = models.CharField(max_length=30)
    name_en = models.CharField(max_length=200)
    name_fa = models.CharField(max_length=200)
    timezone = models.CharField(max_length=64, default="Asia/Tehran")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "org_site"
        ordering = ["company", "code"]
        unique_together = ("company", "code")

    def __str__(self) -> str:
        return f"{self.company.code}/{self.code}"


class Department(SoftDeleteModel):
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name="departments")
    code = models.CharField(max_length=30)
    name_en = models.CharField(max_length=200)
    name_fa = models.CharField(max_length=200)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "org_department"
        ordering = ["site", "code"]
        unique_together = ("site", "code")

    def __str__(self) -> str:
        return f"{self.site}/{self.code}"


class ProductionCapability(models.TextChoices):
    """Production stages a site may be able to perform.

    Grounded in the confirmed SLZ capability baseline (skill 01 / SR-15):
    Tehran (SLZ) runs the full chain; Saveh (Helena) is blown-film + cutting/sewing
    only. Capability is *declared per site* — feasibility and routing must respect
    it. Do not assume every site can run every stage.
    """

    BLOWN_FILM = "BLOWN_FILM", "Blown film"
    CAST_FILM = "CAST_FILM", "Cast film"
    EXTRUSION_LAMINATION = "EXTRUSION_LAMINATION", "Extrusion / lamination"
    PREPRESS = "PREPRESS", "Prepress & color matching"
    FLEXO_PRINTING = "FLEXO_PRINTING", "Flexo printing"
    LAMINATION = "LAMINATION", "Lamination"
    COLD_SEAL = "COLD_SEAL", "Cold seal"
    SLITTING = "SLITTING", "Slitting / rewinding"
    CONVERTING = "CONVERTING", "Converting / bag-making"
    RECYCLING_GRINDING = "RECYCLING_GRINDING", "Recycling / grinding"
    CUTTING_SEWING = "CUTTING_SEWING", "Cutting / sewing"
    WAREHOUSING = "WAREHOUSING", "Warehousing / logistics"


class SiteCapability(SoftDeleteModel):
    """A production stage a given site is able to perform (SR-15 / DR-041).

    Master data only: declares *what a site can do*. Capacity numbers,
    machine-settings and allowed-scrap tables (SR-05) are a later manufacturing
    concern and are intentionally NOT modeled here.
    """

    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name="capabilities")
    capability = models.CharField(max_length=32, choices=ProductionCapability.choices)
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "org_site_capability"
        ordering = ["site", "capability"]
        unique_together = ("site", "capability")
        verbose_name_plural = "site capabilities"

    def __str__(self) -> str:
        return f"{self.site}:{self.capability}"
