"""Soft-delete and base-model behavior (using the concrete Company model)."""

from __future__ import annotations

from django.test import TestCase

from apps.organization.models import Company


class SoftDeleteTests(TestCase):
    def test_uuid_primary_key(self):
        company = Company.objects.create(code="C1", name_en="Acme", name_fa="اکمی")
        self.assertEqual(len(str(company.id)), 36)  # UUID string

    def test_soft_delete_hides_from_default_manager(self):
        company = Company.objects.create(code="C2", name_en="Beta", name_fa="بتا")
        company.delete()
        self.assertFalse(Company.objects.filter(pk=company.pk).exists())
        self.assertTrue(Company.all_objects.filter(pk=company.pk).exists())
        company.refresh_from_db()
        self.assertIsNotNone(company.deleted_at)

    def test_restore(self):
        company = Company.objects.create(code="C3", name_en="Gamma", name_fa="گاما")
        company.delete()
        company.restore()
        self.assertTrue(Company.objects.filter(pk=company.pk).exists())

    def test_hard_delete_removes_row(self):
        company = Company.objects.create(code="C4", name_en="Delta", name_fa="دلتا")
        pk = company.pk
        company.hard_delete()
        self.assertFalse(Company.all_objects.filter(pk=pk).exists())
