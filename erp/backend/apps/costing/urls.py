from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.costing import views

router = DefaultRouter()
router.register("cost-layers", views.CostLayerViewSet, basename="costlayer")

urlpatterns = [path("", include(router.urls))]
