# SLZ ERP — Final Test-VPS Audit Report

**Date:** 2026-09-03 (final handoff pass)
**Host:** `abyss.aeza.network` (1 vCPU / 3.8 GiB RAM / 9.8 GB disk, Ubuntu, no swap)
**Repository:** `main` @ `408f368` (this report covers the audit cycle ending with
commit `408f368`; a follow-up lint fix is committed on top — see *Tests* and
*Repository state*).

This is the single authoritative record of the engineering audit, the fixes
applied, the verification results, and the known remaining work. Supporting
detail lives in:
- `docs/PROJECT-STATUS.md` — consolidated project status (kept current)
- `docs/roadmap-gap-matrix.md` — detailed feature-level gap matrix + roadmap
- `docs/VPS-DEPLOYMENT-HANDOFF.md` — deployment topology + ops runbook
- `.agent-work/DECISIONS.md` — root-cause analysis per fix
- `.agent-work/MASTER-TASKS.md`, `.agent-work/STATE.md`, `.agent-work/stage3/` — working notes

---

## Executive Summary

The audit cycle (2026-09-03, sessions 2–3) hardened the ERP's execution layer,
closed two P0 concurrency races, made posting idempotent, added company-scoped
planning (reorder policies + read-only replenishment engine) and recall
(traceability exposure) modules, verified the full stack on the production VPS,
and re-verified every CI gate in a final pass. The application is deployed and
healthy (`/ready/` → database ok, cache ok); new endpoints fail closed (401)
without authentication.

**Final verification numbers (re-run on the VPS during this handoff):**

```
Backend:        PASS — 381 tests, OK (4 PostgreSQL-only skipped)   (9.5 s, SQLite)
Frontend:       PASS — 28 files / 98 tests OK (vitest)
TypeScript:     PASS — tsc --noEmit, 0 errors
Lint:           PASS — eslint --max-warnings 0; flake8 clean; black clean; isort clean
Build:          PASS — vite production build green (5.8 s); docker images built
Migration check:PASS — makemigrations --check: no changes detected
Live API smoke: PASS — /health/ + /ready/ OK; planning/recall endpoints 401 unauthenticated
Browser smoke:  NOT TESTED — no browser/Playwright on the host (see Known Limitations)
```

One new defect was found and fixed **during this handoff**: the CI gate would
have failed on the next push because `apps/quality/tests/test_quality.py` had
an isort import-order violation (imports introduced by the session-3 quality
hardening were not isort-clean). Fixed in the follow-up commit; `isort
--check-only apps config` now passes.

---

## Bugs Found

### P0 — Concurrency races (both closed, PostgreSQL-tested)

**Bug 1 — Negative stock via parallel OUT postings**
- **Area:** inventory (`apps/inventory/services.py`, `post_movement`)
- **Problem:** two parallel OUT movements on the same (company, warehouse,
  material|unit) could both pass the on-hand guard and drive stock negative.
  Balances are derived, so there was no row to lock.
- **Root cause:** check-then-insert without any serialization between the
  guard read and the movement insert.
- **Fix (F1):** `apps/core/transactions.postgres_advisory_xact_lock(*parts)` —
  `pg_advisory_xact_lock` on a sha256 key inside the atomic block, taken for
  OUT before the guard (no-op on SQLite).
- **Files changed:** `apps/core/transactions.py`, `apps/inventory/services.py`
- **Verification:** regression tests in `test_ledger.py`; two-thread
  PostgreSQL test exercising the race directly.

**Bug 2 — Double shipment of one allocation**
- **Area:** shipment (`apps/shipment/services.py`, `create_shipment`)
- **Problem:** two concurrent shipments of the same RESERVED allocation both
  passed the status check and shipped it twice.
- **Root cause:** allocation status read → SHIPPED write was not atomic.
- **Fix (F2):** `Allocation.objects.select_for_update().get(...)` before the
  status check (the allocation row is the natural serialization point).
- **Files changed:** `apps/shipment/services.py`
- **Verification:** `DeliveryTests.test_shipped_allocation_cannot_be_reused`
  (+ OUT movement count assert).

