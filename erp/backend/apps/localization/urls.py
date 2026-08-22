from django.urls import path

from apps.localization.views import LocaleInfoView

urlpatterns = [path("info/", LocaleInfoView.as_view(), name="locale-info")]
