"""Seed a realistic demo dataset so new developers see a populated dashboard.

Usage:
    python manage.py seed_demo_data

Creates one company with full master data, partners, engineering definitions,
work centers, machines, BOMs, routings, purchase orders, sales orders, and
production orders — enough to explore every module.

Idempotent: running the command again skips objects that already exist (matched
by unique business keys like company.code, material company+code, etc.).
"""

from __future__ import annotations

from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import (
    Material,
    MaterialSubtype,
    Product,
    ProductClass,
    ProductFamily,
    ProductGroup,
    ProductType,
    TraceabilityMode,
    UnitOfMeasure,
    UomDimension,
)
from apps.engineering.models import (
    CustomerProduct,
    LayerFunction,
    PrintProcess,
    SpecColor,
    SpecFormat,
    SpecificationRevision,
    SpecLayer,
    SurfaceFinish,
)
from apps.identity.models import CompanyMembership, Role, User, UserRole
from apps.inventory.models import Warehouse, WarehouseStoreType
from apps.manufacturing.models import (
    BillOfMaterials,
    BomLine,
    BomRevision,
    Machine,
    Routing,
    RoutingOperation,
    RoutingRevision,
    WorkCenter,
)
from apps.organization.models import Company, ProductionCapability, Site, SiteCapability
from apps.partners.models import Customer, Partner, Supplier
from apps.procurement.models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
from apps.production.models import ProductionOrder
from apps.sales.models import SalesOrder, SalesOrderLine, SalesOrderStatus

TODAY = date.today()


