from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.inventory import views

router = DefaultRouter()
router.register("warehouses", views.WarehouseViewSet, basename="warehouse")
router.register("warehouse-access", views.WarehouseAccessViewSet, basename="warehouse-access")
router.register("traceability-units", views.TraceabilityUnitViewSet, basename="traceability-unit")
router.register("genealogy-links", views.GenealogyLinkViewSet, basename="genealogy-link")
router.register("movements", views.StockMovementViewSet, basename="stock-movement")

urlpatterns = [path("", include(router.urls))]
