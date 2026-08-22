"""Transition-safety tests for the procurement document state machine.

These cover the defensive guarantees of ``apps.procurement.services.transition``
that the API-level lifecycle tests do not exercise:

* a target status the model does not declare is rejected (409) and nothing is
  persisted or audited;
* the source-status check reads a freshly locked row inside the transaction, so
  a stale in-memory instance whose ``status`` attribute claims an allowed value
  cannot drive a transition the database row does not permit;
* the happy path still persists, returns the caller's instance consistent with
  the committed row, and emits the audited ``EntityUpdated`` on commit.
"""

from __future__ import annotations

from contextlib import contextmanager

from django.db import DEFAULT_DB_ALIAS, connections
from django.test import TestCase

from apps.audit.models import AuditLog
from apps.core.exceptions import ConflictError
from apps.core.tests.factories import make_company, make_user
from apps.procurement import services
from apps.procurement.models import PurchaseRequisition, PurchaseRequisitionStatus

PR = PurchaseRequisitionStatus


@contextmanager
def _executing_on_commit_callbacks():
    """Drain ``transaction.on_commit`` callbacks as a real COMMIT would.

    Same mechanism as ``OnCommitExecutingClient`` in core test helpers, for
    assertions around *direct* service calls (no HTTP request involved).
    """
    conn = connections[DEFAULT_DB_ALIAS]
    captured: list = []
    old = conn.run_on_commit
    conn.run_on_commit = captured
    try:
        yield
        while captured:
            batch_count = len(captured)
            for _sids, func, robust in captured:
                if robust:
                    try:
                        func()
                    except Exception:
                        pass
                else:
                    func()
            del captured[:batch_count]
    finally:
        conn.run_on_commit = old


class TransitionSafetyTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.user = make_user()
        self.pr = PurchaseRequisition.objects.create(company=self.company, number="PR-T1")

    def _transition(self, document=None, to_status=PR.SUBMITTED, allowed_from=(PR.DRAFT,)):
        return services.transition(
            document=document or self.pr,
            entity_type="procurement.PurchaseRequisition",
            to_status=to_status,
            allowed_from=allowed_from,
            actor=self.user,
        )

    def test_undeclared_target_status_rejected_and_nothing_persisted(self):
        with self.assertRaises(ConflictError) as ctx:
            self._transition(to_status="NOT_A_STATUS")
        self.assertEqual(ctx.exception.code, "invalid_status_transition")
        self.pr.refresh_from_db()
        self.assertEqual(self.pr.status, PR.DRAFT)
        self.assertFalse(AuditLog.objects.filter(entity_id=str(self.pr.id)).exists())

    def test_stale_instance_cannot_transition_a_row_in_a_disallowed_state(self):
        # The database row stays DRAFT; the caller's stale copy claims SUBMITTED.
        # approve() allows only from SUBMITTED — the guard must consult the row.
        stale = PurchaseRequisition.objects.get(pk=self.pr.pk)
        stale.status = PR.SUBMITTED
        with self.assertRaises(ConflictError) as ctx:
            services.transition(
                document=stale,
                entity_type="procurement.PurchaseRequisition",
                to_status=PR.APPROVED,
                allowed_from=[PR.SUBMITTED],
                actor=self.user,
            )
        self.assertEqual(ctx.exception.code, "invalid_status_transition")
        self.pr.refresh_from_db()
        self.assertEqual(self.pr.status, PR.DRAFT)
        self.assertFalse(AuditLog.objects.filter(entity_id=str(self.pr.id)).exists())

    def test_valid_transition_persists_returns_consistent_instance_and_audits(self):
        with _executing_on_commit_callbacks():
            result = self._transition()
        self.assertEqual(result.status, PR.SUBMITTED)
        self.pr.refresh_from_db()
        self.assertEqual(self.pr.status, PR.SUBMITTED)
        self.assertTrue(
            AuditLog.objects.filter(
                action="UPDATE",
                entity_type="procurement.PurchaseRequisition",
                entity_id=str(self.pr.id),
                after_state__status=PR.SUBMITTED,
            ).exists()
        )
