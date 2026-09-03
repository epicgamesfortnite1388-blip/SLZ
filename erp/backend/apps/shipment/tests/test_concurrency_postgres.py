"""True two-thread PostgreSQL concurrency regression tests.

The default SQLite suite cannot exercise ``select_for_update`` blocking, so
these tests skip unless the connection is PostgreSQL. Run them against the
compose Postgres instance::

    docker compose exec -T backend python manage.py test \\
        apps.shipment.tests.test_concurrency_postgres \\
        --settings=config.settings.test_pg --noinput

Each round runs TWO real threads against two separate DB connections, released
together by a barrier. Both threads attempt to deliver the SAME RESERVED
allocation. The row lock (``Allocation.objects.select_for_update``) taken by
``create_shipment`` serializes them: the first marks the allocation SHIPPED and
posts one OUT movement; the second blocks until the first commits, then sees a
non-RESERVED allocation and raises ``shipment.allocation_not_reserved``. Only
one shipment may be created and the unit's stock may never go negative.
"""

from __future__ import annotations

import threading
from datetime import date
from decimal import Decimal

from django.db import connection
from django.test import TransactionTestCase
from django.test.utils import skipUnless

from apps.catalog.models import (
    Material,
    ProductClass,
    ProductFamily,
    ProductGroup,
    ProductType,
    UnitOfMeasure,
    UomDimension,
)
from apps.core.exceptions import ConflictError
from apps.core.tests.factories import make_company, make_site, make_user
from apps.engineering.models import CustomerProduct, SpecificationRevision
from apps.inventory import services as inventory_services
from apps.inventory.models import (
    StockMovement,
    StockMovementDirection,
    TraceabilityUnit,
    TraceabilityUnitType,
    Warehouse,
)
from apps.partners.models import Customer, Partner
from apps.sales.models import SalesOrder, SalesOrderLine
from apps.shipment.models import AllocationStatus, Shipment


