# SLZ ERP / MES

Custom ERP/MES for **صنایع لفاف زرین** (Zarrin Laff Industries), a made-to-order
flexible-packaging manufacturer (NEPTA group; phase 1 = SLZ/Tehran + Helena/Saveh).

The platform is a modular-monolith **Django 4.2 + DRF backend**, a **React 18 +
TypeScript SPA**, and PostgreSQL/Redis infrastructure orchestrated with Docker
Compose. It ships the full foundation (identity & RBAC, JWT auth, append-only
audit trail with before/after diffs, documents/attachments, bilingual fa/en
with Jalali dates, notifications, generic approval workflow), the **confirmed
domain layers** (master data, product engineering with versioned
specifications, BOM/routing, procurement and sales documents, production
orders, quality plans, warehouses, tooling assets), and the **execution layer**
(stock movements & ledger/kardex, GRN receiving, material issues & production
outputs, dated weighted-average costing, allocations & shipments, genealogy
links, QC results) with multi-company isolation (Q-055).

> Open business decisions that remain deliberately out of scope are listed in
> `docs/PROJECT-STATUS.md` (known limitations) and
> `docs/requirements/do-not-build-yet.md`.

## Repository layout

```
ERP/
├── docs/                     # analysis, requirements, architecture, status
│   ├── PROJECT-STATUS.md     # ← current progress & remaining work (start here)
│   └── architecture/         # how the platform is built
├── skills/                   # domain-knowledge primers for AI agents
└── erp/
    ├── backend/              # Django + DRF monolith (20 apps)
    ├── frontend/             # Vite + React 18 + TypeScript SPA
    ├── infrastructure/       # Dockerfiles, nginx
    ├── scripts/              # container entrypoint
    ├── docker-compose.yml
    └── Makefile              # developer shortcuts
```

## Quick start (Docker)

Requires Docker + Docker Compose.

```bash
cd erp
cp .env.example .env          # adjust values; set a real DJANGO_SECRET_KEY
docker compose up --build
```

The backend entrypoint waits for PostgreSQL, applies the committed migrations,
and seeds platform RBAC (66 permissions + the `platform_admin` role — no
business data). To create the first admin, set `ADMIN_EMAIL` /
`ADMIN_PASSWORD` in `.env` before starting, or run `make createsuperuser`.

Services:

- Backend API — http://localhost:8000/api/v1/
- Health / readiness — http://localhost:8000/health/ , `/ready/`
- Frontend SPA — http://localhost:5173 (dev) or the nginx-served build

Common `make` targets (run from `erp/`): `up`, `down`, `build`, `migrate`,
`seed`, `test`, `lint`, `migrations-check`, `verify`. Run `make help` for all.

## Local development without Docker

A fully self-contained settings profile (`config.settings.local`) runs the API
on SQLite with in-process Celery — no external services at all:

```bash
# Backend (Windows PowerShell; use export on bash)
cd erp/backend
python -m venv .venv && .\.venv\Scripts\Activate.ps1
pip install -r requirements/dev.txt
$env:DJANGO_SETTINGS_MODULE = 'config.settings.local'
python manage.py migrate
python manage.py seed_rbac
python manage.py createsuperuser      # first login
python manage.py runserver

# Frontend (second terminal)
cd erp/frontend
npm ci
npm run dev                           # http://localhost:5173
```

For PostgreSQL-backed local development use
`DJANGO_SETTINGS_MODULE=config.settings.dev` with the services from
`docker compose up postgres redis`.

Sign in with your superuser account; every screen is permission-gated
(`module.resource.action`), so an account without seeded permissions sees
nothing by design.

## Running the tests

The backend test suite runs against a throwaway file-backed SQLite database
with eager Celery — no external services:

```bash
cd erp/backend
python manage.py test --settings=config.settings.test --noinput
```

Frontend:

```bash
cd erp/frontend
npm run test          # vitest
npm run typecheck     # tsc --noEmit
npm run lint          # eslint
npm run build         # production build
```

Or everything CI runs, in one command (host mode):

```bash
cd erp && make verify-local
```

CI (`.github/workflows/ci.yml`) gates every push/PR on: backend flake8 +
black + isort, migration-drift check, full Django suite; frontend typecheck,
ESLint, Vitest, production build.

## Conventions (do not violate)

- UUID primary keys; business numbers are separate fields.
- Soft delete is **opt-in**, not universal.
- Permissions are `module.resource.action`; roles are data, never hard-coded.
- Datetimes are timezone-aware UTC; Jalali is presentation-only.
- Store numbers/money numeric; format at the edge via `localization`.
- Migrations are generated during development and committed; deploys only
  apply them (`makemigrations --check` guards drift in CI).
- The standardized error envelope (`docs/architecture/api-conventions.md`)
  is the only error shape clients ever see.
