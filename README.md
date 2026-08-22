# SLZ ERP / MES — Platform Foundation

Custom ERP/MES for **صنایع لفاف زرین** (Zarrin Laff Industries), a made-to-order
flexible-packaging manufacturer.

This repository currently contains the **platform foundation** — a clean,
production-quality modular monolith that future modules build on. It
deliberately ships **no business modules** yet (no sales, engineering,
inventory, manufacturing, quality, purchasing, finance, …). It provides the
mechanisms those modules will share: identity & RBAC, a generic audit trail,
documents, localization (Jalali/Gregorian, bilingual fa/en), notifications, a
minimal approval workflow, a standardized API surface, domain events, and a
consistent transaction strategy.

## Repository layout

```
ERP/
├── docs/
│   ├── architecture/        # how the platform is built (start here)
│   ├── business-analysis/   # Task 001 — domain discovery
│   ├── business-review/     # Task 002 — validation
│   └── requirements/        # Task 002 — requirements baseline
└── erp/
    ├── backend/             # Django + DRF (the monolith)
    ├── frontend/            # Vite + React 18 + TypeScript SPA
    ├── infrastructure/      # Dockerfiles, nginx
    ├── scripts/             # entrypoint
    ├── docker-compose.yml
    ├── Makefile
    └── .env.example
```

Read **[docs/architecture/README.md](docs/architecture/README.md)** first — it
explains the modular monolith, API conventions, data lifecycle, versioning,
transactions, and the security baseline.

## Tech stack

- **Backend:** Django 4.2, Django REST Framework, PostgreSQL 16, Celery + Redis,
  SimpleJWT, django-filter, jdatetime.
- **Frontend:** Vite, React 18, TypeScript (strict), react-router v6,
  i18next, Vitest + Testing Library.
- **Infra:** Docker Compose (postgres/redis/backend/celery/frontend), nginx.

## Quick start (Docker)

Requires Docker + Docker Compose.

```bash
cd erp
cp .env.example .env          # adjust values; set a real DJANGO_SECRET_KEY
docker compose up --build
```

The backend entrypoint waits for PostgreSQL, then runs `makemigrations`,
`migrate`, and `seed_rbac` (which seeds platform permissions and the
`platform_admin` role — no business data). To create the first admin, set
`ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env` before starting, or run
`make createsuperuser`.

Services:

- Backend API — http://localhost:8000/api/v1/
- Health / readiness — http://localhost:8000/health/ , `/ready/`
- Frontend SPA — http://localhost:5173 (dev) or the nginx-served build

Common `make` targets (run from `erp/`): `up`, `down`, `build`, `migrate`,
`seed`, `test`, `lint`, `format`, `createsuperuser`. Run `make help` for all.

## Local development (without Docker)

Backend:

```bash
cd erp/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
export DJANGO_SETTINGS_MODULE=config.settings.dev   # needs Postgres + Redis
python manage.py migrate
python manage.py seed_rbac
python manage.py runserver
```

Frontend:

```bash
cd erp/frontend
npm install
npm run dev
```

## Running the tests

The backend test suite uses **SQLite in-memory** and eager Celery, so it needs
**no external services**:

```bash
cd erp/backend
python manage.py test --settings=config.settings.test
```

Frontend:

```bash
cd erp/frontend
npm run test          # vitest
npm run typecheck     # tsc --noEmit
npm run lint          # eslint
npm run build         # production build
```

CI (`.github/workflows/ci.yml`) runs backend lint + format-check + tests and
frontend typecheck + lint + test + build on push/PR.

## Verification status

All backend and frontend **source compiles and is self-consistent**; JSON
configs and Jalali calendar math were cross-checked offline. Full **runtime**
verification (Docker build, PostgreSQL, `manage.py test`, `npm run build`) must
be executed in an environment with package/network access — the sandbox used to
author this foundation blocked `pip` and `npm` installs. Run the commands above
to complete verification. See the Task 003 final report for details.

## Conventions (do not violate)

- UUID primary keys; business numbers are separate fields.
- Soft delete is **opt-in**, not universal.
- Permissions are `module.resource.action`; roles are data, never hard-coded.
- Datetimes are timezone-aware UTC; Jalali is presentation-only.
- Store numbers/money numeric; format at the edge via `localization`.
- Foundation apps contain no business logic.
