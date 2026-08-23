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
        self.company = make_company(code="ALPHA")

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

    def test_create_captures_company_id_on_company_owned_entity(self):
        """When an entity with a company FK is created, the audit row must
        capture that company_id for row-level isolation."""
        from apps.core.tests.factories import member_of
        from apps.partners.models import Partner

        member_of(self.user, self.company)

        # Create a Partner (has company FK) — then emit the event with company_id.
        partner = Partner.objects.create(
            company=self.company,
            code="P-TEST",
            name_fa="شریک",
            is_customer=True,
            created_by=self.user,
            updated_by=self.user,
        )
        from apps.core.events import EntityCreated, bus

        bus.publish(
            EntityCreated(
                entity_type="partners.Partner",
                entity_id=str(partner.pk),
                actor_id=str(self.user.pk),
                company_id=str(partner.company_id),
                state={"code": "P-TEST"},
            )
        )
        entry = AuditLog.objects.get(
            action="CREATE", entity_type="partners.Partner", entity_id=str(partner.pk)
        )
        self.assertEqual(entry.company_id, self.company.pk)

    def test_record_audit_stores_company_id_directly(self):
        """The record_audit service must accept and persist company_id."""
        entry = record_audit(
            action="CREATE",
            entity_type="test.Thing",
            entity_id="42",
            company_id=str(self.company.pk),
            actor=self.user,
        )
        self.assertEqual(str(entry.company_id), str(self.company.pk))


class AuditCompanyIsolationTests(TestCase):
    """Audit entries must be scoped per company (Q-055)."""

    def setUp(self):
        from apps.core.tests.factories import auth_client, grant, member_of

        self.co_a = make_company(code="CO-A")
        self.co_b = make_company(code="CO-B")

        self.user_a = make_user(email="a@slz.test")
        # Remove auto-memberships so only explicit ones apply.
        self.user_a.company_memberships.all().delete()
        member_of(self.user_a, self.co_a)
        grant(self.user_a, "audit.log.view")
        self.client_a = auth_client(self.user_a)

        self.user_b = make_user(email="b@slz.test")
        self.user_b.company_memberships.all().delete()
        member_of(self.user_b, self.co_b)
        grant(self.user_b, "audit.log.view")
        self.client_b = auth_client(self.user_b)

        # Seed: company-A audit entry
        record_audit(
            action="CREATE",
            entity_type="test.Thing",
            entity_id="a-1",
            company_id=str(self.co_a.pk),
        )
        # Seed: company-B audit entry
        record_audit(
            action="CREATE",
            entity_type="test.Thing",
            entity_id="b-1",
            company_id=str(self.co_b.pk),
        )
        # Seed: platform event (no company)
        record_audit(
            action="LOGIN",
            entity_type="identity.User",
            entity_id=str(self.user_a.pk),
        )

    def test_user_a_sees_only_own_company_entries(self):
        resp = self.client_a.get("/api/v1/audit/logs/")
        self.assertEqual(resp.status_code, 200)
        ids = {r["entity_id"] for r in resp.data["results"]}
        # Should include company-A entry + platform entry
        self.assertIn("a-1", ids)
        # Should NOT include company-B entry
        self.assertNotIn("b-1", ids)
        # Should include the platform (company-NULL) entry
        self.assertIn(str(self.user_a.pk), ids)

    def test_user_b_sees_only_own_company_entries(self):
        resp = self.client_b.get("/api/v1/audit/logs/")
        self.assertEqual(resp.status_code, 200)
        ids = {r["entity_id"] for r in resp.data["results"]}
        self.assertIn("b-1", ids)
        self.assertNotIn("a-1", ids)
        # Platform entry visible
        self.assertIn(str(self.user_a.pk), ids)

    def test_user_with_no_membership_sees_only_platform(self):
        from apps.core.tests.factories import auth_client, grant

        outsider = make_user(email="outsider@slz.test")
        outsider.company_memberships.all().delete()
        grant(outsider, "audit.log.view")
        client = auth_client(outsider)

        resp = client.get("/api/v1/audit/logs/")
        self.assertEqual(resp.status_code, 200)
        ids = {r["entity_id"] for r in resp.data["results"]}
        self.assertNotIn("a-1", ids)
        self.assertNotIn("b-1", ids)
        # Platform entry still visible
        self.assertIn(str(self.user_a.pk), ids)

    def test_superuser_sees_all_entries(self):
        from apps.core.tests.factories import auth_client, make_superuser

        su = make_superuser(email="su@slz.test")
        client = auth_client(su)
        resp = client.get("/api/v1/audit/logs/")
        self.assertEqual(resp.status_code, 200)
        ids = {r["entity_id"] for r in resp.data["results"]}
        self.assertIn("a-1", ids)
        self.assertIn("b-1", ids)
        self.assertIn(str(self.user_a.pk), ids)
