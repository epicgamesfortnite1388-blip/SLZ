# SLZ ERP — Execution State

## Architecture (verified from source, 2026-09-03)
- **Backend**: Django 4.2.16 + DRF 3.15.2, 20 apps under `erp/backend/apps/`, modular monolith.
- **Frontend**: React 18 + TS + Vite 5, `erp/frontend/src`, react-router 6, i18next fa/en, ~97 pages.
- **DB**: PostgreSQL (prod/dev) / SQLite (test settings). **Cache/queue**: Redis + Celery 5.
- **Auth/RBAC**: SimpleJWT (60 min access / 7 d refresh, blacklist on logout); `HasPermission` + `required_permission`/`permission_map`; 66 permission codes seeded by `seed_rbac`; superuser bypass; `allow_any_authenticated` opt-in else fail closed.
- **Tenancy (Q-055)**: `X-SLZ-Company` header validated by `CompanyContextMiddleware` → `request.company_id`; `AuditedModelViewSet.company_scope_lookup` scopes querysets + write guards; non-members ⇒ fail closed. Attachment register resolves owning company via `documents/entity_scoping.py`.
- **Execution layer**: inventory ledger (append-only StockMovement, derived balances/kardex), GRN service (atomic + PO-line locks + over-receipt guard), production material issues/outputs (nonce-idempotent), costing (dated WA layers, best-effort integration), shipment allocation/delivery, genealogy links.
- **Observability**: correlation-id middleware (thread-local), JSON error envelope (no tracebacks), audit event bus with on-commit publish.
- **Infra**: docker-compose (postgres:16, redis:7, backend python:3.11 gunicorn x3 + celery, frontend nginx SPA + API proxy, rate limits, security headers). Entrypoint waits for DB, migrates, seeds RBAC (strict mode env-gated).

## Host facts
- 1 vCPU, 3.8 GiB RAM, no swap, ~9.8G disk (was ~3.1G free at start; ~1.4G free now with images).
- Docker daemon present and usable (daemon not verified before this session — now building images).
- Subagent gateway (api.aeramc.su) OUT OF CREDITS (403 quota exhausted; one model 503) → audits executed by lead agent; one successful business-logic audit report saved.

## Verification baselines
- Backend at start: 342 tests OK (SQLite, config.settings.test). After fixes: **357 OK**.
- Frontend: 26 files / 90 tests OK; typecheck, eslint, vite build all pass.
- flake8/black/isort clean after fixes (fixed 1 pre-existing F401 in identity/views.py).
- Migrations: `makemigrations --check` clean; added 2 new migrations (GRN nonce, Shipment nonce).
- Docker: `erp-backend` image builds; `erp-frontend` build in progress.

## Fixes implemented (see DECISIONS.md)
F1 advisory lock on OUT postings · F2 shipment allocation row lock · F3 transfer_stock service + API, raw TRANSFER rejected · F4 nonce idempotency GRN + Shipment · F5 RELEASED-order guard on issues/outputs · F6 sidebar collapsed-width layout bug + mobile drawer a11y. +15 regression tests.
## Session 3 (2026-09-03, hardening + audit continuation)
- Prod stack verified on VPS via docker-compose.prod.yml (zero public ports; nginx 127.0.0.1:80).
- Secrets rotated (gen-env.sh); postgres role password rotated. Backups scripted (backup-erp.sh).
- Dedicated slz-erp CF tunnel created + connector running; DNS routing NOT applied.

### P2 / Infrastructure (documented, NOT to be acted on without authorization)
slz.abystral.kdns.fr currently bypasses the Cloudflare tunnel: DNS is hosted at OVH
(kdns.fr NS = OVH) and the record is A -> 91.186.216.75 direct. HTTPS hits the VPN's
xray on :443. Do NOT alter DNS/Cloudflare config without explicit user authorization.
