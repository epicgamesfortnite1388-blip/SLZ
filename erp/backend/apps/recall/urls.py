from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.recall import views

router = DefaultRouter()
router.register("recalls", views.RecallViewSet, basename="recall")
router.register("affected-units", views.RecallAffectedUnitViewSet, basename="recallaffectedunit")

urlpatterns = [path("", include(router.urls))]
