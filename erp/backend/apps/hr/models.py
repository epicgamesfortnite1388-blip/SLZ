"""Minimal Employee master (R-MD-06).

Justified early for operator identity and warehouse/user access; full HR
(decrees, payroll, attendance) is DEFERRED to a later HR domain. Company/site
scoped (DR-040); optionally linked to a login ``User``.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import SoftDeleteModel


class Employee(SoftDeleteModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="employees"
    )
    site = models.ForeignKey(
        "organization.Site",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employees",
    )
    department = models.ForeignKey(
        "organization.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employees",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employee_profile",
    )
    employee_code = models.CharField(max_length=40)
    first_name_fa = models.CharField(max_length=120)
    last_name_fa = models.CharField(max_length=120)
    first_name_en = models.CharField(max_length=120, blank=True, default="")
    last_name_en = models.CharField(max_length=120, blank=True, default="")
    job_title = models.CharField(max_length=120, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "hr_employee"
        ordering = ["company", "employee_code"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "employee_code"], name="uq_employee_company_code"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.employee_code} — {self.first_name_fa} {self.last_name_fa}"
