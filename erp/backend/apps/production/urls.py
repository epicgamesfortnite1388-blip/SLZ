from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.production import views

router = DefaultRouter()
router.register("orders", views.ProductionOrderViewSet, basename="productionorder")
router.register("material-issues", views.MaterialIssueViewSet, basename="material-issue")
router.register("outputs", views.ProductionOutputViewSet, basename="production-output")

urlpatterns = [path("", include(router.urls))]