### P1 — Idempotency

**Bug 3 — Duplicate GRN / delivery submissions double-posted**
- **Area:** procurement GRN, shipment delivery
- **Problem:** network retries re-submitted the same GRN or shipment → double
  stock posting.
- **Root cause:** nonce protection existed only on production postings.
- **Fix (F4):** mirror the `MaterialIssue` pattern — `nonce` UUID with a
  partial unique constraint on `GoodsReceipt` and `Shipment`; create
  serializers accept it; `IntegrityError` → 409 `duplicate_request`; new
  migrations `0003` in procurement and shipment apps.
- **Verification:** duplicate-nonce → 409 API tests for both flows.

### P2 — Business rules & consistency

**Bug 4 — Raw TRANSFER movements were inconsistent**
- **Area:** inventory ledger
- **Problem:** API accepted `direction=TRANSFER` with no real transfer flow;
  derived balances ignored TRANSFER while kardex counted it → derived views
  disagreed.
- **Fix (F3):** reject TRANSFER in `post_movement`; add `transfer_stock()`
  (atomic OUT@source + IN@dest with guards) and
  `POST /inventory/movements/transfer/` + `TransferMovementSerializer`.
- **Verification:** 4 service tests + 3 API tests (incl. cross-company and
  raw-TRANSFER rejection).

**Bug 5 — Issues/outputs allowed on non-RELEASED orders**
- **Area:** production services
- **Problem:** `create_material_issue` / `create_production_output` did not
  check order status at the service layer (serializers partially did).
- **Fix (F5):** `_assert_order_released` in both services (defense-in-depth).
- **Verification:** draft-order issue/output rejection tests (API 400 +
  service `ConflictError`).

**Bug 6 — Workflow approve-vs-cancel + duplicate-decision races**
- **Area:** workflow (`record_decision`, `cancel_workflow`)
- **Fix (session 3):** lock the instance row (`select_for_update`) before
  decision/cancel; terminal-state guard.
- **Verification:** two-thread PostgreSQL tests pass.

**Bug 7 — QC result posting not atomic; disposition not validated**
- **Area:** quality (`post_check_result`)
- **Fix (session 3):** `@transaction.atomic`; explicit disposition validation
  (PASS/FAIL/HOLD); 4 regression tests.

**Bug 8 — Sidebar collapse did not expand content; mobile drawer dead**
- **Area:** frontend shell
- **Problem:** collapsed width was hard-coded while the main-content offset
  stayed fixed; on mobile the drawer lived inside a `display:none` wrapper.
- **Fix (F6):** scope `--sidebar-width` to `.app-shell` with a
  `:has(.sidebar--collapsed)` override; make the sidebar wrapper the fixed
  drawer host; drawer close button, Escape-to-close, `aria-expanded`/
  `aria-controls`, body scroll lock, focus management, nav landmark + i18n
  keys (en/fa).

### Infrastructure bugs (found during container verification)

| Bug | Fix |
|---|---|
| Entrypoint unreadable by non-root `appuser` (deploy crash) | `chmod 755` entrypoint in image |
| nginx `limit_req_zone` inside `server` block (config error) | moved to `http` context |
| Celery re-ran migrate/seed on start → transient unique-violation races | backend alone owns migrate/seed; celery no longer runs them |

### N+1 queries

- **Bug:** shipment and GRN list endpoints issued N+1 queries (per-row
  partner/product lookups).
- **Fix (3cae441):** `select_related`/`prefetch_related` on the affected
  serializers/querysets.

### Found during final handoff (this report)

**Bug 9 — CI lint gate would fail: isort violation in quality test file**
- **Area:** `apps/quality/tests/test_quality.py`
- **Problem:** import order introduced by the session-3 quality changes was
  not isort-clean (`apps.inventory.models` misplaced; `from apps.quality
  import services` before the `apps.quality.models` block).
- **Fix:** isort applied to the single file; `isort --check-only apps config`
  now passes.
- **Verification:** full re-run of the gate below.

