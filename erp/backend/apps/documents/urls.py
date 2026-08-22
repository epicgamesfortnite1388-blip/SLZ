from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.documents.views import AttachmentViewSet

router = DefaultRouter()
router.register("attachments", AttachmentViewSet, basename="attachment")

urlpatterns = [path("", include(router.urls))]
