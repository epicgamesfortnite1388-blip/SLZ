"""Root URL configuration.

Health/readiness probes live at the root; all business/platform APIs are
namespaced under ``/api/v1/``.
"""

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

from apps.core import health

# Root error handlers: keep the JSON error envelope for /api/ paths even when a
# request fails at the URL-resolver level (never reaches DRF).
handler404 = "apps.core.error_views.handler404"
handler500 = "apps.core.error_views.handler500"

api_v1 = [
    path("auth/", include("apps.identity.urls")),
    path("organization/", include("apps.organization.urls")),
    path("audit/", include("apps.audit.urls")),
    path("documents/", include("apps.documents.urls")),
    path("localization/", include("apps.localization.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("workflow/", include("apps.workflow.urls")),
    # Task 004 — Master Data.
    path("partners/", include("apps.partners.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("hr/", include("apps.hr.urls")),
    # Task 005 — Product Engineering.
    path("engineering/", include("apps.engineering.urls")),
    # Task 006 — Manufacturing (BOM & Routing).
    path("manufacturing/", include("apps.manufacturing.urls")),
    # Task 007 — Inventory Foundation (warehouses & access).
    path("inventory/", include("apps.inventory.urls")),
    # Task 008 — Quality (inspection / quality plan definition).
    path("quality/", include("apps.quality.urls")),
    # Task 009 — Procurement (requisitions & purchase orders).
    path("procurement/", include("apps.procurement.urls")),
    # Task 010 — Sales (customer orders).
    path("sales/", include("apps.sales.urls")),
    # Task 011 — Production (work orders).
    path("production/", include("apps.production.urls")),
    # Task 012 — Costing (dated weighted-average valuation).
    path("costing/", include("apps.costing.urls")),
    # Task 013 — Shipment (allocation + delivery).
    path("shipment/", include("apps.shipment.urls")),
    # Task 014 — Planning (reorder policies + planning run).
    path("planning/", include("apps.planning.urls")),
    # Task 015 — Recall (traceability-based quality events).
    path("recall/", include("apps.recall.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health.health, name="health"),
    path("ready/", health.ready, name="ready"),
    path("api/v1/", include((api_v1, "api"), namespace="v1")),
]