---

## Security Findings

- **Authentication:** JWT (SimpleJWT) with access/refresh, refresh
  blacklisted on logout, login throttle (default 30/min/IP). No open findings.
- **Authorization/RBAC:** `HasPermission` + `required_permission` /
  `permission_map`; superuser bypass; `allow_any_authenticated` opt-in,
  otherwise fail closed. New planning/recall endpoints verified 401
  unauthenticated through the nginx proxy.
- **Company isolation (Q-055):** `X-SLZ-Company` header validated by
  `CompanyContextMiddleware`; `AuditedModelViewSet.company_scope_lookup`
  scopes querysets + write guards on all 22 apps' viewsets; non-members fail
  closed; cross-company regression tests in place. Audit log company-scoped.
- **IDOR:** object-level access goes through company scoping; the attachment
  register resolves the owning company via `documents/entity_scoping.py`
  (the earlier P0 — unscoped attachment list/download — is fixed and
  regression-tested; 8 tests).
- **Attachments:** extension allowlist + size cap (`DOCUMENTS_ALLOWED_*`),
  path-traversal protection on download.
- **API security:** standardized JSON error envelope (no tracebacks),
  correlation-id logging, HSTS/CSP/security headers via nginx, rate limits
  (fixed zone context bug above), zero public ports on the host (tunnel-only
  ingress), admin panel not proxied.
- **Secrets:** `erp/.env` never committed (gitignored; 600 perms); secrets
  rotated this cycle (`scripts/gen-env.sh --force` + postgres role password
  rotation); `agent/.keys.json` gitignored.
- **Open:** upload virus scanning deferred (documented gap); Q-055 real-org
  membership provisioning is IT-administered.

No open P0/P1 security findings.

---

## Business Logic Findings

- **Costing (2026-09-03):** PRODUCTION_OUTPUT layers are auto-posted on
  production output — produced stock now carries value into downstream
  weighted-average consumption (was a known gap). RECEIPT + ISSUE +
  PRODUCTION_OUTPUT all auto-posted; `cost_summary` bulk-optimized.
- **Inventory ledger:** append-only `StockMovement`, derived balances,
  quarantine cannot be issued, OUT guarded (advisory-locked), transfers
  atomic OUT+IN pairs.
- **Procurement:** GRN over-receipt guard (PO-line locked), traceability-unit
  creation, RECEIPT cost layers at received price, nonce idempotency.
- **Production:** RELEASED-only issues/outputs, explicit/backflush methods
  (Q-048), nonce idempotency, genealogy links.
- **Shipment:** reserve with over-allocation guard, delivery row-locked,
  atomic OUT + forward genealogy, nonce idempotency.
- **Quality:** transactional result posting, disposition validation, HOLD →
  quarantine tagging, per-roll QC (Q-046).
- **Workflow:** generic engine; approve/cancel row-locked; duplicate-decision
  guard.
- **Planning (Task 014):** company-scoped reorder policies (purchased
  Material XOR manufactured CustomerProduct per warehouse — conditional unique
  constraints + serializer XOR enforcement); read-only deterministic engine
  (on-hand + open supply − reservations − confirmed demand → order-up-to
  suggestions); never creates documents.
- **Recall (Task 015):** company-scoped recalls, locked status machine
  (DRAFT→OPEN→INVESTIGATING/ACTION_REQUIRED→CLOSED/CANCELLED) under
  `select_for_update`, bounded/cycle-safe read-only exposure over the
  genealogy ledger (upstream lots, downstream units, producing orders,
  affected shipments/customers). Never mutates stock.
- **Notifications:** provider failures logged and isolated — a broken channel
  can no longer break the caller; in-app record always kept.

No open business-logic defects found in the audited modules
(inventory/procurement/costing/shipment/production/quality/workflow/
notifications/sales/engineering/manufacturing).

---

## UI Findings

- **Sidebar:** collapsed state now expands content (single source of truth for
  shell width); mobile drawer reachable, closable (button + Escape), scroll
  locked, focus-managed, `aria-expanded`/`aria-controls`, nav landmark label.
