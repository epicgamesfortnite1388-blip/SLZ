from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.hr import views

router = DefaultRouter()
router.register("employees", views.EmployeeViewSet, basename="employee")

urlpatterns = [path("", include(router.urls))]
