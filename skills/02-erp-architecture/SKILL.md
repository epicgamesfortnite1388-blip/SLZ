# Skill 02 — ERP Architecture

## Purpose
Define how the SLZ ERP/MES is built so agents extend the existing **platform foundation** consistently instead of inventing new architecture.

## When to Read This Skill
Mandatory on every coding task. Read before adding an app, model, endpoint, service, or migration.

> **CONTINGENT ON BUILD-vs-BUY (DR-000 / NQ-001).** This architecture describes the **custom** build (Task 003 foundation). The official SLZ study recommends **buying Microsoft Dynamics 365 F&O**, so DR-001 (Django), DR-002 (PostgreSQL) and DR-011 (React) are `PROPOSED — CONFLICT FLAGGED`, not confirmed. The platform foundation is real and built, but **domain implementation (Task 004+) is gated** until the business reaffirms build-over-buy. Treat this skill as "how the custom system is built if we build," not as a settled mandate.

## Source of Truth
- `docs/architecture/README.md` — foundation scope & reading order.
- `docs/architecture/system-architecture.md` — modular monolith, apps, layers, event bus.
- `docs/architecture/api-conventions.md` — REST surface, error envelope, pagination.
- `docs/architecture/database-conventions.md` — UUID keys, business numbers, bilingual fields.
- `docs/architecture/data-lifecycle.md` — soft delete, audit, correlation.
- `docs/architecture/versioning.md` — `VersionedRoot` / `Revision` pattern.
- `docs/architecture/transactions.md` — `atomic_with_events` write strategy.
- `docs/architecture/security.md` — authentication (JWT), RBAC grammar, file/upload safety, transport/CORS, secrets, audit baseline.
- Code: `erp/backend/apps/core/` is the canonical reference implementation.

## Core Rules
1. **Modular monolith.** One Django project; modules are **Django apps** under `backend/apps/`. An app boundary is the seam if extraction is ever needed.
2. **Do not introduce microservices** without a demonstrated, documented requirement *(NFR-015)*.
3. **Business logic lives in the backend domain/service layer.** The React frontend owns presentation only — no business rules, no fabricated data.
4. **Important transactions are atomic.** Consumption + output + genealogy + audit + cost capture for one use-case commit together or not at all *(constraint #8)*.
5. **Historical records are preserved.** Versioned entities never hard-delete; transactional records are append-only *(constraints #4/#5)*.
6. **Never bypass domain services with arbitrary DB writes.** Writes go through service functions using `atomic_with_events`; cross-module effects go through the domain-event bus, not direct imports.
7. **Database integrity matters.** Enforce natural keys and referential rules at the DB level; prefer `PROTECT`/`SET_NULL` over `CASCADE` for master data.
8. **Company/site scoping is inherent** *(SR-15/SR-16, DR-040 CONFIRMED)*. SLZ is multi-company (NEPTA; phase-1 SLZ+Helena) and multi-site (Tehran/Saveh). Master data, RBAC, warehouses, capacity and work orders are **scoped by company/site** — extend the `organization` foundation app, do not rebuild it, and do not assume single-company.

## Domain Concepts
**Stack (see `docs/requirements/decision-register.md`; DR-001..014):** Django 4.2 + DRF, PostgreSQL, Redis + Celery (background jobs), React 18 + TypeScript (Vite SPA). The build-vs-buy gate (DR-000/NQ-001) is **RESOLVED → custom build** (2026-08-21): the D365 F&O recommendation was considered and rejected, so DR-001/002/011 are the **confirmed** stack, no longer conflict-flagged.

**Foundation apps (platform only — no business logic):** `core`, `identity`, `organization`, `audit`, `documents`, `localization`, `notifications`, `workflow`. Business modules (sales, engineering, inventory, manufacturing, quality, purchasing, maintenance, finance, logistics) are **future apps** that depend on the foundation.

**App internal layers:** `models.py` (persistence/invariants) · `managers.py` (query scoping) · `services.py` (use-cases, transactions, events) · `serializers.py` (wire + input validation) · `permissions.py` (per-view permission map) · `views.py` (thin HTTP) · `urls.py` (mounted at `/api/v1/`) · `subscribers.py` (react to events).

**Cross-cutting primitives (in `apps/core`):**
- Base models: `UUIDModel`, `TimeStampedModel`, `AuthoredModel`, `BaseModel`, `SoftDeleteModel`.
- Versioning: `VersionedRoot` / `Revision` + `RevisionStatus` (DRAFT→ACTIVE→SUPERSEDED/ARCHIVED).
- Transactions: `atomic_with_events()` → validate → begin → apply → audit → commit → publish.
- Events: `EntityCreated/Updated/Deleted/Approved/Rejected` on an in-process bus, published **after commit**.
- Errors: seven standardized types (validation/authentication/authorization/not_found/conflict/business_rule/system) rendered by `standardized_exception_handler`.
- Permissions: `module.resource.action` codes enforced by `HasPermission`.
- Correlation: `X-Correlation-ID` propagated via middleware into logs/audit/errors.

## Required Behaviors
- Add new business capability as a **new app** depending on foundation apps.
- Put transactional/multi-model logic in `services.py`; keep views thin.
- Publish standard domain events so audit coverage is automatic.
- Use base model classes; pick the minimum (do **not** apply soft delete blindly).
- Adopt the `VersionedRoot`/`Revision` pattern for revisable master data (spec, BOM, routing, price, artwork).
- Store money/quantities as `Decimal` with explicit precision; datetimes UTC-aware.

## Forbidden Behaviors
- No business logic in foundation apps; no foundation app importing a business app.
- No raw `Model.objects.update()`/bulk writes that skip services, audit, or events for auditable entities.
- No microservice/new-datastore introduction without a documented requirement.
- No hard delete of versioned master data or append-only records.
- No presentation formatting (Persian digits, thousands, Jalali strings) persisted in the DB — format at the edge via `localization`.

## Implementation Guidance
- New endpoint → declare `permission_map`/`required_permission`, validate in serializer, delegate to a service, return standardized success/paginated response.
- New revisable entity → subclass `VersionedRoot` + `Revision`; downstream records reference a **revision id**, not the root.
- Cross-module reaction → subscribe to events in `subscribers.py`; do not call another module's internals.
- Slow/remote work (email, SMS, external calls) → Celery task triggered by a post-commit event, never inside the atomic block.

## Examples
- *Consume material + post output.* One service, one `atomic_with_events` block, publish `EntityCreated` for the batch; audit + genealogy land in the same transaction.
- *Notify on approval.* `workflow` publishes `EntityApproved`; a subscriber enqueues a notification post-commit — the write never waits on delivery.

## Common Mistakes
- Writing business rules in serializers/views instead of services.
- Referencing a versioned root instead of a specific revision from a transaction.
- Using `CASCADE` on master-data FKs, silently erasing history.
- Adding a second database or service to "make it scale" prematurely.

## Validation Checklist
- [ ] Is business logic in a service, not a view/serializer?
- [ ] Is the write wrapped in `atomic_with_events` with audit/events inside?
- [ ] Do transactions reference specific revision ids?
- [ ] Are FKs to master data non-cascading?
- [ ] Are permissions declared as `module.resource.action`?
- [ ] No foundation app importing a business app?

## Related Documentation
`docs/architecture/*` · `docs/requirements/decision-register.md` · `docs/requirements/requirements-baseline.md` (NFRs)

## Skill Dependencies
Depends on: `01-slz-domain`. Read with `07-coding-standards` and `08-agent-workflow`. Every domain skill (03–06) builds on this one.
