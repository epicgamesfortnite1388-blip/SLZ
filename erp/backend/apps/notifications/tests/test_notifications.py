"""Notification API tests — per-user isolation + read-state actions.

The viewset is self-authorizing (``get_queryset`` filters to the requesting
user), so these confirm a user only ever sees and mutates their own
notifications and that the read-state helpers behave.
"""

from __future__ import annotations

from django.test import TestCase

from apps.core.tests.factories import auth_client, make_user
from apps.notifications.models import Notification, NotificationType


class NotificationApiTests(TestCase):
    BASE = "/api/v1/notifications/"

    def setUp(self):
        self.alice = make_user(email="alice@slz.test")
        self.bob = make_user(email="bob@slz.test")
        # Two unread for Alice, one for Bob.
        self.n1 = Notification.objects.create(
            recipient=self.alice,
            type=NotificationType.APPROVAL_REQUIRED,
            title="Approve spec",
        )
        self.n2 = Notification.objects.create(
            recipient=self.alice,
            type=NotificationType.SYSTEM_ALERT,
            title="Heads up",
        )
        Notification.objects.create(
            recipient=self.bob,
            type=NotificationType.SYSTEM_ALERT,
            title="Bob only",
        )

    def test_list_returns_only_own_notifications(self):
        resp = auth_client(self.alice).get(self.BASE)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 2)
        titles = {row["title"] for row in resp.data["results"]}
        self.assertEqual(titles, {"Approve spec", "Heads up"})

    def test_unread_count_is_per_user(self):
        self.assertEqual(auth_client(self.alice).get(f"{self.BASE}unread-count/").data["unread"], 2)
        self.assertEqual(auth_client(self.bob).get(f"{self.BASE}unread-count/").data["unread"], 1)

    def test_mark_read_flips_a_single_notification(self):
        resp = auth_client(self.alice).post(f"{self.BASE}{self.n1.pk}/read/", {})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["is_read"])
        self.assertIsNotNone(resp.data["read_at"])
        self.assertEqual(auth_client(self.alice).get(f"{self.BASE}unread-count/").data["unread"], 1)

    def test_cannot_read_another_users_notification(self):
        other = Notification.objects.create(
            recipient=self.bob,
            type=NotificationType.SYSTEM_ALERT,
            title="secret",
        )
        resp = auth_client(self.alice).post(f"{self.BASE}{other.pk}/read/", {})
        self.assertEqual(resp.status_code, 404)

    def test_mark_all_read_clears_only_own_unread(self):
        resp = auth_client(self.alice).post(f"{self.BASE}read-all/", {})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["updated"], 2)
        self.assertEqual(auth_client(self.alice).get(f"{self.BASE}unread-count/").data["unread"], 0)
        # Bob's unread is untouched.
        self.assertEqual(auth_client(self.bob).get(f"{self.BASE}unread-count/").data["unread"], 1)
