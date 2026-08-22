from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.engineering import views

router = DefaultRouter()
router.register("customer-products", views.CustomerProductViewSet, basename="customerproduct")
router.register("specifications", views.SpecificationRevisionViewSet, basename="specification")
router.register("spec-layers", views.SpecLayerViewSet, basename="speclayer")
router.register("spec-colors", views.SpecColorViewSet, basename="speccolor")
router.register("spec-parameters", views.SpecParameterViewSet, basename="specparameter")
router.register("tooling-assets", views.ToolingAssetViewSet, basename="toolingasset")

urlpatterns = [path("", include(router.urls))]
