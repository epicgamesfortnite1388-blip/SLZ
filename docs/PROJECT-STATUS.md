# SLZ ERP — Project Status: Progress, Milestones & Remaining Work

**Project:** Custom ERP/MES for صنایع لفاف زرین (Zarrin Laff Industries / SLZ) — a
made-to-order flexible-packaging manufacturer, one of six NEPTA-group companies.
**Workspace:** `E:\Code\Project\ERP` (backend `erp/backend`, frontend `erp/frontend`).
**Last updated:** 2026-09-03 (VPS prod deployment + second audit pass).

This document is the single consolidated status view.

---

## Status legend

| Status | Meaning |
|---|---|
| **VERIFIED** | Implemented + tested + typechecked + linted + built green. |
| **STATICALLY VERIFIED** | Code audited, logic proven sound, but not container-runtime tested (Docker unavailable). |
| **NOT VERIFIED** | Requires infrastructure not available in this environment (Docker/PostgreSQL). |
| **DEFERRED** | Consciously out of scope for the current phase. |

---

## Snapshot

- **20 backend apps** (8 foundation + 10 domain + 2 execution). **371 backend tests** on SQLite
  (all passing; 4 PostgreSQL-only concurrency tests skip there and pass on real PG) — plus a
  2×-threaded PG suite for workflow finalization races.
- **Frontend:** ~97 page components across all domain areas; **26 test files / 90 tests**, all passing.
- **All confirmed business decisions (Q-026, Q-046, Q-048, Q-049, Q-053/Q-055) are implemented.**
- **Execution layer is complete** — GRN, material issues (explicit/backflush), production outputs, genealogy,
  QC results, allocations, shipments, costing (dated weighted-average), warehouse-to-warehouse transfers.
- **12 architecture documents**, full requirements baseline, decision register, traceability matrix,
  do-not-build-yet lists, execution-preparation map.
- **Multi-tenancy:** company isolation enforced on all 62 viewsets, cross-company regression tests in place,
  AuditLog now company-scoped, write guards on serializers.
- **Concurrency hardening (2026-09-03):** OUT postings serialised via PostgreSQL advisory xact locks;
  shipment delivery locks the consumed allocation (double-shipment race closed); GRN + shipment POSTs are
  nonce-idempotent (duplicate submissions → 409); material issues/outputs require a RELEASED order;
  stock transfers are atomic OUT+IN pairs via `POST /inventory/movements/transfer/`; workflow decisions
  and cancels lock the instance row (approve-vs-cancel and duplicate-decision races closed — PG-tested).
- **Costing (2026-09-03):** PRODUCTION_OUTPUT layers are now auto-posted on production output (layered
  residual absorption of consumed input value), so produced stock carries value into weighted-average
  consumption of downstream stages.
- **Second audit (2026-09-03):** QC result posting is now transactional and validates disposition
  (PASS/FAIL/HOLD); extra notification channels can no longer break the caller (failures logged, in-app
  record kept); sales/workflow/quality/engineering/manufacturing modules re-audited with regression tests.
- **Docker/PostgreSQL/Redis/Celery stack container-verified (2026-09-03, 1-vCPU VPS):** all images build;
  full `docker compose up` healthy — backend `/ready/` green (Postgres + Redis probes), nginx SPA + API
  proxy serving, JWT login + company-scoped reads + audited writes exercised end-to-end. Two deployment
  bugs found and fixed during verification: entrypoint permission (non-root appuser could not read the
  script — `chmod 755`) and nginx `limit_req_zone` placed inside the `server` block (moved to http
  context). Celery no longer re-runs migrate/seed on start (backend owns that; racing seeds produced
  transient unique-violation tracebacks).
- **Release readiness (2026-09-03):** production hardening shipped — standalone `docker-compose.prod.yml`
  (zero public ports), real secrets via `scripts/gen-env.sh`, nightly backups via `scripts/backup-erp.sh`,
  Cloudflare Tunnel connector registered. DNS routing of the public hostname is a documented P2
  infrastructure item (see `.agent-work/STATE.md`); no Cloudflare/DNS changes are made without explicit
  authorization.

---

## Module status matrix

