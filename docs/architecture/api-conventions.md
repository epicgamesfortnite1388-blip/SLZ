# API Conventions

All application endpoints live under a version prefix: **`/api/v1/`**. The
version is set once (`API_VERSION` in settings) and namespaced in
`config/urls.py`. A future breaking change introduces `/api/v2/` alongside v1.

Outside the version prefix live only operational endpoints: `/admin/`,
`/health/`, `/ready/`.

## Authentication

JWT via `djangorestframework-simplejwt`.

| Endpoint                     | Method | Purpose                                       |
|------------------------------|--------|-----------------------------------------------|
| `/api/v1/auth/login/`        | POST   | `{email, password}` → `{access, refresh, user}` |
| `/api/v1/auth/refresh/`      | POST   | `{refresh}` → `{access}`                       |
| `/api/v1/auth/logout/`       | POST   | `{refresh}` → blacklists the refresh token     |
| `/api/v1/auth/me/`           | GET    | current user profile + permission codes        |
| `/api/v1/auth/me/`           | PATCH  | update own `language` / `timezone`             |

Send the access token as `Authorization: Bearer <token>`. Access tokens are
short-lived (`JWT_ACCESS_MINUTES`, default 60); refresh tokens rotate and the
old one is blacklisted on refresh (`JWT_REFRESH_DAYS`, default 7). Login and
logout write `LOGIN` / `LOGOUT` audit entries.

## Authorization

Permissions use the format **`module.resource.action`**, e.g.
`organization.company.view`, `identity.role.manage`. See
[security.md](security.md#rbac) for the model.

Views declare a `permission_map` (per HTTP verb) or a single
`required_permission`; the `HasPermission` DRF class enforces it. Superusers
bypass checks. Missing permission → `AuthorizationError` (403); missing/invalid
token → `AuthenticationError` (401).

## Standard error envelope

Every error — validation, auth, not-found, conflict, business-rule, or
unexpected — is returned in one shape by
`apps.core.handlers.standardized_exception_handler`:

```json
{
  "error": {
    "type": "validation_error",
    "message": "Human-readable summary.",
    "details": { "field": ["what is wrong"] },
    "code": "optional_machine_code",
    "correlation_id": "0f1c…"
  }
}
```

The **seven** standardized error types (from `apps/core/exceptions.py`):

| `type`               | HTTP | Raise when …                                        |
|----------------------|------|-----------------------------------------------------|
| `validation_error`   | 400  | Input fails field/format/shape validation           |
| `authentication_error` | 401 | No/invalid credentials                             |
| `authorization_error` | 403 | Authenticated but lacks the required permission     |
| `not_found`          | 404  | Target entity does not exist (or is soft-deleted)   |
| `conflict`           | 409  | Uniqueness / concurrency / state conflict           |
| `business_rule_error`| 422  | A domain invariant is violated                      |
| `system_error`       | 500  | Unhandled/unexpected server fault                   |

Unknown exceptions are logged as `system_error` with the `correlation_id`; raw
tracebacks are never leaked. Auth challenge headers (`WWW-Authenticate`) are
preserved.

## Success responses

- Single resource: the serialized object.
- Collection: **paginated** (see below).
- Mutations return the resulting resource representation where practical.
- `204 No Content` for deletes.

## Pagination

`apps.core.pagination.StandardPagination` (page-number based):

```json
{
  "count": 137,
  "total_pages": 6,
  "page": 2,
  "page_size": 25,
  "next": "http://…?page=3",
  "previous": "http://…?page=1",
  "results": [ … ]
}
```

- Default page size from `API_PAGE_SIZE` (default 25).
- Client override via `?page_size=`, capped at `max_page_size` (200).

## Filtering & sorting

- Filtering via `django-filter` (`?field=value`); each viewset declares its
  `filterset_fields`.
- Sorting via DRF `OrderingFilter` (`?ordering=field` / `?ordering=-field`).
- Free-text search via `SearchFilter` (`?search=`) where a viewset opts in.

## Correlation IDs

Send `X-Correlation-ID` to trace a request end-to-end; if absent the server
generates one. It is attached to logs, stored on audit rows, embedded in error
envelopes, and echoed on the response header. The SPA generates one per request
automatically.

## Localization of payloads

Datetimes are serialized in **UTC (ISO-8601)**; Jalali and localized number
formatting are presentation concerns handled by the client or by explicit
localization endpoints — never stored pre-formatted. See
[data-lifecycle.md](data-lifecycle.md) and the `localization` app.
