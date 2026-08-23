"""Identity & RBAC models: User, Permission, Role and their assignments."""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone as dj_timezone

from apps.core.models import TimeStampedModel
from apps.identity.managers import UserManager


class Language(models.TextChoices):
    FA = "fa", "فارسی"
    EN = "en", "English"


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """Custom user with a UUID PK and locale preferences.

    ``is_superuser`` (from PermissionsMixin) bypasses RBAC checks. Business
    authorization is driven by role→permission assignments, not Django's native
    per-model permissions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=255, blank=True, default="")
    language = models.CharField(max_length=5, choices=Language.choices, default=Language.FA)
    timezone = models.CharField(max_length=64, default="Asia/Tehran")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=dj_timezone.now)

    roles = models.ManyToManyField(
        "identity.Role", through="identity.UserRole", related_name="users", blank=True
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "identity_user"
        ordering = ["email"]

    def __str__(self) -> str:
        return self.email

    def permission_codes(self, company_id: str | None = None) -> set[str]:
        """All permission codes granted through this user's roles.

        When *company_id* is provided, roles are scoped:
        - roles with ``UserRole.company_id`` matching *company_id* apply.
        - roles with ``UserRole.company_id IS NULL`` (global) always apply.
        - roles scoped to a different company are excluded.
        """
        if self.is_superuser:
            return {"*"}
        userrole_qs = UserRole.objects.filter(user=self)
        if company_id is not None:
            userrole_qs = userrole_qs.filter(
                models.Q(company_id=company_id) | models.Q(company__isnull=True),
            )
        role_ids = userrole_qs.values_list("role_id", flat=True).distinct()
        return set(
            Permission.objects.filter(roles__id__in=role_ids)
            .values_list("code", flat=True)
            .distinct()
        )

    def has_permission_code(self, code: str, company_id: str | None = None) -> bool:
        if self.is_superuser:
            return True
        userrole_qs = UserRole.objects.filter(user=self)
        if company_id is not None:
            userrole_qs = userrole_qs.filter(
                models.Q(company_id=company_id) | models.Q(company__isnull=True),
            )
        role_ids = userrole_qs.values_list("role_id", flat=True).distinct()
        return Permission.objects.filter(roles__id__in=role_ids, code=code).exists()


class Permission(TimeStampedModel):
    """A grantable capability, coded as ``module.resource.action``."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=150, unique=True)
    module = models.CharField(max_length=50)
    description_en = models.CharField(max_length=255, blank=True, default="")
    description_fa = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "identity_permission"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code

    def save(self, *args, **kwargs):
        # Derive module from the code prefix if not set explicitly.
        if not self.module and "." in self.code:
            self.module = self.code.split(".", 1)[0]
        super().save(*args, **kwargs)


class Role(TimeStampedModel):
    """A named bundle of permissions. Not hard-coded; fully data-driven."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True)
    name_en = models.CharField(max_length=150)
    name_fa = models.CharField(max_length=150)
    description = models.TextField(blank=True, default="")
    is_system = models.BooleanField(
        default=False, help_text="System roles cannot be deleted via the API."
    )
    permissions = models.ManyToManyField(
        Permission, through="identity.RolePermission", related_name="roles", blank=True
    )

    class Meta:
        db_table = "identity_role"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class RolePermission(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        db_table = "identity_role_permission"
        unique_together = ("role", "permission")


class UserRole(TimeStampedModel):
    """Link a user to a role, optionally scoped to a company.

    company=NULL → the role applies globally (across all companies the user is
    a member of).  company=<FK> → the role only applies when the user is acting
    within that specific company (Q-055).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    company = models.ForeignKey(
        "organization.Company",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        help_text="NULL = global role; set = scoped to this company only.",
    )

    class Meta:
        db_table = "identity_user_role"
        unique_together = ("user", "role", "company")


class CompanyMembership(TimeStampedModel):
    """Which companies a user may access (Q-055 answer).

    A user may belong to **multiple** companies; visibility is company-granular
    (each company currently has one site). Memberships are administered by IT —
    there is deliberately no self-service or business-side write path.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="company_memberships")
    company = models.ForeignKey(
        "organization.Company", on_delete=models.CASCADE, related_name="memberships"
    )

    class Meta:
        db_table = "identity_company_membership"
        unique_together = ("user", "company")

    def __str__(self) -> str:
        return f"{self.user_id} → {self.company_id}"