- **Navigation:** nav ↔ route coverage cross-checked — every sidebar entry
  resolves; new planning/recall routes registered with sidebar entries.
- **Forms/tables:** inline-line editors, StatusBadge across status surfaces,
  ConfirmButton on destructive transitions, deterministic back links, sticky
  table headers, structured empty states.
- **i18n/RTL:** fa/en 100% parity (drift-guard test); Vazirmatn webfont; RTL
  layout verified at the CSS level.
- **Company context:** all mounted data refetches when the active company
  changes (dashboard tiles, order-book rows, record/detail hooks) — fixed
  stale-context display bug.
- **Loading/error/empty states:** structured across pages; standardized error
  envelope surfaces cleanly (405 MethodNotAllowed mapped to a domain error).
- **Not tested in a real browser** (no browser on host) — see Known
  Limitations.

---

## Infrastructure Findings

- **VPS constraints:** 1 vCPU, 3.8 GiB RAM, **no swap**, 9.8 GB disk at
  ~92% (≈840 MB free after build + prune). Within the operating envelope but
  tight; the swap-less 1-vCPU box is the deployment ceiling for now.
- **Docker:** 5 services healthy (`docker ps`): postgres:16-alpine, redis:
  7-alpine, erp-backend (healthy), erp-celery, erp-frontend (nginx). Prod
  compose publishes nothing publicly; nginx binds 127.0.0.1:80 only.
- **Database:** PostgreSQL in a named volume; `pg_isready` healthcheck
  green; migrations applied incl. planning.0001 + recall.0001; no drift.
- **Redis:** containerized (3 logical DBs: broker/results/cache); the process
  seen on the host (`*:6379`) is the *container's* redis, not a stray host
  service.
- **Celery:** worker up, idle-safe; no longer races migrate/seed with the
  backend.
- **nginx:** SPA + `/api` proxy; HTTP→HTTPS redirect with
  `X-Forwarded-Proto` preserved from cloudflared (redirect-loop fix);
  `limit_req_zone` in http context.
- **Secrets & config:** `scripts/gen-env.sh` (real random secrets, 600);
  secrets rotated this cycle; `docker-compose.prod.yml` standalone (never
  overlaid on the dev file).
- **Backups:** `scripts/backup-erp.sh` exists (pg_dump via compose exec,
  media archive, SHA256, 30-day retention, optional off-box rsync,
  `--install-cron` for nightly 03:15). **Not yet scheduled/restore-drilled
  on the VPS** — see Roadmap P1.
- **Tunnel:** `cloudflared-slz` connector registered and running; public DNS
  routing intentionally **not** applied (external authorization required) —
  see Roadmap P1 and `.agent-work/STATE.md`.

---

## Tests — exact verified results (2026-09-03, final pass)

| Gate | Result |
|---|---|
| Backend suite (`manage.py test --settings=config.settings.test`) | **PASS — 381 tests, OK (4 PG-only skipped), 9.5 s** |
| flake8 (apps config) | PASS |
| black --check (apps config) | PASS (255 files unchanged) |
| isort --check-only (apps config) | PASS (after Bug 9 fix) |
| Migration drift (`makemigrations --check --dry-run`) | PASS — no changes detected |
| Frontend typecheck (`tsc --noEmit`) | PASS |
| Frontend lint (`eslint . --max-warnings 0`) | PASS |
| Frontend vitest | **PASS — 28 files / 98 tests OK** |
| Frontend production build (`vite build`) | PASS (5.8 s; 572 kB bundle — chunk-split warning only) |
| Docker images (`docker build` backend/celery/frontend) | PASS (final-build log 18:52) |
| Live health (`/health/`, `/ready/`) | PASS — `{"status":"ok"}`, `{"checks":{"database":"ok","cache":"ok"}}` |
| Live auth gate (planning/recall endpoints) | PASS — 401 unauthenticated through nginx |
| PostgreSQL concurrency suites (2-thread) | PASS — run on VPS against real PG earlier this cycle |
| Browser E2E | **NOT TESTED** — no browser/Playwright on the host; HTTP/API-level verification used instead |

