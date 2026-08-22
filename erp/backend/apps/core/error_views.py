"""Root HTTP error handlers preserving the JSON error contract for API paths.

Django's URL-resolver 404s (e.g. path-traversal segments such as
``/api/v1/x/../../etc/passwd``) never reach DRF, so without these handlers
malformed URLs would return the HTML error page and break the documented JSON
envelope for API consumers. Non-API paths keep Django's default pages.
"""

from __future__ import annotations

from django.http import JsonResponse

from apps.core.middleware import get_correlation_id


def _is_api_request(request) -> bool:
    return request.path.startswith("/api/")


def _json_error(status: int, error_type: str, message: str) -> JsonResponse:
    return JsonResponse(
        {
            "error": {
                "type": error_type,
                "message": message,
                "details": None,
                "code": None,
                "correlation_id": get_correlation_id() or "",
            }
        },
        status=status,
    )


def handler404(request, exception=None):
    if not _is_api_request(request):
        from django.views.defaults import page_not_found

        return page_not_found(request, exception)
    return _json_error(404, "NotFoundError", "The requested resource was not found.")


def handler500(request):
    if not _is_api_request(request):
        from django.views.defaults import server_error

        return server_error(request)
    return _json_error(500, "SystemError", "An unexpected system error occurred.")
