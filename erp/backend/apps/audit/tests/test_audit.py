"""Audit-trail tests: direct recording, event-bus bridging, state snapshots."""

from __future__ import annotations

from django.test import TestCase
from rest_framework import serializers as drf

from apps.audit.models import AuditLog
from apps.audit.services import record_audit
from apps.core.events import EntityCreated, bus
from apps.core.service import create_from_serializer, delete_instance, update_from_serializer
from apps.core.tests.factories import make_company, make_user
from apps.organization.models import Company


class AuditTests(TestCase):
    def test_record_audit_persists_entry(self):
        user = make_user()
        entry = record_audit(
            action="CREATE",
            entity_type="organization.Company",
            entity_id="123",
            actor=user,
        )
        self.assertEqual(entry.action, "CREATE")
        self.assertEqual(entry.actor_label, user.email)

    def test_domain_event_creates_audit_entry(self):
        # apps.audit.subscribers registers handlers at app-ready time.
        bus.publish(EntityCreated(entity_type="test.Thing", entity_id="42"))
        self.assertTrue(
            AuditLog.objects.filter(
                action="CREATE", entity_type="test.Thing", entity_id="42"
            ).exists()
        )

    def test_event_actor_id_is_resolved_onto_audit_row(self):
        # The event path carries only actor_id (decoupled from the user model);
        # the subscriber must resolve it so actor/actor_label are populated.
        user = make_user(email="actor@slz.test")
        bus.publish(EntityCreated(entity_type="test.Thing", entity_id="99", actor_id=str(user.pk)))
        entry = AuditLog.objects.get(entity_type="test.Thing", entity_id="99")
        self.assertEqual(entry.actor_id, user.pk)
        self.assertEqual(entry.actor_label, user.email)

    def test_unknown_actor_id_degrades_to_anonymous_row(self):
        import uuid

        bus.publish(
            EntityCreated(
                entity_type="test.Thing",
                entity_id="100",
                actor_id=str(uuid.uuid4()),
            )
        )
        entry = AuditLog.objects.get(entity_type="test.Thing", entity_id="100")
        self.assertIsNone(entry.actor_id)
        self.assertEqual(entry.actor_label, "")


class CompanySerializer(drf.ModelSerializer):
    class Meta:
        model = Company
        fields = ["code", "name_en", "name_fa"]


class AuditStateSnapshotTests(TestCase):
    """The generic write service must snapshot record state onto the trail."""

    def setUp(self):
        self.user = make_user()

    def test_create_captures_after_state(self):
        ser = CompanySerializer(data={"code": "ACME", "name_en": "Acme", "name_fa": "اک"})
        self.assertTrue(ser.is_valid(), ser.errors)
        with self.captureOnCommitCallbacks(execute=True):
            company = create_from_serializer(ser, actor=self.user)
        entry = AuditLog.objects.get(action="CREATE", entity_id=str(company.id))
        self.assertEqual(entry.after_state["code"], "ACME")
        self.assertEqual(entry.after_state["name_en"], "Acme")
        self.assertIsNone(entry.before_state)

    def test_update_captures_before_and_after(self):
        company = make_company(code="ACME")
        ser = CompanySerializer(company, data={"name_en": "Renamed"}, partial=True)
        self.assertTrue(ser.is_valid(), ser.errors)
        with self.captureOnCommitCallbacks(execute=True):
            update_from_serializer(ser, actor=self.user)
        entry = AuditLog.objects.get(action="UPDATE", entity_id=str(company.id))
        self.assertEqual(entry.before_state["name_en"], "Lafaf Zarrin")
        self.assertEqual(entry.after_state["name_en"], "Renamed")

    def test_soft_delete_captures_before_state(self):
        company = make_company(code="GONE")
        with self.captureOnCommitCallbacks(execute=True):
            delete_instance(company)
        entry = AuditLog.objects.get(action="DELETE", entity_id=str(company.id))
        self.assertEqual(entry.before_state["code"], "GONE")
        self.assertIsNone(entry.after_state)
