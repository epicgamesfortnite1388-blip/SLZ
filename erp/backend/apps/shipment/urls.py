from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.shipment import views

router = DefaultRouter()
router.register("allocations", views.AllocationViewSet, basename="allocation")
router.register("deliveries", views.ShipmentViewSet, basename="shipment")

urlpatterns = [path("", include(router.urls))]
