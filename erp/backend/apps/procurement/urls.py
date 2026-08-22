from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.procurement import views

router = DefaultRouter()
router.register("requisitions", views.PurchaseRequisitionViewSet, basename="requisition")
router.register(
    "requisition-lines",
    views.PurchaseRequisitionLineViewSet,
    basename="requisitionline",
)
router.register("orders", views.PurchaseOrderViewSet, basename="order")
router.register("goods-receipts", views.GoodsReceiptViewSet, basename="goodsreceipt")
router.register("order-lines", views.PurchaseOrderLineViewSet, basename="orderline")

urlpatterns = [path("", include(router.urls))]