---

## Known Limitations

- **No browser on the VPS** — no real-viewport/E2E; UI verified via static
  analysis, unit/behavior tests, and live HTTP checks.
- **Subagent gateway out of credits (api.aeramc.su 403/503)** — deeper
  multi-model audits unavailable this cycle; audits performed by the lead
  agent (one successful business-logic subagent report retained in
  `.agent-work/reports/`).
- **Disk 92% / no swap** — headroom is the main operational risk on this box.
- **Bin/location tracking (Q-047)** deferred with justification (derived
  balance layer would need a new dimension + backfill on every movement path).
- **Email/SMS/push notifications** gated on DR-008; in-app works.
- **BOM-exploded MRP demand** needs the consumption-basis dataset
  (business-open Q-027).
- **Upload virus scanning** deferred (extension/size allowlist in place).
- **Backups scripted but restore not drill-tested; cron not yet installed.**
- **Public DNS routing of `slz.abystral.kdns.fr`** deliberately not applied
  (no Cloudflare/DNS changes without explicit authorization).

---

## Remaining Roadmap

Ground truth: `docs/roadmap-gap-matrix.md` (full gap matrix) and
`docs/requirements/do-not-build-yet.md` (business-blocked items). This is the
prioritized extract; nothing below is marked done unless verified.

### P0 — Security / data-loss / outage
- **None open in code.** The concurrency, idempotency, and scoping work above
  closed the last known P0s.

### P1 — Core ERP functionality
1. **Authorize public DNS routing** for `slz.abystral.kdns.fr` through the
   Cloudflare tunnel so alpha users can actually reach the app.
   - Area: infra · Why: the system is deployed but not reachable by users ·
   - Impl: point DNS at Cloudflare (CNAME/custom hostname), verify edge TLS →
     connector → nginx · Deps: explicit user authorization · Priority: P1.
2. **Schedule backups + restore drill.**
   - Area: ops · `backup-erp.sh --install-cron`, quarterly test restore,
     off-box target · Priority: P1.
3. **Replicate the master-data edit flow** to remaining entities (products,
   materials, companies, sites, employees, work centers, machines,
   warehouses) using `PartnerEditPage` as the pattern (+ PATCH contract test
   each). Largest remaining unblocked UI workstream.
   - Area: UI/master data · Priority: P1.
4. **Upload virus scanning**.
   - Area: security · Priority: P1 (deferred gap).

### P2 — Major usability / operational improvements
5. **BOM-exploded MRP demand** in the planning engine — requires the
   consumption-basis dataset (Q-027, business-open; planning foundation is
   shipped).
6. **Bin/location tracking** (Q-047) — deferred with justification; revisit
   with a migration plan.
7. **Email/SMS/push channels** (DR-008 gate; in-app + provider isolation done).
8. **Frontend bundle code-splitting** (572 kB single chunk → route-level
   dynamic imports).
9. **Q-055 real-org membership provisioning** (IT-administered) + role
   assignment matrix UI.

### P3 — Enhancements
10. "Load demo data" UI button wired to `seed_demo_data` (exists, guarded).
11. Detail/edit polish for small master entities flagged in the gap matrix.
12. Exports polish (reuse module view permission; read-only).

### Future — larger capabilities (all gated by business decisions)
- Accounting/GL/AR/AP (Q-061), production scheduling/APS (DR-012),
  machine/IoT/PLC integration (Q-062), advanced OEE (Q-017), customer
  portal, mobile app, barcode/QR/RFID (DR-006/Q-049), AI/ML features
  (not requested), formal recall automation (Q-044 — the exposure engine is
  shipped, workflow gated).

---

## Repository state (this report)

```
Branch:            main
Commit (code):     408f368  — feat: planning + recall modules (remote == local)
Follow-up commit:  lint fix for isort violation in quality test file (this pass)
Remote:            origin  — https://github.com/epicgamesfortnite1388-blip/SLZ.git
Working tree:      clean after this pass's commit + push
```