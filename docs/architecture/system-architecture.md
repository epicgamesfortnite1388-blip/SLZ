# System Architecture

## Style: modular monolith

The backend is a **single Django project** deployed as one unit. Module
boundaries are expressed as **Django apps** under `backend/apps/`, not as
separate services. This gives us clear ownership and separation without the
operational cost of microservices. If a module ever needs to be extracted, its
app boundary is the seam.

```
erp/
├── backend/                 # Django + DRF (the monolith)
│   ├── config/              # project settings, urls, celery, wsgi/asgi
│   │   ├── settings/        # base.py, dev.py, prod.py, test.py
│   │   ├── urls.py          # /admin, /health, /ready, /api/v1/*
│   │   └── celery.py
│   └── apps/
│       ├── core/            # base models, errors, events, pagination, health,
│       │                    #   correlation middleware, versioning, transactions
│       ├── identity/        # custom User, RBAC (Permission/Role), JWT auth
│       ├── organization/    # Company / Site / Department (structural master)
│       ├── audit/           # generic, module-independent audit trail
│       ├── documents/       # attachments + secure storage abstraction
│       ├── localization/    # Jalali/Gregorian, timezone, number/currency
│       ├── notifications/   # in-app + email/SMS/push interfaces
│       └── workflow/        # minimal configurable approval workflow
├── frontend/                # Vite + React 18 + TypeScript (SPA)
└── infrastructure/          # Dockerfiles, nginx, compose
```

### Foundation apps only

The eight apps above are **platform foundation**. Business modules (sales, crm,
engineering, inventory, manufacturing, quality, purchasing, maintenance,
finance, logistics) are **not** part of this task and must be added later as new
apps that depend on the foundation.

## Layers within an app

Each app follows the same internal layering so any developer can navigate any
module:

| Layer          | File(s)                | Responsibility                                   |
|----------------|------------------------|--------------------------------------------------|
| Models         | `models.py`            | Persistence, invariants, derived properties      |
| Managers       | `managers.py`          | Query scoping (e.g. alive/dead for soft delete)  |
| Services       | `services.py`          | Use-cases, cross-model orchestration, events     |
| Serializers    | `serializers.py`       | Wire (de)serialization + input validation        |
| Permissions    | `permissions.py`       | Per-view permission mapping                       |
| Views          | `views.py`             | HTTP concerns only; delegate to services/models  |
| URLs           | `urls.py`              | Routing, mounted under `/api/v1/`                 |
| Subscribers    | `subscribers.py`       | React to domain events (audit does this)         |

**Rule:** views stay thin. Anything that spans models, publishes events, or
must be transactional lives in a service function.

## Dependency rules

- Every app may depend on **`core`**.
- Apps may depend on **`identity`** (for the acting user) and **`localization`**
  (for formatting) freely.
- `audit` depends on nothing app-specific; it reacts to the **event bus** and
  serializes arbitrary instances generically.
- Foundation apps must **not** import from (not-yet-existing) business apps.
- Business apps (future) may depend on any foundation app but should prefer the
  documented base classes and the event bus over reaching into internals.

Cross-module communication at runtime prefers the **domain-event bus** over
direct imports, keeping modules loosely coupled.

## Request lifecycle

```
HTTP request
  → CorrelationIdMiddleware        (assigns/propagates X-Correlation-ID)
  → Authentication                 (JWT bearer or session)
  → Permission check               (HasPermission, module.resource.action)
  → View                           (parse/validate via serializer)
  → Service / model                (business rules; atomic_with_events)
      → DB write
      → audit + events queued to publish on commit
  → COMMIT
      → on_commit: events published → subscribers (audit, notifications)
  → Standardized response (or standardized error envelope)
      ← X-Correlation-ID echoed on the response
```

Errors raised anywhere are converted by `apps.core.handlers.standardized_exception_handler`
into the standard envelope (see [api-conventions.md](api-conventions.md)).

## Domain-event bus

`apps/core/events.py` provides a small **in-process** publish/subscribe bus.

- Events are dataclasses: `EntityCreated`, `EntityUpdated(changes=…)`,
  `EntityDeleted`, `EntityApproved`, `EntityRejected` (all subclass
  `DomainEvent`).
- `bus.subscribe(EventType, handler)` registers a handler; `bus.publish(event)`
  dispatches to handlers whose subscribed type matches by `isinstance`.
- Handler exceptions are swallowed and logged so one bad subscriber cannot break
  a request or another subscriber.
- Events are published **after commit** (see
  [transactions.md](transactions.md)), so subscribers never observe rolled-back
  state.

`audit` subscribes to entity events and writes the audit trail; `workflow`
publishes approval/rejection events and triggers notifications. This is the
preferred extension point for future modules.

## Background work

Celery + Redis are configured for asynchronous work (`config/celery.py`). The
foundation ships no business tasks; email/SMS/push delivery are the natural
first async consumers. In tests, Celery runs eagerly.

## Health & readiness

- `GET /health/` — liveness; always `{"status": "ok"}` if the process is up.
- `GET /ready/` — readiness; checks DB and cache connectivity, returns `200`
  when both are reachable, `503` otherwise. Use this for orchestrator probes.

## Frontend

A separate SPA (Vite + React 18 + TypeScript strict) talks to `/api/v1/`. It
owns presentation only: auth token handling with silent refresh, i18n
(fa RTL default / en LTR), a permission-aware routing guard, and a component
library. It contains **no** business screens and **no** fabricated data.
