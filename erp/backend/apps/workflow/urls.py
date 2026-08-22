from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.workflow import views

router = DefaultRouter()
router.register("definitions", views.WorkflowDefinitionViewSet, basename="workflow-definition")
router.register("instances", views.WorkflowInstanceViewSet, basename="workflow-instance")

urlpatterns = [path("", include(router.urls))]