class Command(BaseCommand):
    help = "Seed a realistic demo dataset for development and onboarding."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data …")

        # ── 1. Company ──────────────────────────────────────────────────
        company, _ = Company.objects.get_or_create(
            code="SLZ",
            defaults={
                "name_en": "SLZ Packaging Co.",
                "name_fa": "شرکت بسته‌بندی SLZ",
                "is_active": True,
            },
        )

        # ── 2. Site ─────────────────────────────────────────────────────
        site, _ = Site.objects.get_or_create(
            company=company,
            code="TEH",
            defaults={
                "name_en": "Tehran Main Plant",
                "name_fa": "کارخانه تهران",
                "timezone": "Asia/Tehran",
                "is_active": True,
            },
        )

        # ── 3. Site capabilities ────────────────────────────────────────
        for cap in (
            ProductionCapability.BLOWN_FILM,
            ProductionCapability.EXTRUSION_LAMINATION,
            ProductionCapability.FLEXO_PRINTING,
            ProductionCapability.LAMINATION,
            ProductionCapability.SLITTING,
            ProductionCapability.CONVERTING,
            ProductionCapability.RECYCLING_GRINDING,
            ProductionCapability.WAREHOUSING,
        ):
            SiteCapability.objects.get_or_create(
                site=site, capability=cap, defaults={"is_active": True}
            )

        # ── 4. Warehouses ───────────────────────────────────────────────
        wh_config = [
            (
                "RM-01",
                "انبار مواد اولیه",
                "Raw Material Warehouse",
                WarehouseStoreType.RAW_MATERIAL,
            ),
            ("WIP-01", "انبار نیم‌ساخته", "WIP Warehouse", WarehouseStoreType.WIP),
            ("FG-01", "انبار محصول", "Finished Goods Warehouse", WarehouseStoreType.FINISHED_GOODS),
            ("QC-01", "انبار قرنطینه", "Quarantine Warehouse", WarehouseStoreType.QUARANTINE),
            ("SCR-01", "انبار ضایعات", "Scrap Warehouse", WarehouseStoreType.SCRAP),
            ("CL-01", "انبار کلیشه", "Cliché Store", WarehouseStoreType.CLICHE),
        ]
        warehouses = {}
        for code, fa, en, st in wh_config:
            wh, _ = Warehouse.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    "site": site,
                    "name_fa": fa,
                    "name_en": en,
                    "store_type": st,
                },
            )
            warehouses[st] = wh

        # ── 5. Units of measure ─────────────────────────────────────────
        uom_config = [
            ("KG", "کیلوگرم", "Kilogram", UomDimension.MASS),
            ("M", "متر", "Meter", UomDimension.LENGTH),
            ("PCS", "عدد", "Piece", UomDimension.COUNT),
            ("ROLL", "رول", "Roll", UomDimension.COUNT),
            ("CARTON", "کارتن", "Carton", UomDimension.COUNT),
            ("TON", "تن", "Ton (1000 kg)", UomDimension.MASS),
        ]
        uoms = {}
        for code, fa, en, dim in uom_config:
            uom, _ = UnitOfMeasure.objects.get_or_create(
                code=code,
                defaults={"name_fa": fa, "name_en": en, "dimension": dim},
            )
            uoms[code] = uom

        # ── 6. Product taxonomy ─────────────────────────────────────────
        prod_type, _ = ProductType.objects.get_or_create(
            code="PACK",
            defaults={"name_fa": "بسته‌بندی", "name_en": "Packaging"},
        )
        prod_class, _ = ProductClass.objects.get_or_create(
            product_type=prod_type,
            code="FLEX",
            defaults={"name_fa": "بسته‌بندی انعطاف‌پذیر", "name_en": "Flexible packaging"},
        )
        prod_family, _ = ProductFamily.objects.get_or_create(
            product_class=prod_class,
            code="FILM",
            defaults={"name_fa": "فیلم و رول", "name_en": "Film & Rolls"},
        )

        prod_group, _ = ProductGroup.objects.get_or_create(
            code="IND",
            defaults={"name_fa": "صنعتی", "name_en": "Industrial"},
        )

        # ── 7. Materials ────────────────────────────────────────────────
        mat_config = [
            (
                "PE-LD",
                "گرانول پلی‌اتیلن سبک",
                "LDPE Granule",
                MaterialSubtype.RESIN_MASTERBATCH,
                TraceabilityMode.BATCH,
                "KG",
            ),
            (
                "PE-LLD",
                "گرانول پلی‌اتیلن خطی",
                "LLDPE Granule",
                MaterialSubtype.RESIN_MASTERBATCH,
                TraceabilityMode.BATCH,
                "KG",
            ),
            (
                "BOPP-20",
                "فیلم BOPP 20 میکرون",
                "BOPP Film 20µ",
                MaterialSubtype.SEMI_FINISHED,
                TraceabilityMode.SERIALIZED_ROLL,
                "ROLL",
            ),
            (
                "PET-12",
                "فیلم PET 12 میکرون",
                "PET Film 12µ",
                MaterialSubtype.SEMI_FINISHED,
                TraceabilityMode.SERIALIZED_ROLL,
                "ROLL",
            ),
            (
                "PE-FILM80",
                "فیلم PE 80 میکرون",
                "PE Film 80µ",
                MaterialSubtype.SEMI_FINISHED,
                TraceabilityMode.SERIALIZED_ROLL,
                "ROLL",
            ),
            ("INK-BLK", "مرکب مشکی", "Black Ink", MaterialSubtype.INK, None, "KG"),
            ("INK-CYN", "مرکب فیروزه‌ای", "Cyan Ink", MaterialSubtype.INK, None, "KG"),
            ("INK-MAG", "مرکب قرمز", "Magenta Ink", MaterialSubtype.INK, None, "KG"),
            ("INK-YEL", "مرکب زرد", "Yellow Ink", MaterialSubtype.INK, None, "KG"),
            (
                "SOL-001",
                "حلال اتیل استات",
                "Ethyl Acetate Solvent",
                MaterialSubtype.SOLVENT,
                None,
                "KG",
            ),
            (
                "ADH-001",
                "چسب لمینیت",
                "Lamination Adhesive",
                MaterialSubtype.CONSUMABLE,
                None,
                "KG",
            ),
            (
                "PE-RECYCLE",
                "گرانول بازیافتی PE",
                "Recycled PE Granule",
                MaterialSubtype.REGRIND,
                TraceabilityMode.BATCH,
                "KG",
            ),
        ]
        materials = {}
        for code, fa, en, sub, tmode, uom_code in mat_config:
            mat, _ = Material.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    "name_fa": fa,
                    "name_en": en,
                    "subtype": sub,
                    "traceability_mode": tmode,
                    "base_uom": uoms[uom_code],
                },
            )
            materials[code] = mat

        # ── 8. Products ─────────────────────────────────────────────────
        product_config = [
            ("FP-001", "فیلم لمینت BOPP/PET/PE", "BOPP/PET/PE Laminated Film", "ROLL"),
            ("FP-002", "کیسه PE چاپدار", "Printed PE Bag", "CARTON"),
        ]
        products = {}
        for code, fa, en, uom_code in product_config:
            prod, _ = Product.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    "name_fa": fa,
                    "name_en": en,
                    "product_group": prod_group,
                    "family": prod_family,
                    "base_uom": uoms[uom_code],
                },
            )
            products[code] = prod

        # ── 9. Partners ─────────────────────────────────────────────────
        # Supplier
        supp_partner, _ = Partner.objects.get_or_create(
            company=company,
            code="SUP-001",
            defaults={
                "name_fa": "آریا پلیمر",
                "name_en": "Arya Polymer Co.",
                "legal_name": "Arya Polymer Industries",
                "is_supplier": True,
                "is_customer": False,
                "national_id": "1010101010",
                "economic_code": "411111111111",
            },
        )
        supplier, _ = Supplier.objects.get_or_create(
            partner=supp_partner,
            defaults={"is_approved": True, "lead_time_days": 14},
        )

        # Customer
        cust_partner, _ = Partner.objects.get_or_create(
            company=company,
            code="CUST-001",
            defaults={
                "name_fa": "گلرنگ",
                "name_en": "Golrang Co.",
                "legal_name": "Golrang Industrial Group",
                "is_customer": True,
                "is_supplier": False,
                "national_id": "2020202020",
            },
        )
        customer, _ = Customer.objects.get_or_create(
            partner=cust_partner,
            defaults={"sales_line": prod_group, "requires_coa": True},
        )

        # ── 10. Customer Products ────────────────────────────────────────
        cp_config = [
            (
                "CP-001",
                "فیلم لمینت گلرنگ",
                "Golrang Laminated Film",
                cust_partner,
                "ROLL",
                TraceabilityMode.SERIALIZED_ROLL,
            ),
            (
                "CP-002",
                "کیسه 1kg گلرنگ",
                "Golrang 1kg Bag",
                cust_partner,
                "PCS",
                TraceabilityMode.CARTON,
            ),
        ]
        customer_products = {}
        for code, fa, en, partner, uom_code, tmode in cp_config:
            cp, _ = CustomerProduct.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    "name_fa": fa,
                    "name_en": en,
                    "customer": partner,
                    "product_group": prod_group,
                    "family": prod_family,
                    "base_uom": uoms[uom_code],
                    "traceability_mode": tmode,
                },
            )
            customer_products[code] = cp

        # ── 11. Specification Revisions ──────────────────────────────────
        # Product 1: BOPP/PET/PE laminated film
        spec1, _ = SpecificationRevision.objects.get_or_create(
            root=customer_products["CP-001"],
            revision_number=1,
            defaults={
                "spec_format": SpecFormat.ROLL_STOCK,
                "width_mm": 620,
                "length_mm": 4000,
                "print_process": PrintProcess.FLEXO_REVERSE,
                "number_of_colors": 7,
                "has_lamination": True,
                "surface_finish": SurfaceFinish.GLOSS,
                "status": "ACTIVE",
            },
        )

        # Layers for product 1
        layer_configs_1 = [
            (1, "BOPP-20", LayerFunction.PRINT, 20),
            (2, "ADH-001", LayerFunction.ADHESIVE, None),
            (3, "PET-12", LayerFunction.BARRIER, 12),
            (4, "ADH-001", LayerFunction.ADHESIVE, None),
            (5, "PE-FILM80", LayerFunction.SEALANT, 80),
        ]
        for seq, mat_code, func, micron in layer_configs_1:
            SpecLayer.objects.get_or_create(
                revision=spec1,
                sequence=seq,
                defaults={
                    "material": materials[mat_code],
                    "function": func,
                    "micron": micron,
                },
            )

        # Colors for product 1
        color_configs_1 = [
            (1, "Black", "INK-BLK"),
            (2, "Cyan", "INK-CYN"),
            (3, "Magenta", "INK-MAG"),
            (4, "Yellow", "INK-YEL"),
        ]
        for seq, name, ink_code in color_configs_1:
            SpecColor.objects.get_or_create(
                revision=spec1,
                sequence=seq,
                defaults={"color_name": name, "ink": materials[ink_code]},
            )

        # Product 2: PE bag
        spec2, _ = SpecificationRevision.objects.get_or_create(
            root=customer_products["CP-002"],
            revision_number=1,
            defaults={
                "spec_format": SpecFormat.FINISHED_BAG,
                "width_mm": 180,
                "length_mm": 280,
                "gusset_mm": 60,
                "bag_type": "Side-gusset",
                "print_process": PrintProcess.FLEXO_SURFACE,
                "number_of_colors": 7,
                "surface_finish": SurfaceFinish.MATTE,
                "status": "ACTIVE",
            },
        )

        # Layers for product 2 (single PE layer)
        SpecLayer.objects.get_or_create(
            revision=spec2,
            sequence=1,
            defaults={
                "material": materials["PE-FILM80"],
                "function": LayerFunction.SUBSTRATE,
                "micron": 80,
            },
        )

        # Colors for product 2
        for seq, name, ink_code in color_configs_1:
            SpecColor.objects.get_or_create(
                revision=spec2,
                sequence=seq,
                defaults={"color_name": name, "ink": materials[ink_code]},
            )

        # ── 12. Work Centers & Machines ──────────────────────────────────
        wc_config = [
            ("EXT", "اکستروژن", "Extrusion", 1),
            ("PRINT", "چاپ", "Printing", 2),
            ("LAM", "لمینیت", "Lamination", 3),
            ("SLIT", "اسلیت", "Slitting", 4),
            ("CONV", "تبدیل", "Converting / Bag-making", 5),
        ]
        work_centers = {}
        for code, fa, en, seq_hint in wc_config:
            wc, _ = WorkCenter.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    "site": site,
                    "name_fa": fa,
                    "name_en": en,
                    "sequence_hint": seq_hint,
                },
            )
            work_centers[code] = wc

        # Machines
        machine_config = [
            (
                "M-EXT01",
                "اکسترودر ۱",
                "Extruder 1",
                "EXT",
                {"web_width_mm": 1800, "thickness_um": "20-200"},
            ),
            (
                "M-PRT01",
                "فلکسو ۱",
                "Flexo Press 1",
                "PRINT",
                {"web_width_mm": 1200, "color_stations": 8},
            ),
            ("M-LAM01", "لمینتور ۱", "Laminator 1", "LAM", {"web_width_mm": 1400}),
            ("M-SLT01", "اسلیتر ۱", "Slitter 1", "SLIT", {"web_width_mm": 1600}),
            ("M-CNV01", "کیسه‌زن ۱", "Bag Machine 1", "CONV", {"max_bag_width_mm": 500}),
        ]
        for code, fa, en, wc_code, profile in machine_config:
            Machine.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    "site": site,
                    "work_center": work_centers[wc_code],
                    "name_fa": fa,
                    "name_en": en,
                    "capability_profile": profile,
                },
            )

        # ── 13. BOMs ─────────────────────────────────────────────────────
        # BOM 1: multilayer film
        bom1, _ = BillOfMaterials.objects.get_or_create(
            spec_revision=spec1,
            output_material=materials["PE-FILM80"],
        )
        bom1_rev, _ = BomRevision.objects.get_or_create(
            root=bom1,
            revision_number=1,
            defaults={"status": "ACTIVE"},
        )
        bom1_lines = [
            (1, "BOPP-20", 220, "M", "PER_1000M"),
            (2, "PET-12", 220, "M", "PER_1000M"),
            (3, "PE-FILM80", 1000, "M", "PER_1000M"),
            (4, "ADH-001", 12, "KG", "PER_1000M"),
            (5, "INK-BLK", 2.5, "KG", "PER_1000M"),
            (6, "INK-CYN", 1.8, "KG", "PER_1000M"),
            (7, "INK-MAG", 1.5, "KG", "PER_1000M"),
            (8, "INK-YEL", 1.2, "KG", "PER_1000M"),
            (9, "SOL-001", 15, "KG", "PER_1000M"),
        ]
        for seq, mat_code, qty, uom_code, basis in bom1_lines:
            BomLine.objects.get_or_create(
                revision=bom1_rev,
                sequence=seq,
                defaults={
                    "material": materials[mat_code],
                    "quantity_per_output": qty,
                    "uom": uoms[uom_code],
                    "consumption_basis": basis,
                    "scrap_pct": 2.0 if seq <= 3 else None,
                },
            )

        # BOM 2: PE bag
        bom2, _ = BillOfMaterials.objects.get_or_create(
            spec_revision=spec2,
            output_material=materials["PE-FILM80"],
        )
        bom2_rev, _ = BomRevision.objects.get_or_create(
            root=bom2,
            revision_number=1,
            defaults={"status": "ACTIVE"},
        )
        bom2_lines = [
            (1, "PE-FILM80", 0.035, "KG", "PER_BAG"),
            (2, "INK-BLK", 0.002, "KG", "PER_BAG"),
            (3, "INK-CYN", 0.0015, "KG", "PER_BAG"),
            (4, "INK-MAG", 0.0012, "KG", "PER_BAG"),
            (5, "INK-YEL", 0.001, "KG", "PER_BAG"),
            (6, "SOL-001", 0.008, "KG", "PER_BAG"),
        ]
        for seq, mat_code, qty, uom_code, basis in bom2_lines:
            BomLine.objects.get_or_create(
                revision=bom2_rev,
                sequence=seq,
                defaults={
                    "material": materials[mat_code],
                    "quantity_per_output": qty,
                    "uom": uoms[uom_code],
                    "consumption_basis": basis,
                },
            )

        # ── 14. Routings ─────────────────────────────────────────────────
        # Routing 1: multilayer film
        rout1, _ = Routing.objects.get_or_create(spec_revision=spec1)
        rout1_rev, _ = RoutingRevision.objects.get_or_create(
            root=rout1,
            revision_number=1,
            defaults={"status": "ACTIVE"},
        )
        rout1_ops = [
            (1, "EXT", "Blown film extrusion", "BACKFLUSH"),
            (2, "PRINT", "Reverse flexo printing", "EXPLICIT"),
            (3, "LAM", "Solventless lamination", "EXPLICIT"),
            (4, "SLIT", "Slitting to width", "EXPLICIT"),
        ]
        for seq, wc_code, name, issue in rout1_ops:
            RoutingOperation.objects.get_or_create(
                revision=rout1_rev,
                sequence=seq,
                defaults={
                    "work_center": work_centers[wc_code],
                    "operation_name": name,
                    "issue_method": issue,
                },
            )

        # Routing 2: PE bag
        rout2, _ = Routing.objects.get_or_create(spec_revision=spec2)
        rout2_rev, _ = RoutingRevision.objects.get_or_create(
            root=rout2,
            revision_number=1,
            defaults={"status": "ACTIVE"},
        )
        rout2_ops = [
            (1, "EXT", "Blown film extrusion", "BACKFLUSH"),
            (2, "PRINT", "Surface flexo printing", "EXPLICIT"),
            (3, "CONV", "Bag converting", "EXPLICIT"),
        ]
        for seq, wc_code, name, issue in rout2_ops:
            RoutingOperation.objects.get_or_create(
                revision=rout2_rev,
                sequence=seq,
                defaults={
                    "work_center": work_centers[wc_code],
                    "operation_name": name,
                    "issue_method": issue,
                },
            )

        # ── 15. Sales Orders ─────────────────────────────────────────────
        so, _ = SalesOrder.objects.get_or_create(
            company=company,
            number="SO-2026-001",
            defaults={
                "customer": customer,
                "status": SalesOrderStatus.CONFIRMED,
                "order_date": TODAY - timedelta(days=14),
                "requested_date": TODAY + timedelta(days=30),
            },
        )
        SalesOrderLine.objects.get_or_create(
            order=so,
            sequence=1,
            defaults={
                "customer_product": customer_products["CP-001"],
                "quantity": 10000,
                "uom": uoms["M"],
                "unit_price": 85000,
            },
        )
        SalesOrderLine.objects.get_or_create(
            order=so,
            sequence=2,
            defaults={
                "customer_product": customer_products["CP-002"],
                "quantity": 5000,
                "uom": uoms["PCS"],
                "unit_price": 12500,
            },
        )

        so2, _ = SalesOrder.objects.get_or_create(
            company=company,
            number="SO-2026-002",
            defaults={
                "customer": customer,
                "status": SalesOrderStatus.CONFIRMED,
                "order_date": TODAY - timedelta(days=7),
                "requested_date": TODAY + timedelta(days=21),
            },
        )
        SalesOrderLine.objects.get_or_create(
            order=so2,
            sequence=1,
            defaults={
                "customer_product": customer_products["CP-001"],
                "quantity": 5000,
                "uom": uoms["M"],
            },
        )

        # ── 16. Purchase Orders ──────────────────────────────────────────
        po, _ = PurchaseOrder.objects.get_or_create(
            company=company,
            number="PO-2026-001",
            defaults={
                "supplier": supplier,
                "status": PurchaseOrderStatus.SENT,
                "order_date": TODAY - timedelta(days=21),
                "expected_date": TODAY + timedelta(days=7),
            },
        )
        po_lines = [
            (1, "PE-LD", 5000, "KG", 65000),
            (2, "PE-LLD", 3000, "KG", 72000),
            (3, "BOPP-20", 200, "ROLL", 4500000),
            (4, "PET-12", 200, "ROLL", 5200000),
            (5, "INK-BLK", 200, "KG", 380000),
            (6, "INK-CYN", 150, "KG", 420000),
        ]
        for seq, mat_code, qty, uom_code, price in po_lines:
            PurchaseOrderLine.objects.get_or_create(
                order=po,
                sequence=seq,
                defaults={
                    "material": materials[mat_code],
                    "quantity": qty,
                    "uom": uoms[uom_code],
                    "unit_price": price,
                },
            )

        # ── 17. Production Orders ────────────────────────────────────────
        prod_order_config = [
            ("WO-2026-001", "CP-001", 10000, "M", "RELEASED", TODAY - timedelta(days=5)),
            ("WO-2026-002", "CP-002", 5000, "PCS", "RELEASED", TODAY - timedelta(days=3)),
            ("WO-2026-003", "CP-001", 5000, "M", "DRAFT", TODAY),
        ]
        for number, cp_code, qty, uom_code, status, start in prod_order_config:
            cp = customer_products[cp_code]
            # Find the active spec for this customer product
            spec = cp.specifications.filter(status="ACTIVE").first()
            if not spec:
                continue
            ProductionOrder.objects.get_or_create(
                company=company,
                number=number,
                defaults={
                    "customer_product": cp,
                    "spec_revision": spec,
                    "status": status,
                    "planned_quantity": qty,
                    "uom": uoms[uom_code],
                    "scheduled_start": start,
                    "scheduled_end": start + timedelta(days=10),
                },
            )

        # ── 18. Demo operator user ───────────────────────────────────────
        demo_user, user_created = User.objects.get_or_create(
            email="operator@slz.local",
            defaults={
                "full_name": "Demo Operator",
                "language": "fa",
            },
        )
        if user_created:
            demo_user.set_password("demo123")
            demo_user.save(update_fields=["password"])

        # Assign to platform_admin role
        admin_role = Role.objects.filter(code="platform_admin").first()
        if admin_role:
            UserRole.objects.get_or_create(user=demo_user, role=admin_role)

        # Add company membership
        CompanyMembership.objects.get_or_create(user=demo_user, company=company)

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data seeded.\n"
                f"  Company: {company.name_en} ({company.code})\n"
                f"  Site:    {site.name_en}\n"
                f"  Warehouses: {len(warehouses)}\n"
                f"  UoMs:    {len(uoms)}\n"
                f"  Materials: {len(materials)}\n"
                f"  Products: {len(products)}\n"
                f"  Customer products: {len(customer_products)}\n"
                f"  Work centers: {len(work_centers)}\n"
                f"  Sales orders: 2 (CONFIRMED)\n"
                f"  Purchase orders: 1 (SENT)\n"
                f"  Production orders: 3 (2 RELEASED, 1 DRAFT)\n"
                f"  Demo user: operator@slz.local / demo123"
            )
        )
