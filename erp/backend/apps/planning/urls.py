from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.planning import views

router = DefaultRouter()
router.register("policies", views.PlanningPolicyViewSet, basename="planning-policy")

urlpatterns = [path("", include(router.urls))]
