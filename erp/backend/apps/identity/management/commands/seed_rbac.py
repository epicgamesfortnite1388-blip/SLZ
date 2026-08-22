"""Seed platform RBAC data (permissions + an Admin role) and an optional
superuser. This seeds *platform* access-control data only — NO business/ERP
master data is created (that is deferred to Task 004).

Usage:
    python manage.py seed_rbac
Environment (optional) for the bootstrap superuser:
    ADMIN_EMAIL, ADMIN_PASSWORD
"""

from __future__ import annotations

import os

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.identity.models import Permission, Role, RolePermission, User

# Platform permission catalogue (module.resource.action). Business modules will
# register their own permissions later; these cover the foundation only.
PLATFORM_PERMISSIONS = [
    ("identity.user.view", "View users", "مشاهده کاربران"),
    ("identity.permission.view", "View platform permissions", "مشاهده دسترسی‌های سامانه"),
    ("identity.role.manage", "Manage roles", "مدیریت نقش‌ها"),
    ("audit.log.view", "View audit log", "مشاهده گزارش حسابرسی"),
    ("organization.company.view", "View companies", "مشاهده شرکت‌ها"),
    ("organization.company.manage", "Manage companies", "مدیریت شرکت‌ها"),
    ("organization.site.view", "View sites", "مشاهده سایت‌ها"),
    ("organization.site.manage", "Manage sites", "مدیریت سایت‌ها"),
    ("organization.department.view", "View departments", "مشاهده دپارتمان‌ها"),
    ("organization.department.manage", "Manage departments", "مدیریت دپارتمان‌ها"),
    ("documents.attachment.view", "View attachments", "مشاهده اسناد"),
    ("documents.attachment.delete", "Delete attachments", "حذف اسناد"),
    ("workflow.definition.view", "View workflow definitions", "مشاهده گردش کارها"),
    ("workflow.definition.manage", "Manage workflow definitions", "مدیریت گردش کارها"),
    ("workflow.instance.view", "View workflow instances", "مشاهده نمونه‌های گردش کار"),
    (
        "workflow.instance.manage",
        "Manage/cancel workflow instances",
        "مدیریت/لغو نمونه‌های گردش کار",
    ),
    # --- Task 004 Master Data ---------------------------------------------
    ("organization.sitecapability.view", "View site capabilities", "مشاهده توانمندی‌های سایت"),
    ("organization.sitecapability.manage", "Manage site capabilities", "مدیریت توانمندی‌های سایت"),
    ("partners.partner.view", "View partners", "مشاهده طرف‌های تجاری"),
    ("partners.partner.manage", "Manage partners", "مدیریت طرف‌های تجاری"),
    ("partners.contact.view", "View partner contacts", "مشاهده مخاطبین"),
    ("partners.contact.manage", "Manage partner contacts", "مدیریت مخاطبین"),
    ("partners.address.view", "View partner addresses", "مشاهده آدرس‌ها"),
    ("partners.address.manage", "Manage partner addresses", "مدیریت آدرس‌ها"),
    ("catalog.uom.view", "View units of measure", "مشاهده واحدهای اندازه‌گیری"),
    ("catalog.uom.manage", "Manage units of measure", "مدیریت واحدهای اندازه‌گیری"),
    ("catalog.productgroup.view", "View product groups", "مشاهده گروه‌های محصول"),
    ("catalog.productgroup.manage", "Manage product groups", "مدیریت گروه‌های محصول"),
    ("catalog.producttaxonomy.view", "View product taxonomy", "مشاهده طبقه‌بندی محصول"),
    ("catalog.producttaxonomy.manage", "Manage product taxonomy", "مدیریت طبقه‌بندی محصول"),
    ("catalog.product.view", "View products", "مشاهده محصولات"),
    ("catalog.product.manage", "Manage products", "مدیریت محصولات"),
    ("catalog.material.view", "View materials", "مشاهده مواد"),
    ("catalog.material.manage", "Manage materials", "مدیریت مواد"),
    ("hr.employee.view", "View employees", "مشاهده کارکنان"),
    ("hr.employee.manage", "Manage employees", "مدیریت کارکنان"),
    # --- Task 005 Product Engineering -------------------------------------
    ("engineering.customerproduct.view", "View customer products", "مشاهده محصولات مشتری"),
    ("engineering.customerproduct.manage", "Manage customer products", "مدیریت محصولات مشتری"),
    ("engineering.specification.view", "View product specifications", "مشاهده مشخصات فنی محصول"),
    (
        "engineering.specification.manage",
        "Manage product specifications",
        "مدیریت مشخصات فنی محصول",
    ),
    ("engineering.tooling.view", "View tooling assets", "مشاهده قالب‌ها و کلیشه‌ها"),
    ("engineering.tooling.manage", "Manage tooling assets", "مدیریت قالب‌ها و کلیشه‌ها"),
    # --- Task 006 Manufacturing (BOM & Routing) ---------------------------
    ("manufacturing.workcenter.view", "View work centers", "مشاهده مراکز کاری"),
    ("manufacturing.workcenter.manage", "Manage work centers", "مدیریت مراکز کاری"),
    ("manufacturing.machine.view", "View machines", "مشاهده ماشین‌آلات"),
    ("manufacturing.machine.manage", "Manage machines", "مدیریت ماشین‌آلات"),
    ("manufacturing.bom.view", "View bills of materials", "مشاهده فهرست مواد"),
    ("manufacturing.bom.manage", "Manage bills of materials", "مدیریت فهرست مواد"),
    ("manufacturing.routing.view", "View routings", "مشاهده مسیرهای تولید"),
    ("manufacturing.routing.manage", "Manage routings", "مدیریت مسیرهای تولید"),
    # --- Task 007 Inventory Foundation ------------------------------------
    ("inventory.warehouse.view", "View warehouses", "مشاهده انبارها"),
    ("inventory.warehouse.manage", "Manage warehouses", "مدیریت انبارها"),
    (
        "inventory.warehouseaccess.view",
        "View warehouse access",
        "مشاهده دسترسی انبار",
    ),
    (
        "inventory.warehouseaccess.manage",
        "Manage warehouse access",
        "مدیریت دسترسی انبار",
    ),
    (
        "inventory.traceability.view",
        "View traceability units and genealogy",
        "مشاهده ردیابی و شجره‌نامه",
    ),
    (
        "inventory.traceability.manage",
        "Manage traceability units and genealogy",
        "مدیریت ردیابی و شجره‌نامه",
    ),
    ("inventory.movement.view", "View stock movements", "مشاهده گردش موجودی"),
    ("inventory.movement.manage", "Post stock movements", "ثبت گردش موجودی"),
    # --- Task 008 Quality (inspection / quality plan definition) -----------
    ("quality.characteristic.view", "View quality characteristics", "مشاهده مشخصه‌های کیفی"),
    ("quality.characteristic.manage", "Manage quality characteristics", "مدیریت مشخصه‌های کیفی"),
    ("quality.plan.view", "View quality plans", "مشاهده طرح‌های کنترل کیفیت"),
    ("quality.plan.manage", "Manage quality plans", "مدیریت طرح‌های کنترل کیفیت"),
    # --- Task 009 Procurement (requisitions & purchase orders) -------------
    ("procurement.requisition.view", "View purchase requisitions", "مشاهده درخواست‌های خرید"),
    ("procurement.requisition.manage", "Manage purchase requisitions", "مدیریت درخواست‌های خرید"),
    ("procurement.order.view", "View purchase orders", "مشاهده سفارش‌های خرید"),
    ("procurement.order.manage", "Manage purchase orders", "مدیریت سفارش‌های خرید"),
    ("procurement.grn.view", "View goods receipts", "مشاهده رسیدهای خرید"),
    (
        "procurement.grn.manage",
        "Post goods receipts",
        "ثبت رسیدهای خرید",
    ),  # --- Task 010 Sales (customer orders) ----------------------------------
    ("sales.order.view", "View sales orders", "مشاهده سفارش‌های فروش"),
    ("sales.order.manage", "Manage sales orders", "مدیریت سفارش‌های فروش"),
    # --- Task 011 Production (work orders) ---------------------------------
    ("production.order.view", "View production orders", "مشاهده سفارش‌های تولید"),
    ("production.order.manage", "Manage production orders", "مدیریت سفارش‌های تولید"),
    ("production.execution.view", "View production execution", "مشاهده اجرای تولید"),
    ("production.execution.manage", "Post production execution", "ثبت اجرای تولید"),
]


class Command(BaseCommand):
    help = "Seed platform RBAC permissions, an Admin role, and an optional superuser."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        perms = []
        for code, desc_en, desc_fa in PLATFORM_PERMISSIONS:
            perm, was_created = Permission.objects.get_or_create(
                code=code,
                defaults={
                    "module": code.split(".", 1)[0],
                    "description_en": desc_en,
                    "description_fa": desc_fa,
                },
            )
            perms.append(perm)
            created += int(was_created)

        admin_role, _ = Role.objects.get_or_create(
            code="platform_admin",
            defaults={
                "name_en": "Platform Administrator",
                "name_fa": "مدیر سامانه",
                "description": "Full platform administration role.",
                "is_system": True,
            },
        )
        for perm in perms:
            RolePermission.objects.get_or_create(role=admin_role, permission=perm)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(perms)} permissions ({created} new) and role " f"'{admin_role.code}'."
            )
        )

        email = os.environ.get("ADMIN_EMAIL")
        password = os.environ.get("ADMIN_PASSWORD")
        if email and password and not User.objects.filter(email=email).exists():
            User.objects.create_superuser(email=email, password=password, full_name="Administrator")
            self.stdout.write(self.style.SUCCESS(f"Created superuser {email}."))
