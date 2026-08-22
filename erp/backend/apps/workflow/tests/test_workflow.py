"""Approval-workflow service tests (sequential + rejection paths)."""

from __future__ import annotations

from django.test import TestCase

from apps.audit.models import AuditLog
from apps.core.tests.factories import auth_client, grant, make_user
from apps.notifications.models import Notification
from apps.workflow.models import WorkflowDefinition, WorkflowState
from apps.workflow.services import record_decision, start_workflow


class WorkflowTests(TestCase):
    def setUp(self):
        self.definition = WorkflowDefinition.objects.create(
            code="spec_approval", name_en="Spec", name_fa="مشخصات"
        )
        self.requester = make_user(email="req@slz.test")
        self.a1 = make_user(email="a1@slz.test")
        self.a2 = make_user(email="a2@slz.test")

    def _start(self):
        return start_workflow(
            definition=self.definition,
            entity_type="engineering.Spec",
            entity_id="SPEC-1",
            approvers=[self.a1, self.a2],
            actor=self.requester,
        )

    def test_sequential_approval_completes(self):
        instance = self._start()
        self.assertEqual(instance.state, WorkflowState.UNDER_REVIEW)
        record_decision(instance=instance, approver=self.a1, approve=True)
        instance.refresh_from_db()
        self.assertEqual(instance.state, WorkflowState.UNDER_REVIEW)
        record_decision(instance=instance, approver=self.a2, approve=True)
        instance.refresh_from_db()
        self.assertEqual(instance.state, WorkflowState.APPROVED)

    def test_rejection_finalizes_immediately(self):
        instance = self._start()
        record_decision(instance=instance, approver=self.a1, approve=False, comment="no")
        instance.refresh_from_db()
        self.assertEqual(instance.state, WorkflowState.REJECTED)

    def test_out_of_order_approval_blocked(self):
        from apps.core.exceptions import BusinessRuleError

        instance = self._start()
        with self.assertRaises(BusinessRuleError):
            record_decision(instance=instance, approver=self.a2, approve=True)

    def test_first_approver_notified(self):
        self._start()
        self.assertTrue(
            Notification.objects.filter(recipient=self.a1, type="APPROVAL_REQUIRED").exists()
        )


