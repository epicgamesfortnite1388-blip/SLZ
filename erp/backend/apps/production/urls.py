from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.production import views

router = DefaultRouter()
router.register("orders", views.ProductionOrderViewSet, basename="productionorder")

urlpatterns = [path("", include(router.urls))]
