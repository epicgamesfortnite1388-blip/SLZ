"""Cross-company isolation tests for the attachment register (Q-055).

Attachments are generic (entity_type, entity_id) references, so company
isolation cannot be a plain FK filter — the target's company is resolved at
upload through ``ENTITY_COMPANY_PATHS`` and stamped on the row; listing,
retrieval, download and delete are scoped to the caller's memberships
(fail closed: rows without a resolvable company are superuser-only).

These tests pin the attacks that motivated the fix:

* uploading against another company's record was possible with only
  ``documents.attachment.view``;
* listing returned every company's file metadata;
* any attachment UUID could be downloaded once known.
"""

from __future__ import annotations

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.core.tests.factories import auth_client, grant, make_company, make_user
from apps.documents.models import Attachment
from apps.identity.models import CompanyMembership
from apps.partners.models import Partner


def _only_member_of(user, company) -> None:
    CompanyMembership.objects.filter(user=user).exclude(company=company).delete()


@override_settings(DOCUMENTS_ALLOWED_EXTENSIONS=["txt"])
class AttachmentCompanyIsolationTests(TestCase):
    def setUp(self):
        # Company B first so the Company-A insider does not auto-join it.
        self.company_b = make_company(code="BBBB")
        self.company_a = make_company(code="AAAA")

        self.partner_a = Partner.objects.create(
            company=self.company_a, code="P-A", name_fa="شریک الف", is_customer=True
        )
        self.partner_b = Partner.objects.create(
            company=self.company_b, code="P-B", name_fa="شریک ب", is_customer=True
        )

        self.insider = make_user(email="a@slz.test")
        _only_member_of(self.insider, self.company_a)
        grant(self.insider, "documents.attachment.view", "documents.attachment.delete")
        self.client = auth_client(self.insider)

    def _upload(self, partner_id, name="spec.txt"):
        return self.client.post(
            "/api/v1/documents/attachments/upload/",
            {
                "entity_type": "partners.Partner",
                "entity_id": str(partner_id),
                "file": SimpleUploadedFile(name, b"payload", content_type="text/plain"),
            },
            format="multipart",
        )

    def test_upload_to_own_entity_stamps_the_company(self):
        resp = self._upload(self.partner_a.id)
        self.assertEqual(resp.status_code, 201, resp.content)
        att = Attachment.objects.get(pk=resp.json()["id"])
        self.assertEqual(att.company_id, self.company_a.id)

    def test_upload_against_foreign_entity_is_rejected(self):
        resp = self._upload(self.partner_b.id)
        self.assertIn(resp.status_code, (403, 404), resp.content)
        self.assertEqual(Attachment.objects.count(), 0)

    def test_upload_to_unsupported_entity_type_is_rejected(self):
        resp = self.client.post(
            "/api/v1/documents/attachments/upload/",
            {
                "entity_type": "audit.AuditLog",
                "entity_id": "00000000-0000-0000-0000-000000000000",
                "file": SimpleUploadedFile("x.txt", b"x", content_type="text/plain"),
            },
            format="multipart",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertEqual(resp.json()["error"]["code"], "documents.entity.unsupported")

    def test_upload_to_nonexistent_record_is_404(self):
        resp = self._upload("00000000-0000-0000-0000-000000000000")
        self.assertEqual(resp.status_code, 404, resp.content)

    def test_list_excludes_foreign_attachments(self):
        self._upload(self.partner_a.id)  # own company — visible
        foreign = Attachment.objects.create(
            entity_type="partners.Partner",
            entity_id=str(self.partner_b.id),
            company=self.company_b,
            original_filename="foreign.txt",
        )
        ids = [
            row["id"]
            for row in self.client.get("/api/v1/documents/attachments/").json()["results"]
        ]
        self.assertNotIn(str(foreign.pk), ids)

    def test_download_of_foreign_attachment_is_404(self):
        foreign = Attachment.objects.create(
            entity_type="partners.Partner",
            entity_id=str(self.partner_b.id),
            company=self.company_b,
            original_filename="foreign.txt",
        )
        resp = self.client.get(f"/api/v1/documents/attachments/{foreign.pk}/download/")
        self.assertEqual(resp.status_code, 404)

    def test_delete_of_foreign_attachment_is_404(self):
        foreign = Attachment.objects.create(
            entity_type="partners.Partner",
            entity_id=str(self.partner_b.id),
            company=self.company_b,
            original_filename="foreign.txt",
        )
        resp = self.client.delete(f"/api/v1/documents/attachments/{foreign.pk}/")
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Attachment.all_objects.filter(pk=foreign.pk).exists())

    def test_superuser_sees_all_companies(self):
        from apps.core.tests.factories import make_superuser

        self._upload(self.partner_a.id)
        Attachment.objects.create(
            entity_type="partners.Partner",
            entity_id=str(self.partner_b.id),
            company=self.company_b,
            original_filename="foreign.txt",
        )
        admin = make_superuser()
        grant(admin, "documents.attachment.view")
        ids = [
            row["id"]
            for row in auth_client(admin).get("/api/v1/documents/attachments/").json()["results"]
        ]
        self.assertEqual(len(ids), 2)
