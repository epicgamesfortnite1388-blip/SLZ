"""True two-thread PostgreSQL concurrency tests for the workflow engine.

SQLite cannot exercise ``select_for_update`` blocking, so these skip unless the
connection is PostgreSQL. Run against the compose Postgres instance::

    docker compose exec -T backend python manage.py test \\\\
        apps.workflow.tests.test_concurrency_postgres \\\\
        --settings=config.settings.test_pg --noinput

The workflow services now re-read the instance under ``select_for_update``
before deciding/cancelling (mirroring the sales status-transition guard). These
tests race a final approval against a cancel (and a duplicate decision of the
same step) and assert that EXACTLY ONE terminal transition is persisted — one
audit row, one final state — while the losing caller gets a clean domain error.
"""

from __future__ import annotations

import threading

from django.db import connection
from django.test import TransactionTestCase
from django.test.utils import skipUnless

from apps.audit.models import AuditLog
from apps.core.exceptions import BusinessRuleError
from apps.core.tests.factories import make_user
from apps.workflow.models import ApprovalMode, WorkflowDefinition, WorkflowState
from apps.workflow.services import cancel_workflow, record_decision, start_workflow


@skipUnless(connection.vendor == "postgresql", "requires PostgreSQL")
class WorkflowFinalizationRaceTests(TransactionTestCase):
    """Two threads race the terminal transition of one workflow instance.

    ``record_decision`` (final approval) and ``cancel_workflow`` both lock the
    instance row and re-check its state inside the transaction, so only one may
    finalize it. Before the lock was added, both could pass the pre-check and
    double-finalize (two audit rows, two terminal-state writes).
    """

    ROUNDS = 5

    def _make_instance(self, round_no, single=True):
        definition = WorkflowDefinition.objects.create(
            code=f"wf_{round_no}",
            name_en=f"WF {round_no}",
            name_fa=f"گردش {round_no}",
            approval_mode=ApprovalMode.SEQUENTIAL,
        )
        requester = make_user(email=f"req{round_no}@slz.test")
        approver = make_user(email=f"appr{round_no}@slz.test")
        instance = start_workflow(
            definition=definition,
            entity_type="engineering.Spec",
            entity_id=f"SPEC-{round_no}",
            approvers=[approver],
            actor=requester,
        )
        return {"instance": instance, "approver": approver, "requester": requester}

    def test_approve_racing_cancel_finalizes_exactly_once(self):
        for round_no in range(self.ROUNDS):
            ctx = self._make_instance(round_no)
            instance = ctx["instance"]
            results: dict = {}
            barrier = threading.Barrier(2)

            def _approve():
                try:
                    barrier.wait(timeout=20)
                    record_decision(
                        instance=instance, approver=ctx["approver"], approve=True, comment="ok"
                    )
                    results["approve"] = "ok"
                except BusinessRuleError as exc:
                    results["approve"] = exc.code or exc.message
                except Exception as exc:  # noqa: BLE001 - surface any failure
                    results["approve"] = f"unexpected:{type(exc).__name__}:{exc}"
                finally:
                    connection.close()

            def _cancel():
                try:
                    barrier.wait(timeout=20)
                    cancel_workflow(instance=instance, actor=ctx["requester"], reason="race")
                    results["cancel"] = "ok"
                except BusinessRuleError as exc:
                    results["cancel"] = exc.code or exc.message
                except Exception as exc:  # noqa: BLE001 - surface any failure
                    results["cancel"] = f"unexpected:{type(exc).__name__}:{exc}"
                finally:
                    connection.close()

            threads = [
                threading.Thread(target=_approve),
                threading.Thread(target=_cancel),
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)

            instance.refresh_from_db()
            terminal = instance.state in (WorkflowState.APPROVED, WorkflowState.CANCELLED)
            self.assertTrue(terminal, f"round {round_no}: state={instance.state} must be terminal")
            values = list(results.values())
            self.assertEqual(
                values.count("ok"),
                1,
                f"round {round_no}: exactly one caller may finalize, got {values}",
            )
            loser = next(v for v in values if v != "ok")
            self.assertFalse(
                loser.startswith("unexpected"), f"round {round_no}: loser error: {loser}"
            )
            terminal_audits = AuditLog.objects.filter(
                entity_type="workflow.WorkflowInstance",
                entity_id=str(instance.pk),
                action__in=["APPROVE", "CANCEL"],
            ).count()
            self.assertEqual(
                terminal_audits, 1, f"round {round_no}: exactly one terminal audit row"
            )

    def test_duplicate_decision_of_final_step_finalizes_once(self):
        for round_no in range(self.ROUNDS):
            ctx = self._make_instance(round_no)
            instance = ctx["instance"]
            results: dict = {}
            barrier = threading.Barrier(2)

            def _decide(idx):
                try:
                    barrier.wait(timeout=20)
                    record_decision(
                        instance=instance, approver=ctx["approver"], approve=True, comment=f"d{idx}"
                    )
                    results[idx] = "ok"
                except BusinessRuleError as exc:
                    results[idx] = exc.code or exc.message
                except Exception as exc:  # noqa: BLE001 - surface any failure
                    results[idx] = f"unexpected:{type(exc).__name__}:{exc}"
                finally:
                    connection.close()

            threads = [
                threading.Thread(target=_decide, args=(0,)),
                threading.Thread(target=_decide, args=(1,)),
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)

            instance.refresh_from_db()
            self.assertEqual(instance.state, WorkflowState.APPROVED, f"round {round_no}")
            values = list(results.values())
            self.assertEqual(
                values.count("ok"),
                1,
                f"round {round_no}: one decision wins, the duplicate is rejected, got {values}",
            )
            loser = next(v for v in values if v != "ok")
            self.assertFalse(
                loser.startswith("unexpected"), f"round {round_no}: loser error: {loser}"
            )
            approve_audits = AuditLog.objects.filter(
                entity_type="workflow.WorkflowInstance",
                entity_id=str(instance.pk),
                action="APPROVE",
            ).count()
            self.assertEqual(approve_audits, 1, f"round {round_no}: one APPROVE audit row")
