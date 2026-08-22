from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.inventory import views

router = DefaultRouter()
router.register("warehouses", views.WarehouseViewSet, basename="warehouse")
router.register("warehouse-access", views.WarehouseAccessViewSet, basename="warehouse-access")

urlpatterns = [path("", include(router.urls))]
