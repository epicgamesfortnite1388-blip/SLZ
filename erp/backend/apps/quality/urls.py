from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.quality import views

router = DefaultRouter()
router.register(
    "characteristics", views.QualityCharacteristicViewSet, basename="qualitycharacteristic"
)
router.register("plans", views.QualityPlanViewSet, basename="qualityplan")
router.register("plan-revisions", views.QualityPlanRevisionViewSet, basename="qualityplanrevision")
router.register("plan-items", views.QualityPlanItemViewSet, basename="qualityplanitem")

urlpatterns = [path("", include(router.urls))]
