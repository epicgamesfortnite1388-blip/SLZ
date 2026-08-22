from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.sales import views

router = DefaultRouter()
router.register("orders", views.SalesOrderViewSet, basename="salesorder")
router.register("order-lines", views.SalesOrderLineViewSet, basename="salesorderline")

urlpatterns = [path("", include(router.urls))]
