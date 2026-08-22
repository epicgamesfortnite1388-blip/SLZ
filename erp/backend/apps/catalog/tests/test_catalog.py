"""Catalog master-data tests: UoM + conversions, taxonomy, product, material."""

from __future__ import annotations

from django.test import TestCase

from apps.catalog.models import (
    Material,
    Product,
    ProductClass,
    ProductFamily,
    ProductGroup,
    ProductType,
    UnitOfMeasure,
)
from apps.core.tests.factories import auth_client, grant, make_company, make_user


class UomTests(TestCase):
    def setUp(self):
        self.user = make_user()
        grant(self.user, "catalog.uom.view", "catalog.uom.manage")
        self.client = auth_client(self.user)

    def _uom(self, code, dimension="MASS"):
        return UnitOfMeasure.objects.create(code=code, name_fa=code, dimension=dimension)

    def test_create_uom(self):
        resp = self.client.post(
            "/api/v1/catalog/uoms/",
            {"code": "KG", "name_fa": "کیلوگرم", "dimension": "MASS"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)

    def test_conversion_rejects_same_unit(self):
        kg = self._uom("KG")
        resp = self.client.post(
            "/api/v1/catalog/uom-conversions/",
            {"from_uom": str(kg.id), "to_uom": str(kg.id), "factor": "1.0"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_conversion_rejects_cross_dimension(self):
        kg = self._uom("KG", "MASS")
        m = self._uom("M", "LENGTH")
        resp = self.client.post(
            "/api/v1/catalog/uom-conversions/",
            {"from_uom": str(kg.id), "to_uom": str(m.id), "factor": "2.0"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_conversion_rejects_non_positive_factor(self):
        kg = self._uom("KG", "MASS")
        g = self._uom("G", "MASS")
        resp = self.client.post(
            "/api/v1/catalog/uom-conversions/",
            {"from_uom": str(kg.id), "to_uom": str(g.id), "factor": "0"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_conversion_valid_same_dimension(self):
        kg = self._uom("KG", "MASS")
        g = self._uom("G", "MASS")
        resp = self.client.post(
            "/api/v1/catalog/uom-conversions/",
            {"from_uom": str(kg.id), "to_uom": str(g.id), "factor": "1000"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)


class TaxonomyAndProductTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.user = make_user()
        grant(
            self.user,
            "catalog.producttaxonomy.view",
            "catalog.producttaxonomy.manage",
            "catalog.product.view",
            "catalog.product.manage",
        )
        self.client = auth_client(self.user)
        self.uom = UnitOfMeasure.objects.create(code="EA", name_fa="عدد", dimension="COUNT")
        self.group = ProductGroup.objects.create(code="FOOD", name_fa="بسته‌بندی مواد غذایی")

    def _family(self):
        t = ProductType.objects.create(code="FILM", name_fa="فیلم")
        c = ProductClass.objects.create(product_type=t, code="LAMINATE", name_fa="لمینت")
        return ProductFamily.objects.create(product_class=c, code="POUCH", name_fa="پاکت")

    def test_taxonomy_hierarchy_created(self):
        fam = self._family()
        self.assertEqual(fam.product_class.product_type.code, "FILM")

    def test_create_thin_product(self):
        fam = self._family()
        resp = self.client.post(
            "/api/v1/catalog/products/",
            {
                "company": str(self.company.id),
                "code": "P-100",
                "name_fa": "پاکت قهوه ۱ کیلو",
                "product_group": str(self.group.id),
                "family": str(fam.id),
                "base_uom": str(self.uom.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertTrue(Product.objects.filter(code="P-100").exists())


class MaterialTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.user = make_user()
        grant(self.user, "catalog.material.view", "catalog.material.manage")
        self.client = auth_client(self.user)
        self.uom = UnitOfMeasure.objects.create(code="KG", name_fa="کیلوگرم", dimension="MASS")

    def test_create_material_with_subtype(self):
        resp = self.client.post(
            "/api/v1/catalog/materials/",
            {
                "company": str(self.company.id),
                "code": "INK-BLK",
                "name_fa": "مرکب مشکی",
                "subtype": "INK",
                "base_uom": str(self.uom.id),
                "shelf_life_days": 365,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        mat = Material.objects.get(code="INK-BLK")
        self.assertEqual(mat.subtype, "INK")

    def test_material_rejects_unknown_subtype(self):
        resp = self.client.post(
            "/api/v1/catalog/materials/",
            {
                "company": str(self.company.id),
                "code": "X",
                "name_fa": "نامعتبر",
                "subtype": "NOT_A_SUBTYPE",
                "base_uom": str(self.uom.id),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400, resp.content)
