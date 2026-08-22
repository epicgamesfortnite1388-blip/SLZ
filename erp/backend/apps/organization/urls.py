from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.organization import views

router = DefaultRouter()
router.register("companies", views.CompanyViewSet, basename="company")
router.register("sites", views.SiteViewSet, basename="site")
router.register("departments", views.DepartmentViewSet, basename="department")
router.register("site-capabilities", views.SiteCapabilityViewSet, basename="site-capability")

urlpatterns = [path("", include(router.urls))]
