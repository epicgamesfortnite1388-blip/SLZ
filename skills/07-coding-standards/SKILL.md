# Skill 07 — Coding Standards

## Purpose
The permanent engineering standard for the SLZ ERP. Match the existing `erp/` foundation; do not introduce new conventions, libraries, or patterns without cause.

## When to Read This Skill
Mandatory on every coding task, before writing or modifying code.

## Source of Truth
- Code: `erp/backend/apps/core/` (reference implementation), `erp/backend/pyproject.toml`, `erp/backend/requirements/`, `erp/frontend/package.json`.
- `docs/architecture/*` (all files).

## Core Rules
1. Match existing patterns in `apps/core` and existing apps before inventing new ones.
2. Business logic in services; views thin; frontend presentation-only.
3. Everything auditable and (where master data) versioned; nothing hard-deleted that carries history.
4. Tests accompany every feature; do not mark work done with failing/absent tests.
5. Small, focused commits; no secrets; no generated garbage; no unrelated changes.

## Domain Concepts

### Backend (Python / Django / DRF)
- **Stack (pinned):** Python 3.11, Django 4.2.16, DRF 3.15.2, `djangorestframework-simplejwt`, `django-filter`, PostgreSQL (`psycopg2-binary`), Celery 5.4 + Redis, `jdatetime` (Jalali).
- **Style:** `black` (line-length 100), `isort` (black profile, `known_first_party = ["apps","config"]`), `flake8`. Migrations are excluded from formatting. Use `from __future__ import annotations` and type hints as in `apps/core`.
- **Service/domain layer:** use-cases live in `services.py` and own transactions + event publication via `atomic_with_events`. Views/serializers never own business rules.
- **Serializers:** wire (de)serialization and input/shape validation only.
- **Validation:** validate input and domain invariants **before** opening the transaction; raise the correct standardized error (`ValidationError` 400, `BusinessRuleError` 422, `ConflictError` 409, `NotFoundError` 404, `AuthenticationError` 401, `AuthorizationError` 403, `SystemError` 500) from `apps/core/exceptions.py`.
- **Transactions:** one `atomic_with_events` block per use-case; audit/events inside; slow/remote work deferred to post-commit subscribers/Celery.
- **Permissions:** declare `permission_map` (per verb) or `required_permission` as `module.resource.action`; enforced by `HasPermission`.
- **Migrations:** additive, reviewed, committed. Generate explicitly; the source of truth for schema.

### Frontend (TypeScript / React)
- **Stack (pinned):** React 18.3, TypeScript 5.6 (strict), Vite 5, React Router 6, i18next/react-i18next, Vitest + Testing Library, ESLint (`--max-warnings 0`).
- **Component architecture:** presentational UI in `components/ui`, layout in `components/layout`, pages in `pages/`, routing guards in `routes/`. No business rules in components.
- **State management:** React context/hooks (see `auth/AuthContext.tsx`); no browser `localStorage` for business state beyond auth/session as already established. Do not add a state library without cause.
- **Forms & API:** call the backend only via `api/client.ts` (`apiClient`) — it injects auth, correlation IDs, refresh-on-401, and typed `ApiError`. Do not hand-roll `fetch`.
- **Localization:** all user-facing strings via i18next (fa/en); default fa RTL. Use `i18n/useDirection.ts` for RTL/LTR. Never hard-code Persian/English strings in components.
- **Accessibility:** semantic HTML, labelled inputs (`FormField`), keyboard/focus support; respect RTL in layout.

### Database
- **Naming:** Django default table names (`<app>_<model>`); `snake_case` fields; booleans as predicates (`is_active`); FKs singular; `*_at` datetimes, `*_date` dates; choices via `TextChoices`.
- **Keys:** UUID v4 PKs (`UUIDModel`); business numbers (order no., product code) are **separate fields**, never the PK.
- **Timestamps/audit:** `TimeStampedModel`/`AuthoredModel`/`BaseModel`; datetimes UTC-aware (`USE_TZ=True`); Jalali is presentation only.
- **Foreign keys & constraints:** index FKs used in filters; enforce natural keys via `unique`/`UniqueConstraint` (violations → `ConflictError`); prefer `PROTECT`/`SET_NULL` over `CASCADE` for master data.
- **Money/quantities:** `DecimalField` with explicit `max_digits`/`decimal_places`; never floats; currency code beside amount (default IRR).
- **Bilingual:** `name_fa` (required) + `name_en` (optional) where entities carry human labels.
- **Soft deletion where appropriate:** `SoftDeleteModel` only where retention matters (documents, master data); transient rows hard-delete. Do not apply blindly.

### Testing
Every feature needs the appropriate mix:
- **Unit tests** — models/services/domain invariants.
- **Integration tests** — service + DB + events/audit.
- **API tests** — endpoint behavior, error envelope, pagination.
- **Permission tests** — RBAC allow/deny per role.
- **Domain/business-rule tests** — the confirmed rule holds (e.g. revision immutability, atomic posting, QC_HOLD blocks issue).
Backend: `manage.py test` (Celery eager in tests). Frontend: `vitest run`, `tsc -b --noEmit`, `eslint`.

### Git
- Small, single-purpose commits with meaningful messages (what + why).
- No secrets/credentials committed (`.env` is example-only).
- No generated artifacts, build output, or `__pycache__`.
- No unrelated changes bundled in; keep diffs reviewable.
- Follow repo git-safety norms; do not force-push shared branches.

## Required Behaviors
- Reuse `apps/core` base classes, versioning, transactions, events, exceptions, pagination.
- Run formatters/linters and the test suite before declaring done.
- Keep configurable/OPEN business values in data/config, never hard-coded.

## Forbidden Behaviors
- No business logic in views, serializers, or React components.
- No raw `fetch` on the frontend; no direct ORM writes bypassing services for auditable entities.
- No floats for money/quantity; no naive datetimes; no pre-formatted locale strings in the DB.
- No new dependency, state library, or datastore without a documented need.
- No committing secrets, generated files, or unrelated changes.

## Implementation Guidance
When adding a module: create the app, subclass foundation bases, write service + serializer + thin view + permission map + urls, publish standard events, add migrations, then write the full test set. Mirror an existing app's file layout.

## Examples
- *New create-use-case:* `validate() → atomic_with_events(): create + publish(EntityCreated) → return`; view calls the service and returns the serialized resource.
- *New list endpoint:* declare `filterset_fields`/`ordering`, use `StandardPagination`, gate with a permission code.

## Common Mistakes
- Logic creeping into serializers/views/components.
- Forgetting audit events, so the trail diverges.
- `CASCADE` FKs on master data; float money; missing `name_fa`.
- Skipping permission or business-rule tests.

## Validation Checklist
- [ ] `black`/`isort`/`flake8` clean; `tsc`/`eslint` clean.
- [ ] Backend + frontend tests written and passing (`manage.py test`, `vitest run`).
- [ ] Logic in services; views/components thin; API via `apiClient`.
- [ ] UUID PKs, Decimal money, UTC datetimes, bilingual labels, indexed FKs.
- [ ] Standard events + audit fire; permissions declared and tested.
- [ ] No secrets/generated/unrelated changes in the commit.

## Related Documentation
`docs/architecture/*` · `erp/backend/apps/core/*` · `erp/frontend/src/api/client.ts`

## Skill Dependencies
Depends on: `01-slz-domain`, `02-erp-architecture`. Mandatory alongside `08-agent-workflow` on every task.
