"""True two-thread PostgreSQL concurrency regression tests.

The default SQLite suite cannot exercise ``pg_advisory_xact_lock`` semantics,
so these tests skip unless the connection is PostgreSQL. Run them against the
compose Postgres instance::

    docker compose exec -T backend python manage.py test \\
        apps.inventory.tests.test_concurrency_postgres \\
        --settings=config.settings.test_pg --noinput

Each round runs TWO real threads against two separate DB connections, released
together by a barrier. The invariant asserted is the one the advisory lock
guarantees: when two OUT postings race for the same stock dimension, exactly
one wins, the loser raises ``inventory.insufficient_stock``, the ledger never
goes negative, and exactly one OUT row is appended. (Without the lock both
threads can pass the derived on-hand check and drive stock below zero.)
"""

from __future__ import annotations

import threading
from decimal import Decimal

from django.db import connection
from django.test import TransactionTestCase
from django.test.utils import skipUnless

from apps.catalog.models import Material, UnitOfMeasure, UomDimension
from apps.core.exceptions import BusinessRuleError
from apps.core.tests.factories import make_company, make_site, make_user
from apps.inventory import services as inventory_services
from apps.inventory.models import (
    StockMovement,
    StockMovementDirection,
    Warehouse,
    WarehouseStoreType,
)


@skipUnless(connection.vendor == "postgresql", "requires PostgreSQL")
class OutPostingAdvisoryLockTests(TransactionTestCase):
    """Two threads race two OUT postings on the same stock dimension.

    ``post_movement`` takes a transaction-scoped advisory lock keyed on
    (company, warehouse, material) before the read-then-write on-hand check,
    so the two transactions cannot both pass the check. The loser blocks on
    the lock until the winner commits, then observes zero on-hand and raises.
    """

    ROUNDS = 5

    def _dimension(self, round_no):
        company = make_company(code=f"CONC{round_no}")
        site = make_site(company=company, code=f"S{round_no}")
        uom = UnitOfMeasure.objects.create(
            code=f"KG{round_no}", name_fa="کیلوگرم", dimension=UomDimension.MASS
        )
        material = Material.objects.create(
            company=company, code=f"RM-{round_no}", name_fa="ماده", base_uom=uom
        )
        warehouse = Warehouse.objects.create(
            company=company,
            site=site,
            code=f"WH-{round_no}",
            name_fa="انبار",
            store_type=WarehouseStoreType.RAW_MATERIAL,
        )
        user = make_user(email=f"race{round_no}@slz.test")
        return company, site, uom, material, warehouse, user

    def _post_out(self, company, warehouse, material, uom, qty, user):
        return inventory_services.post_movement(
            company=company,
            warehouse=warehouse,
            direction=StockMovementDirection.OUT,
            quantity=qty,
            uom=uom,
            material=material,
            reference_type="test.race",
            actor=user,
        )

    def test_two_concurrent_outs_are_serialized(self):
        for round_no in range(self.ROUNDS):
            company, _site, uom, material, warehouse, user = self._dimension(round_no)
            # Seed exactly enough for ONE posting; both threads want it all.
            inventory_services.post_movement(
                company=company,
                warehouse=warehouse,
                direction=StockMovementDirection.IN,
                quantity=Decimal("100"),
                uom=uom,
                material=material,
                reference_type="test.seed",
                actor=user,
            )
            results: dict = {}
            barrier = threading.Barrier(2)

            def _worker(idx):
                try:
                    barrier.wait(timeout=20)
                    self._post_out(company, warehouse, material, uom, Decimal("100"), user)
                    results[idx] = "ok"
                except BusinessRuleError as exc:
                    results[idx] = exc.code
                except Exception as exc:  # noqa: BLE001 - surface any failure
                    results[idx] = f"unexpected:{type(exc).__name__}"
                finally:
                    connection.close()

            threads = [threading.Thread(target=_worker, args=(i,)) for i in (0, 1)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)

            self.assertEqual(
                sorted(results.values()),
                ["inventory.insufficient_stock", "ok"],
                f"round {round_no}: one posting must win, the other must be rejected",
            )
            on_hand = inventory_services.on_hand_quantity(
                company=company,
                warehouse=warehouse,
                material=material,
            )
            self.assertEqual(
                on_hand, Decimal("0"), "stock must never go negative under racing OUTs"
            )
            out_rows = StockMovement.objects.filter(
                company=company,
                direction=StockMovementDirection.OUT,
                reference_type="test.race",
            ).count()
            self.assertEqual(out_rows, 1, "exactly one OUT row may be appended")
