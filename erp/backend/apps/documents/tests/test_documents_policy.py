"""Attachment policy edge cases: size limit, soft-delete visibility, and
delete authorization — complementing the base upload/download tests.

Upload bytes are kept out of the repository by ``MEDIA_ROOT`` in
``config.settings.test`` (temp dir), so these tests never pollute backend/media.
"""

from __future__ import annotations

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.core.tests.factories import auth_client, grant, make_company, make_user
from apps.partners.models import Partner
from apps.documents.models import Attachment
from apps.identity.models import Permission, Role, RolePermission, UserRole


def grant_isolated(user, *codes):
    """Like ``grant`` but with a per-call role, so permission sets stay
    independent between users (the shared factory role would leak grants)."""
    role = Role.objects.create(
        code=f"role_{user.pk}",
        name_en="Isolated",
        name_fa="موقت",
    )
    UserRole.objects.create(user=user, role=role)
    for code in codes:
        perm, _ = Permission.objects.get_or_create(
            code=code, defaults={"module": code.split(".", 1)[0]}
        )
        RolePermission.objects.get_or_create(role=role, permission=perm)


@override_settings(DOCUMENTS_ALLOWED_EXTENSIONS=["txt"])
class DocumentPolicyTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.partner = Partner.objects.create(
            company=self.company, code="P-9", name_fa="شریک", is_customer=True
        )
        self.user = make_user()
        grant(
            self.user,
            "documents.attachment.view",
            "documents.attachment.delete",
        )
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

    @override_settings(DOCUMENTS_MAX_UPLOAD_BYTES=4)
    def test_oversize_upload_rejected_with_policy_code(self):
        resp = self._upload(content=b"toolarge")
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertEqual(resp.json()["error"]["code"], "documents.file.too_large")
        self.assertEqual(Attachment.objects.count(), 0)

    def test_soft_deleted_attachment_hidden_from_list_and_download(self):
        self._upload()
        att = Attachment.objects.first()
        resp = self.client.delete(f"/api/v1/documents/attachments/{att.pk}/")
        self.assertEqual(resp.status_code, 204, resp.content)

        # Metadata is retained (soft delete) but hidden from the alive managers.
        self.assertEqual(Attachment.objects.count(), 0)
        self.assertEqual(Attachment.all_objects.count(), 1)

        listing = self.client.get("/api/v1/documents/attachments/")
        ids = [row["id"] for row in listing.data["results"]]
        self.assertNotIn(str(att.pk), ids)

        download = self.client.get(f"/api/v1/documents/attachments/{att.pk}/download/")
        self.assertEqual(download.status_code, 404)

    def test_delete_requires_the_delete_permission(self):
        self._upload()
        att = Attachment.objects.first()

        viewer_only = make_user(email="viewonly@slz.test")
        grant_isolated(viewer_only, "documents.attachment.view")
        forbidden = auth_client(viewer_only).delete(f"/api/v1/documents/attachments/{att.pk}/")
        self.assertEqual(forbidden.status_code, 403, forbidden.content)
        self.assertEqual(Attachment.objects.count(), 1)

    def test_upload_without_any_documents_permission_is_rejected(self):
        outsider = make_user(email="outsider@slz.test")
        resp = auth_client(outsider).post(
            "/api/v1/documents/attachments/upload/",
            {
                "entity_type": "partners.Partner",
                "entity_id": str(self.partner.id),
                "file": SimpleUploadedFile("spec.txt", b"x", content_type="text/plain"),
            },
            format="multipart",
        )
        self.assertEqual(resp.status_code, 403, resp.content)
        self.assertEqual(Attachment.objects.count(), 0)

    def test_download_header_cannot_be_broken_out_of(self):
        """A crafted filename must never escape the Content-Disposition
        quoted-string (header injection) or crash header serialization."""
        hostile = 'evil".txt'
        resp = self._upload(name=hostile)
        self.assertEqual(resp.status_code, 201, resp.content)

        att = Attachment.objects.first()
        download = self.client.get(f"/api/v1/documents/attachments/{att.pk}/download/")
        self.assertEqual(download.status_code, 200)
        # The quote is neutralized so the value stays a single quoted-string.
        self.assertEqual(download["Content-Disposition"], 'attachment; filename="evil_.txt"')

    def test_quoted_header_filename_neutralizes_control_chars(self):
        from apps.documents.validators import quoted_header_filename

        raw = 'a"b\\c\rd\ne.txt'
        safe = quoted_header_filename(raw)
        for ch in ('"', "\\", "\r", "\n"):
            self.assertNotIn(ch, safe)
        self.assertEqual(safe, "a_b_c_d_e.txt")