class WorkflowApiTests(TestCase):
    """API-surface authorization + the personal approvals inbox."""

    BASE = "/api/v1/workflow/instances/"

    def setUp(self):
        self.definition = WorkflowDefinition.objects.create(
            code="spec_approval", name_en="Spec", name_fa="مشخصات"
        )
        self.requester = make_user(email="req@slz.test")
        self.a1 = make_user(email="a1@slz.test")
        self.a2 = make_user(email="a2@slz.test")

    def _start(self):
        return start_workflow(
            definition=self.definition,
            entity_type="engineering.Spec",
            entity_id="SPEC-1",
            approvers=[self.a1, self.a2],
            actor=self.requester,
        )

    def test_cancel_requires_manage_permission(self):
        instance = self._start()
        # A plain authenticated user (no workflow perms) cannot cancel.
        stranger = make_user(email="stranger@slz.test")
        resp = auth_client(stranger).post(f"{self.BASE}{instance.pk}/cancel/", {})
        self.assertEqual(resp.status_code, 403)
        instance.refresh_from_db()
        self.assertEqual(instance.state, WorkflowState.UNDER_REVIEW)

        # With workflow.instance.manage the cancel succeeds.
        manager = make_user(email="mgr@slz.test")
        grant(manager, "workflow.instance.manage")
        resp = auth_client(manager).post(f"{self.BASE}{instance.pk}/cancel/", {})
        self.assertEqual(resp.status_code, 200)
        instance.refresh_from_db()
        self.assertEqual(instance.state, WorkflowState.CANCELLED)

    def test_list_requires_view_permission(self):
        self._start()
        stranger = make_user(email="stranger@slz.test")
        self.assertEqual(auth_client(stranger).get(self.BASE).status_code, 403)
        viewer = make_user(email="viewer@slz.test")
        grant(viewer, "workflow.instance.view")
        self.assertEqual(auth_client(viewer).get(self.BASE).status_code, 200)

    def test_mine_returns_only_my_pending_no_special_permission(self):
        instance = self._start()
        # Assigned approver sees the item in their inbox with no extra grant.
        resp = auth_client(self.a1).get(f"{self.BASE}mine/")
        self.assertEqual(resp.status_code, 200)
        ids = [row["id"] for row in resp.data["results"]]
        self.assertIn(str(instance.pk), ids)
        # The requester (no approval step) sees an empty inbox.
        resp = auth_client(self.requester).get(f"{self.BASE}mine/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["results"], [])

    def test_decision_via_api_by_assigned_approver(self):
        instance = self._start()
        resp = auth_client(self.a1).post(
            f"{self.BASE}{instance.pk}/decision/", {"approve": True}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        instance.refresh_from_db()
        # Second approver still pending → workflow stays under review.
        self.assertEqual(instance.state, WorkflowState.UNDER_REVIEW)
        # It now leaves a1's inbox but remains in a2's.
        self.assertEqual(auth_client(self.a1).get(f"{self.BASE}mine/").data["results"], [])
        self.assertEqual(len(auth_client(self.a2).get(f"{self.BASE}mine/").data["results"]), 1)

    def test_decision_by_unassigned_user_is_rejected(self):
        """Object-level guard: only an assigned, still-pending approver may act.

        The endpoint deliberately allows any authenticated user through the
        permission layer (approvers must not need ``workflow.instance.manage``);
        the service must therefore reject decisions from users without a
        pending step on THIS instance — otherwise anyone could approve.
        """
        instance = self._start()
        outsider = make_user(email="outsider@slz.test")
        resp = auth_client(outsider).post(
            f"{self.BASE}{instance.pk}/decision/", {"approve": True}, format="json"
        )
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"]["type"], "BusinessRuleError")
        instance.refresh_from_db()
        self.assertEqual(instance.state, WorkflowState.UNDER_REVIEW)


class WorkflowDefinitionApiTests(TestCase):
    """The definitions admin surface: RBAC + audited writes."""

    BASE = "/api/v1/workflow/definitions/"

    def test_create_is_audited_and_stamps_actor(self):
        manager = make_user(email="wf-mgr@slz.test")
        grant(manager, "workflow.definition.view")
        grant(manager, "workflow.definition.manage")
        payload = {
            "code": "po_approval",
            "name_en": "PO approval",
            "name_fa": "تأیید سفارش خرید",
            "approval_mode": "SEQUENTIAL",
            "is_active": True,
        }
        resp = auth_client(manager).post(self.BASE, payload, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        definition = WorkflowDefinition.objects.get(code="po_approval")
        self.assertEqual(definition.created_by_id, manager.id)
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE",
                entity_type="workflow.WorkflowDefinition",
                entity_id=str(definition.pk),
            ).exists()
        )

    def test_duplicate_code_rejected(self):
        WorkflowDefinition.objects.create(code="dup", name_en="Dup", name_fa="تکراری")
        manager = make_user(email="wf-mgr2@slz.test")
        grant(manager, "workflow.definition.view")
        grant(manager, "workflow.definition.manage")
        resp = auth_client(manager).post(
            self.BASE,
            {"code": "dup", "name_en": "Dup2", "name_fa": "دو"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_view_only_user_cannot_create(self):
        viewer = make_user(email="wf-viewer@slz.test")
        grant(viewer, "workflow.definition.view")
        resp = auth_client(viewer).post(
            self.BASE,
            {"code": "nope", "name_en": "No", "name_fa": "نه"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_unpermitted_user_cannot_list(self):
        stranger = make_user(email="wf-stranger@slz.test")
        self.assertEqual(auth_client(stranger).get(self.BASE).status_code, 403)