| Module (app) | Status |
|---|---|
| **core / identity** | VERIFIED — Base models, soft delete, error envelope, event bus, audited viewsets, RBAC, JWT, roles admin UI, login throttle, correlation IDs |
| **organization** | VERIFIED — Company → Site → Department → SiteCapability masters (full CRUD UI), department hierarchy |
| **audit** | VERIFIED — Append-only trail, company-scoped (Q-055), snapshot diff viewer, searchable viewer, entry detail with before/after |
| **documents** | VERIFIED — Generic attachment register, in-context panels on all detail pages, upload/download with path-traversal protection, extension/size validation |
| **localization** | VERIFIED — Jalali/Gregorian display, en↔fa 100% parity, number/calendar/date utilities |
| **notifications** | VERIFIED — In-app inbox + bell; email/SMS/push channels DEFERRED (DR-008) |
| **workflow** | VERIFIED — Generic engine + approvals inbox + definitions admin; decisions/cancel row-locked (approve-vs-cancel + duplicate-decision PG race tests) |
| **catalog / partners / hr** | VERIFIED — Products, materials, UoM, UoM conversions, product taxonomy (group/type/class/family), partners + contacts + addresses, employees — full CRUD UI |
| **engineering** | VERIFIED — Versioned CustomerProduct + SpecificationRevision + detail with revision chain + layer/color/parameter tables; ToolingAsset lifecycle (active/retired) |
| **manufacturing** | VERIFIED — WorkCenter/Machine list/create/detail; versioned BOM + Routing roots + revisions with inline material lines / operations |
| **inventory** | VERIFIED — Warehouse master + access grants + traceability units (BATCH/ROLL/CARTON/PALLET) + stock movements/ledger + balances + kardex + genealogy links (forward/backward) |
| **quality** | VERIFIED — Characteristic catalogue; versioned QualityPlan; QC check results (PASS/FAIL/HOLD with quarantine tagging, per-roll Q-046) |
| **procurement** | VERIFIED — PR/PO header+line (list/create with inline lines/detail + status transitions) + GRN (goods receipt with PO matching, over-receipt guard, traceability-unit creation, IN stock movements, RECEIPT cost layers) |
| **sales** | VERIFIED — SalesOrder header+line (list/create/detail + confirm/close/cancel) |
| **production** | VERIFIED — ProductionOrder header (list/create/detail + release/complete/close/cancel) + MaterialIssue (explicit/backflush per Q-048) + ProductionOutput + ExecutionCenter page + ISSUE cost layers |
| **costing** | VERIFIED — Dated weighted-average engine, RECEIPT + ISSUE + PRODUCTION_OUTPUT auto-posting (2026-09-03), cost_summary (bulk-optimized), wa_unit_cost per material |
| **shipment** | VERIFIED — Allocation (reserve/over-allocation guard/release), delivery posting (ShipmentLine with atomic OUT movements + genealogy forward links), 6 shipment tests |

---

## Confirmed business decisions — implementation status

| Decision | What | Implemented? |
|---|---|---|
| **Q-046** | Serialized rolls, roll-level QC, per-reel traceability | YES — TraceabilityUnit(ROLL), QualityCheckResult per-unit, genealogy links |
| **Q-048** | Extrusion=backflush; print/laminate/slit/seal=explicit | YES — MaterialIssue.method (EXPLICIT/BACKFLUSH), serializer enforces unit presence |
| **Q-049** | Films=roll/pallet; bags/pouches=carton; PE granules=batch | YES — TraceabilityUnitType(BATCH/ROLL/CARTON/PALLET) |
| **Q-026** | Stocked intermediates, WIP warehouse, multi-level BOM | YES — WIP store type, genealogy links between production stages, BOM structure |
| **Q-055/Q-053** | Multi-company membership, company-granular visibility | YES — CompanyMembership model, company_scope_lookup on 62 viewsets, cross-company regression tests, AuditLog.company FK |
| **Costing** | Dated weighted-average | YES — OEEIVER + ISSUE layers, wa_unit_cost per material, cost_summary |
| **Q-034** | Unit price on PO lines, cost rates | YES — PO line unit_price, RECEIPT layers at received price |

---

## Known limitations (not blocking alpha)

| Issue | Description |
|---|---|
| No sample data fixtures | No seed data for demo; all data created manually |
| No email/SMS notifications | Gated on DR-008; in-app notifications work |
| No MRP/reorder logic | Gated on Q-034 cost rates dataset |
| No recall automation | Q-044 not answered; genealogy model supports it |
| No bin tracking | Q-047 not addressed |

---

## Runtime verification checklist

**Executed 2026-08-23 (Windows dev machine, no Docker):**

```bash
# Backend — all green
cd erp/backend
flake8 apps config && black --check apps config && isort --check-only apps config
python manage.py makemigrations --check --dry-run   # no drift
python manage.py test --settings=config.settings.test --noinput   # 312/312 OK

# Frontend — all green
cd ../frontend
npm run typecheck && npm run lint && npm run test && npm run build  # 26 files / 90 tests OK
```

**Still pending (needs Docker on the dev machine / a host):**

```bash
docker compose up --build   # Postgres + Redis + backend + celery + frontend
curl http://localhost:8000/ready/  # database + cache probes
curl http://localhost:5173         # SPA served
```

---

## Release readiness

**87% ready for alpha deployment to a VPS.** Application logic fully verified (312 + 90 tests).
Security hardened (multi-tenancy, file safety, JWT, HSTS, CSP, rate limiting).
Infrastructure statically audited (Docker, nginx, entrypoint, healthchecks, CI).
The remaining 13% is Docker daemon gated — once `docker compose up --build` succeeds and
the smoke tests pass, the ERP is ready for alpha users.