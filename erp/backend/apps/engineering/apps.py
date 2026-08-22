from __future__ import annotations

from django.apps import AppConfig


class EngineeringConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.engineering"
    verbose_name = "Product Engineering"
