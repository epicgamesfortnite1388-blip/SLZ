# SLZ ERP — Takeover State (NEW VPS)

Date: 2026-09-14 · Lead: Buffy (autonomous takeover)
This VPS: `freestyle-vm` — Ubuntu 24.04, 4 vCPU, 7.8 GiB RAM, 32G disk (24G free),
Docker 29.1.3 + Compose 2.40.3, Node 24, Python 3.12. No containers, no other services.

## Repository
- Canonical remote: https://github.com/epicgamesfortnite1388-blip/SLZ
- Working copy: `/home/ubuntu/workspace/erp` (fresh clone — the VPS had no prior copy)
- Branch: `main` @ `69b57c5` (== origin/main), clean tree at takeover
- Previous handoff: `.agent-work/FINAL-STATE.md` (2026-09-03) — claims all re-verified below

## Independent verification (this session, not trusted from handoff)
- Backend: **381 tests OK** (4 PG-only skips) on SQLite `config.settings.test` — 4.9s ✓
- Frontend: typecheck ✓ · eslint (0 warnings) ✓ · **vitest 28 files / 98 tests OK** ✓
- `vite build` ✓ (2.05s; one >500 kB chunk warning — P4 code-splitting candidate)
- flake8 / black / isort ✓ · `makemigrations --check` ✓ (no drift)
- Backend venv: `erp/backend/.venv` (requirements/dev.txt) · frontend: `npm ci` done

## Architecture (confirmed from source)
- Django 4.2 + DRF monolith, 22 apps in `erp/backend/apps/`; React 18 + TS + Vite SPA
  (~111 page components) in `erp/frontend/src`; PostgreSQL/Redis/Celery/nginx via compose.
- Tenancy (Q-055): `AuditedModelViewSet.company_scope_lookup` + fail-closed queryset
  scoping + write guards (`_assert_company_allowed`); superuser bypass; company create
  auto-membership bootstrap. Audited writes via `apps.core.service`.
- RBAC: `HasPermission`, `required_permission` + `permission_map` (GET→view, writes→manage);
  frontend `ProtectedRoute requiredPermission` + route guards; permissions seeded.
- Frontend reference edit flow: `PartnerEditPage.tsx` (PATCH) + route
  `partners/:id/edit` (manage-permission) + "Edit" link on PartnerDetailPage +
  `updatePartner()` API fn. Detail pages of other entities have **no Edit entry**.

## Verified gap (the workstream, from docs/roadmap-gap-matrix.md)
Master-data edit flows exist ONLY for Partner (+ partner role profiles). Backend
serializers already accept PATCH for all master data (permissions already mapped:
PUT/PATCH → `<module>.<resource>.manage`). Missing = frontend-only:
- update API fns: none for product/material/company/site/department/warehouse/
  employee/work-center/machine
- edit pages: none except Partner
- detail-page "Edit" links: none except Partner
- edit-flow PATCH contract tests: none except partner-related flows

## Known limitations (business-blocked, DO NOT invent scope)
- BOM-driven MRP explosion — needs consumption-basis decision (Q-027 etc.)
- Bin/location tracking — Q-047 deferred
- Email/SMS channels — DR-008 deferred
- Users admin is read-only by design (Q-053)
- Detail pages exist for: products, materials, employees, warehouses, work-centers,
  machines, partners. Companies/sites/departments are list+create only (no detail page).

## Conventions (enforced by CI)
- i18n fa/en 100% parity guard — every new t() key needs both locales
- apiPathDrift guard test — new API fns should be covered in src/api/__tests__/
- Migration drift gate; flake8/black/isort; eslint --max-warnings 0
