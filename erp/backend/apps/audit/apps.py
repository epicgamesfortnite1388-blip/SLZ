from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit"
    verbose_name = "Audit Trail"

    def ready(self):
        # Register event-bus subscribers that mirror domain events to audit.
        from apps.audit import subscribers  # noqa: F401