@skipUnless(connection.vendor == "postgresql", "requires PostgreSQL")
class DoubleDeliveryAllocationLockTests(TransactionTestCase):
    """Two threads race two deliveries consuming the same RESERVED allocation.

    ``create_shipment`` locks the allocation row (``select_for_update``) before
    checking its status, so two concurrent deliveries cannot both consume it.
    """

    ROUNDS = 5

    def _round_prereqs(self, round_no):
        company = make_company(code=f"SHIP{round_no}")
        site = make_site(company=company, code=f"SH{round_no}")
        uom = UnitOfMeasure.objects.create(
            code=f"KG{round_no}", name_fa="کیلوگرم", dimension=UomDimension.MASS
        )
        group = ProductGroup.objects.create(code=f"G{round_no}", name_fa="گروه")
        ptype = ProductType.objects.create(code=f"T{round_no}", name_fa="نوع")
        pclass = ProductClass.objects.create(
            product_type=ptype, code=f"C{round_no}", name_fa="کلاس"
        )
        family = ProductFamily.objects.create(
            product_class=pclass, code=f"F{round_no}", name_fa="خانواده"
        )
        partner = Partner.objects.create(
            company=company, code=f"P{round_no}", name_fa="مشتری", is_customer=True
        )
        customer = Customer.objects.create(partner=partner)
        product = CustomerProduct.objects.create(
            company=company,
            customer=partner,
            code=f"CP{round_no}",
            name_fa="محصول",
            product_group=group,
            family=family,
            base_uom=uom,
        )
        SpecificationRevision.objects.create(root=product, revision_number=1)
        material = Material.objects.create(
            company=company, code=f"MAT{round_no}", name_fa="ماده", base_uom=uom
        )
        warehouse = Warehouse.objects.create(
            company=company,
            site=site,
            code=f"FG{round_no}",
            name_fa="انبار",
            store_type="FINISHED_GOODS",
        )
        unit = TraceabilityUnit.objects.create(
            company=company,
            material=material,
            unit_type=TraceabilityUnitType.ROLL,
            identifier=f"ROLL-{round_no}",
            quantity=Decimal("100"),
            uom=uom,
        )
        so = SalesOrder.objects.create(
            company=company, number=f"SO-{round_no}", customer=customer, status="CONFIRMED"
        )
        sol = SalesOrderLine.objects.create(
            order=so, sequence=1, customer_product=product, quantity=100, uom=uom
        )
        user = make_user(email=f"ship{round_no}@slz.test")
        # Stock + a RESERVED allocation for the full 100.
        inventory_services.post_movement(
            company=company,
            warehouse=warehouse,
            direction=StockMovementDirection.IN,
            quantity=Decimal("100"),
            uom=uom,
            material=material,
            traceability_unit=unit,
            reference_type="test.seed",
            actor=user,
        )
        from apps.shipment import services as shipment_services

        alloc = shipment_services.reserve(
            company=company,
            sales_order_line=sol,
            traceability_unit=unit,
            quantity=Decimal("100"),
            uom=uom,
            actor=user,
        )
        return {
            "company": company,
            "uom": uom,
            "customer": customer,
            "sol": sol,
            "warehouse": warehouse,
            "unit": unit,
            "alloc": alloc,
            "user": user,
        }

    @staticmethod
    def _stub_serializer(validated_data):
        """Minimal serializer stand-in exposing validated_data (create_shipment
        only reads that attribute)."""
        stub = type("StubSerializer", (), {})()
        stub.validated_data = validated_data
        return stub

    def _delivery_payload(self, p, number):
        return {
            "company": p["company"],
            "warehouse": p["warehouse"],
            "customer": p["customer"],
            "sales_order": p["sol"].order,
            "number": number,
            "status": "SHIPPED",
            "shipped_at": date(2026, 8, 22),
            "notes": "",
            "nonce": None,
            "lines": [
                {
                    "traceability_unit": p["unit"],
                    "sales_order_line": p["sol"],
                    "allocation": p["alloc"],
                    "quantity": Decimal("100"),
                    "uom": p["uom"],
                    "notes": "",
                }
            ],
        }

    def test_two_concurrent_deliveries_of_same_allocation_serialized(self):
        for round_no in range(self.ROUNDS):
            p = self._round_prereqs(round_no)
            from apps.shipment import services as shipment_services

            results: dict = {}
            barrier = threading.Barrier(2)

            def _worker(idx, number):
                try:
                    barrier.wait(timeout=20)
                    payload = self._delivery_payload(p, number)
                    serializer = self._stub_serializer(payload)
                    shipment_services.create_shipment(serializer, actor=p["user"])
                    results[idx] = "ok"
                except ConflictError as exc:
                    results[idx] = exc.code
                except Exception as exc:  # noqa: BLE001 - surface any failure
                    results[idx] = f"unexpected:{type(exc).__name__}:{exc}"
                finally:
                    connection.close()

            threads = [
                threading.Thread(target=_worker, args=(0, f"D-{round_no}A")),
                threading.Thread(target=_worker, args=(1, f"D-{round_no}B")),
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)

            self.assertEqual(
                sorted(results.values()),
                ["ok", "shipment.allocation_not_reserved"],
                f"round {round_no}: one delivery must win, the second must be rejected",
            )
            p["alloc"].refresh_from_db()
            self.assertEqual(p["alloc"].status, AllocationStatus.SHIPPED)
            self.assertEqual(Shipment.objects.filter(company=p["company"]).count(), 1)
            outs = StockMovement.objects.filter(
                company=p["company"],
                direction=StockMovementDirection.OUT,
                reference_type="shipment.ShipmentLine",
            ).count()
            self.assertEqual(outs, 1, "exactly one OUT movement may be posted")
            on_hand = inventory_services.on_hand_quantity(
                company=p["company"],
                warehouse=p["warehouse"],
                traceability_unit=p["unit"],
            )
            self.assertEqual(on_hand, Decimal("0"), "stock must never go negative")
