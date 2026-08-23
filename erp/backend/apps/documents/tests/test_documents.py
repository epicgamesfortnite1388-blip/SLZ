"""Document upload / download / authorization tests."""

from __future__ import annotations

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.core.tests.factories import auth_client, grant, make_company, make_user
from apps.documents.models import Attachment
from apps.partners.models import Partner


@override_settings(DOCUMENTS_ALLOWED_EXTENSIONS=["txt", "pdf"])
class DocumentTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.partner = Partner.objects.create(
            company=self.company, code="P-1", name_fa="شریک", is_customer=True
        )
        self.user = make_user()
        grant(self.user, "documents.attachment.view", "documents.attachment.delete")
        # make_user() auto-joins every existing company, so this user is a
        # member of self.company here (required by the Q-055 upload guard).
        self.client = auth_client(self.user)

    def _upload(self, name="spec.txt", content=b"hello"):
        return self.client.post(
            "/api/v1/documents/attachments/upload/",
            {
                "entity_type": "partners.Partner",
                "entity_id": str(self.partner.id),
                "file": SimpleUploadedFile(name, content, content_type="text/plain"),
            },
            format="multipart",
        )

    def test_upload_creates_attachment(self):
        resp = self._upload()
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(Attachment.objects.count(), 1)
        att = Attachment.objects.first()
        self.assertEqual(att.entity_id, str(self.partner.id))
        # The company is resolved from the pinned entity (Q-055).
        self.assertEqual(att.company_id, self.company.id)
        self.assertTrue(att.checksum_sha256)

    def test_disallowed_extension_rejected(self):
        resp = self._upload(name="danger.exe", content=b"x")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "documents.file.type_not_allowed")

    def test_download_streams_original_name(self):
        self._upload(name="spec.txt", content=b"payload")
        att = Attachment.objects.first()
        resp = self.client.get(f"/api/v1/documents/attachments/{att.pk}/download/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("spec.txt", resp["Content-Disposition"])

    def test_view_requires_permission(self):
        other = make_user(email="nop@slz.test")
        resp = auth_client(other).get("/api/v1/documents/attachments/")
        self.assertEqual(resp.status_code, 403)
