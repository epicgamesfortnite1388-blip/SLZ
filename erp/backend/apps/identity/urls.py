"""Identity URL routes."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.identity import views

router = DefaultRouter()
router.register("permissions", views.PermissionViewSet, basename="permission")
router.register("roles", views.RoleViewSet, basename="role")
router.register("users", views.UserViewSet, basename="user")

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("refresh/", views.RefreshView.as_view(), name="refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
