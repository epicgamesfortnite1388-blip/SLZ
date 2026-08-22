from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.manufacturing import views

router = DefaultRouter()
router.register("work-centers", views.WorkCenterViewSet, basename="workcenter")
router.register("machines", views.MachineViewSet, basename="machine")
router.register("boms", views.BillOfMaterialsViewSet, basename="bom")
router.register("bom-revisions", views.BomRevisionViewSet, basename="bomrevision")
router.register("bom-lines", views.BomLineViewSet, basename="bomline")
router.register("routings", views.RoutingViewSet, basename="routing")
router.register("routing-revisions", views.RoutingRevisionViewSet, basename="routingrevision")
router.register("routing-operations", views.RoutingOperationViewSet, basename="routingoperation")

urlpatterns = [path("", include(router.urls))]
