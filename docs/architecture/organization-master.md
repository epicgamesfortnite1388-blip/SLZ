# Organization Master (Company → Site)

This documents the **organization structural master** surface — the
`Company` → `Site` roots of the platform's company/site scoping (DR-040) — and
the audit-consistency hardening applied to its write path.

## Why this slice

Almost every business entity in the SLZ ERP references a `company`, and sites
carry timezone and production-capability context. The models
(`Company`, `Site`, `Department`, `ProductionCapability`, `SiteCapability`)
already existed in `apps.organization`, but only `SiteCapabilityViewSet` routed
writes through the audited service layer. `Company`, `Site` and `Department`
used a plain DRF `ModelViewSet`, so their creates/updates/deletes were **not**
transactional-with-audit — an inconsistency with every other master-data module.

This slice (a) hardens those three viewsets and (b) adds the browse + create
frontend for companies and sites. No business rule is introduced: the
unique-code rules (`Company.code` globally, `Site.code` per company) are
pre-existing model constraints enforced server-side.

## Audit-consistency hardening (backend)

`CompanyViewSet`, `SiteViewSet` and `DepartmentViewSet` now extend
`AuditedModelViewSet` (`apps/core/viewsets.py`) instead of `viewsets.ModelViewSet`.
Their `permission_map` / `required_permission` declarations are unchanged;
the redundant `permission_classes = [HasPermission]` lines were removed because
`AuditedModelViewSet` already sets them. As a result a create/update/delete now:

- runs through `apps.core.service` (`create_from_serializer` /
  `update_from_serializer` / `delete_instance`) inside a transaction,
- stamps `created_by = request.user`,
- emits `EntityCreated` / `EntityUpdated` / `EntityDeleted`, which the audit
  subscriber records as a CREATE / UPDATE / DELETE row with `entity_type`
  `organization.Company` / `organization.Site` / `organization.Department`.

No schema migration is required (behavioural change only) and no new RBAC
permission is needed — the `organization.company.*` / `organization.site.*` /
`organization.department.*` permissions are already seeded.

## API surface

Mounted under `/api/v1/organization/`:

- `companies/` — `Company` {code (unique), name_fa, name_en, is_active}
- `sites/` — `Site` {company (PROTECT), code (unique per company), name_fa,
  name_en, timezone (default `Asia/Tehran`), is_active}
- `departments/`, `site-capabilities/` — unchanged.

Uniqueness is enforced server-side; the UI surfaces the backend's 400 rather
than duplicating the rule.

## Frontend

- `src/api/organization.ts` — `Company` / `Site` types and `createCompany` /
  `createSite` helpers.
- `CompaniesPage` / `SitesPage` — read-only `CollectionView`s (code, name,
  timezone, active). The **New** header action is gated by
  `organization.company.manage` / `organization.site.manage`.
- `CompanyCreatePage` / `SiteCreatePage` — the standard `FormField` create form.
  The site form loads its company `<select>` from
  `/organization/companies/?page_size=100`, defaulting to the first result, and
  exposes an optional timezone input (default `Asia/Tehran`).
- Routes live under `/organization/{companies,sites}` (+ `/new`), each wrapped in
  a `ProtectedRoute` with the matching view/manage permission; two sidebar
  entries are gated by the `.view` permissions.

## Deliberately not built

- No department / capability frontend (no confirmed operational need yet).
- No edit/detail pages — the create + browse slice mirrors the other master
  surfaces; inline edit is a later, uniform decision.
- No cross-company scoping UI beyond the existing per-user data scoping.

## Verification status

IMPLEMENTED + STATICALLY CHECKED. Backend `py_compile` clean; frontend i18n
en/fa parity verified (parity True). Backend test `test_organization.py` and
frontend `organization.test.ts` are IMPLEMENTED, not EXECUTED (sandbox has no
Postgres / npm). Runtime verification deferred to a networked environment.
