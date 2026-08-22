"""Localization info endpoint (supported locales, server time in both calendars)."""

from __future__ import annotations

from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.localization.calendar import dual_calendar, format_jalali
from apps.localization.timezone import now_utc


class LocaleInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = now_utc()
        return Response(
            {
                "languages": [
                    {"code": code, "name": name, "direction": "rtl" if code == "fa" else "ltr"}
                    for code, name in settings.LANGUAGES
                ],
                "default_language": settings.LANGUAGE_CODE,
                "default_timezone": settings.TIME_ZONE,
                "server_time": {
                    **dual_calendar(now.date()),
                    "iso": now.isoformat(),
                    "jalali_datetime": format_jalali(
                        now, fmt="%Y/%m/%d %H:%M", persian_digits=False
                    ),
                },
            }
        )
