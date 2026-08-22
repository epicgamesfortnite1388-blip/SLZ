from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.catalog import views

router = DefaultRouter()
router.register("uoms", views.UnitOfMeasureViewSet, basename="uom")
router.register("uom-conversions", views.UomConversionViewSet, basename="uom-conversion")
router.register("product-groups", views.ProductGroupViewSet, basename="product-group")
router.register("product-types", views.ProductTypeViewSet, basename="product-type")
router.register("product-classes", views.ProductClassViewSet, basename="product-class")
router.register("product-families", views.ProductFamilyViewSet, basename="product-family")
router.register("products", views.ProductViewSet, basename="product")
router.register("materials", views.MaterialViewSet, basename="material")

urlpatterns = [path("", include(router.urls))]
