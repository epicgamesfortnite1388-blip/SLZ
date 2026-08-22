from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.partners import views

router = DefaultRouter()
router.register("partners", views.PartnerViewSet, basename="partner")
router.register("customers", views.CustomerViewSet, basename="customer")
router.register("suppliers", views.SupplierViewSet, basename="supplier")
router.register("contacts", views.ContactViewSet, basename="contact")
router.register("addresses", views.AddressViewSet, basename="address")

urlpatterns = [path("", include(router.urls))]
