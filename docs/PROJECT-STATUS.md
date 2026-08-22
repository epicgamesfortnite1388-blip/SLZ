# SLZ ERP — Project Status: Progress, Milestones & Remaining Work

**Project:** Custom ERP/MES for صنایع لفاف زرین (Zarrin Laff Industries / SLZ) — a
made-to-order flexible-packaging manufacturer, one of six NEPTA-group companies
(phase-1 = SLZ/Tehran + Helena/Saveh).
**Workspace:** `E:\Code\Project\ERP` (backend `erp/backend`, frontend `erp/frontend`).
**Last updated:** 2026-08-22 (sample-product model validation batch).

This document is the single consolidated status view. Requirement *text* lives in
`docs/requirements/requirements-baseline.md`; per-decision history in
`docs/requirements/decision-register.md`; build deltas in
`docs/requirements/requirements-changelog.md`; architecture in
`docs/architecture/`. This file summarizes and points into those.

---

## Status legend

| Status | Meaning |
|---|---|
| **IMPLEMENTED** | Code written and self-consistent. |
| **RUNTIME VERIFIED** | Actually executed: lint suite, migrations generated, backend tests green (SQLite), frontend typecheck/lint/vitest/build green. |
| **BLOCKED** | Cannot proceed without an SLZ business decision (must not be invented). |
| **DEFERRED** | Consciously out of scope for the current phase. |

> **Verification status (2026-08-22, sample-product validation batch).** The codebase is
> **RUNTIME VERIFIED** on a Windows dev machine: flake8/black/isort clean, all
> app migrations generated (`makemigrations --check` → no drift), backend suite
> **247/247 OK**, frontend `tsc --noEmit` + ESLint (0 warnings) + vitest
> **26 files / 88 tests OK** + production build OK. Scope caveat: tests run on SQLite per
> `config.settings.test`; Docker is unavailable, so the PostgreSQL/Redis/Celery
> stack via `docker compose up --build` has not been exercised and remains the
> only unverified deployment path.

---

## Snapshot

- **18 backend apps** implemented (8 foundation + 10 domain). **245 backend tests** (all passing).
- **Frontend:** ~80 page components across all 18 domain areas; **25 test files / 83 tests** (all passing); production build verified.
- **All 15+ confirmed backend entities have list + create + detail (where applicable) frontend surfaces.**
- **All documented API enums have type-checked covering tests** (translation-key guard, permission-code guard, API-contract regression tests).
- **24 architecture documents**, full requirements baseline, decision register, traceability, contradictions, do-not-build-yet lists, execution-preparation map.
- **Phase reached:** the un-gated frontend surface is **substantially complete**. The **execution &
  traceability layer is not started** — it is blocked on business decisions. Multi-tenancy horizontal scoping
  remains single-tenant-open until Q-055 is resolved. All business gated decisions are documented in
  `docs/architecture/execution-preparation.md`.

## Module status matrix

| Module (app) | Built & usable now | Deferred (gated) layer | Gate |
|---|---|---|---|
| **core / identity** | Base models, soft delete, error envelope, event bus, audited viewsets, RBAC, JWT, roles admin UI | — | — |
| **organization** | Company → Site → Department → SiteCapability masters (all with create + list UI) | Cross-company scoping UI | Q-055 |
| **audit** | Append-only trail + searchable viewer + entry detail with before/after diff | Export, tamper-evidence | — |
| **documents** | Generic attachment register + in-context panels on all 10 detail pages | Attachment policy, controlled-doc/e-sign | — |
| **localization** | Jalali/Gregorian, number/calendar utilities, en ↔ fa parity on all pages | — | — |
| **notifications** | In-app inbox + bell | Email / SMS / push channels | DR-008 |
| **workflow** | Generic engine + approvals inbox + definitions admin | Approval hierarchy/threshold **content**, escalation/SLA | Q-054/056, #7 |
| **catalog / partners / hr** | Products, materials, UoM, UoM conversions, product taxonomy (group/type/class/family — list + create), partners + contacts + addresses, employees — full CRUD UI | Product coding scheme | Q-019 |
| **engineering** | Versioned CustomerProduct + SpecificationRevision + detail with revision chain; ToolingAsset detail | Tooling cost model; spec-revision trigger rule; auto usage capture | Q-004/036, Q-024, Q-046 |
| **manufacturing** | WorkCenter/Machine list+create; versioned BOM + Routing + root detail pages | Consumption bases/waste factors; routing templates | Q-027, Q-016/042, Q-029 |
| **inventory** | Warehouse master + access grants + detail | **Stock movements, kardex, lots/rolls, genealogy** | **Q-046**, Q-048/049 |
| **quality** | Characteristic catalogue list+create; versioned QualityPlan list+create + root detail | Check execution, results, NCR/hold, scrap/rework, COA, recall | Q-039/040/043/044, Q-046 |
| **procurement** | PR / PO header+line (list + create with inline lines + detail + attachments + audit) + status transitions | Goods receipt/GRN, MRP, RFQ, thresholds, invoice matching, valuation | #7/#14/#17/#23, Q-034 |
| **sales** | SalesOrder header+line (list + create with inline lines + detail + attachments + audit) + confirm/close/cancel | Pricing/proforma, ATP, allocation, shipment, invoicing, credit | Q-046, #11/#12/#18 |
| **production** | ProductionOrder header (list + create + detail + attachments + audit) + release/complete/close/cancel | Material issue/genealogy, confirmations/scrap/downtime, QC results | **Q-046**, SR-05/06/08 |

---

## Milestone history (chronological)

### Discovery & requirements (no code)

**Task 001 — Business & Domain Discovery** (2026-08-20). Produced 10 documents in
`docs/business-analysis/` covering business processes, manufacturing processes,
the product model, BOM & routing, costing, quality, inventory, and roles.
Captured 22 assumptions (A-001…A-022) and 64 open questions (Q-001…Q-064).

**Task 002 — Business Validation & Requirements Baseline** (2026-08-21). Produced
the bilingual workshop doc `docs/business-review/` and `docs/requirements/`:
78 functional + 24 non-functional requirements (each traced), a 31-entry decision
register (none CONFIRMED), traceability matrix, 8 contradictions, and a 35-item
do-not-build-yet list. Verdict: **ready for platform foundation, not domain
implementation** (business model not yet validated).

**Task 004A — Read & Reconcile Existing SLZ Documentation** (2026-08-21). An
official NEPTA feasibility study was reconciled against our analysis (7 docs in
`docs/reconciliation/`). **Critical finding:** the study recommends *buying*
Microsoft Dynamics 365 F&O — the custom build must be reaffirmed by the business
(NQ-001/DR-000). Also confirmed the multi-company structure (six NEPTA companies;
phase-1 SLZ + Helena, site-specific capability).

### Platform foundation

**Task 003 — Platform Foundation** (2026-08-21). First implementation task. A
modular-monolith foundation (Django 4.2 + DRF + Postgres; Vite + React 18 + TS).
**8 foundation apps, no business logic:** `core`, `identity`, `organization`, `audit`,
`documents`, `localization`, `notifications`, `workflow`.

### Domain modules (confirmed layers only) — Tasks 004–011

Each domain module ships **only the business-confirmed slice** — masters,
versioned definitions, or header/line transactional documents with a
server-authoritative status state machine.

- **Task 004 — Master Data:** partners, product taxonomy, products, materials, UoM, site capabilities, employees.
- **Task 005 — Product Engineering:** versioned `CustomerProduct` + `SpecificationRevision`.
- **Task 005b — Tooling / Cliché Asset (SR-03):** `ToolingAsset` identity + usage-life master.
- **Task 006 — Manufacturing:** `WorkCenter` / `Machine` + versioned `BillOfMaterials` and `Routing`.
- **Task 007 — Inventory Foundation:** `Warehouse` + `WarehouseAccess`.
- **Task 008 — Quality Foundation:** `QualityCharacteristic` + versioned `QualityPlan`.
- **Task 009 — Procurement Foundation:** `PurchaseRequisition` / `PurchaseOrder` header+line + status machine.
- **Task 010 — Sales Order Management:** `SalesOrder` header+line + confirm/close/cancel.
- **Task 011 — Production Order Management:** header-only `ProductionOrder` + release/complete/close/cancel.

### Foundation "make-it-usable" slices (2026-08-21 → 08-22)

UI surfaces for all foundation apps: approvals inbox, notifications inbox, audit log viewer,
organization masters, workflow definitions, documents upload/download, live dashboard
with per-module record counts and order-book status summaries.

### Runtime verification (2026-08-22) — Tasks 012–026

Runtime verification, audit trail snapshots + diff viewer, order-book reporting,
document detail pages + audit history panels, product engineering detail with
revision chain, engineering API foundation, security hardening, silent-action-failure
fix, Jalali date presentation, CI hardening, auth brute-force resistance,
self-profile validation, Q-055 multi-tenancy dependency map, and two QA cycles
(input-fuzz hardening, workflow-decision guard regression).

### Sample-product model validation (2026-08-22)

Validated the two real SLZ product sheets in
`docs/architecture/sample-product-model-validation.md` against the current
CustomerProduct, SpecificationRevision, SpecLayer, SpecColor, SpecParameter,
ToolingAsset, BOM, Routing, material, UoM, quality-plan, attachment, and audit
models. The core definition layer represents both samples without a new backend
schema: product 1 maps to an ordered BOPP/PET/PE laminate-roll specification;
product 2 maps to a single PE, seven-color converting specification.

The safe implementation was frontend-only: the Customer Product detail view now
resolves existing customer/material/UoM references to readable labels and shows
layer tolerances, color alternatives/ΔE, and typed parameter values. No sample
fixture or seed data was created because customer identity, alternate identifier
ownership, coded dimensions, BOM semantics, and production quantities remain
uncertain in the PDFs.

Remaining gaps are semantic rather than safe schema additions: pairwise
lamination, print-reference metadata, layer treatments, converting-feature
vocabulary, packaging hierarchy, and page-level field provenance. Q-019/NQ-005,
Q-024, Q-026, Q-039/Q-040, Q-046/Q-048/Q-049, Q-053/Q-055, and costing gates
remain untouched. See the validation document for field-by-field evidence and
classification.

**Verification for this batch:** backend 247/247 tests green on SQLite;
frontend 26 files / 88 tests green; typecheck, ESLint, production build,
flake8, black, isort, and `makemigrations --check` all passed. Docker is
unavailable, so PostgreSQL/Redis/container verification remains unexecuted.

### Autonomous implementation batch #2 (2026-08-22, afternoon)

**Task 027 — I18n parity repair + orphan page wiring.** The `translationKeys` guard
found 17 missing keys from a concurrent agent's committed-but-incomplete work.
Added all missing `manufacturing.detail.*`, `manufacturing.fields.*`, `masterData.fields.uom`,
and `roles.*` locale keys (en ↔ fa parity). Wired the orphan `BomRootDetailPage`
into App.tsx with a proper `boms/:id` route and fixed the BOM roots list row-click
navigation. Removed unused `useTranslation` import from `RolesPage`. Fixed the
`ProductClass`/`ProductFamily` list pages to display just the code column (was
concatenating UUIDs). Fixed `addressKinds.*` → `kinds.*` i18n prefix mismatch in
`PartnerSubPanels`.

**Task 028 — Inline line-creation on transactional create pages.** Previously the
SalesOrder, PurchaseRequisition, and PurchaseOrder create pages only captured
header data — lines had to be added later. All three now include inline row
editors below the header form: product/material/UoM dropdown selectors, numeric
quantity/price inputs, add/remove row buttons. On submit the header is created first,
then each populated line is POSTed sequentially. Added `common.addLine`,
`procurement.fields.lineNotes`, and `sales.fields.lineNotes` locale keys.

**Task 029 — In-context attachment panels on all detail pages.** Only 5 of 10
detail pages had the permission-gated `AttachmentPanel`. Added it to the
remaining 5: `BomRootDetailPage`, `RoutingRootDetailPage`, `ToolingAssetDetailPage`,
`CustomerProductDetailPage`, and all four transactional document detail pages
(SalesOrder, PurchaseOrder, PurchaseRequisition, ProductionOrder). Fixed React
hooks rules violations in two pages (conditional `useAuth()` call).

**Task 030 — Product taxonomy UI completion.** ProductGroup, ProductType,
ProductClass, and ProductFamily had backend endpoints but no frontend pages.
Added list + create pages for all four taxonomy levels, wired routes under
`/master-data/product-groups` (etc.), and added sidebar navigation links.
Added the missing `product_group` picker to `ProductCreatePage`.

**Task 031 — UoM conversion pages.** Added `UomConversionsPage` (list) and
`UomConversionCreatePage` (create with dual-UoM dropdown selectors + factor input),
wired under `/master-data/uom-conversions/`. Added `uomConversions.*` locale keys
and sidebar link.

**Task 032 — Product detail FK name resolution.** `ProductsDetailPage` previously
showed raw UUIDs for `product_group` and `family`. Added `fetchProductGroup()` and
`fetchProductFamily()` to the API layer; the detail page now resolves these to
human-readable `name_fa || code` on mount. Graceful fallback to raw ID on fetch failure.

**Task 033 — Concurrent-agent integration fixes.** During this batch a concurrent
agent committed multiple files. Repairs made: removed duplicate `BomRootDetailPage`
import, fixed `quality.ts` missing `Paginated` import, removed duplicate
`onRowClick` prop on `QualityPlanRootsPage`, added missing `useAuth` imports on
procurement detail pages.

**Verification after this batch:** backend **245/245**, frontend **25 files / 83 tests**,
migration check clean, flake8/black/isort green, typecheck/lint/build green.

---

## What remains — blocked on SLZ business decisions

Every high-value item left is **BLOCKED** on a decision that must not be invented.
Full list in `docs/requirements/do-not-build-yet.md`; the priority order:

### Priority 1 — the single highest-leverage decision

**Q-046 — Roll serialization vs. lot + count.** Track each produced roll as an
individually serialized unit (unique ID + per-roll genealogy) or as a lot/batch
with a piece count? This determines the **traceability schema** and blocks the
entire execution layer across **five modules**: stock movements & kardex, goods
receipt, material issue, production confirmations & genealogy, QC execution, and
sales allocation/shipment. Answer this and the largest body of remaining
engineering unblocks at once. Decide together with:

- **Q-049** — Traceability granularity (roll / pallet / carton).
- **Q-048** — Material issue method (explicit issue vs. backflush).
- **Q-026** — Inventoried intermediates / real BOM levels.

### Priority 2 — costing & finance

Q-031/033/034 (costing method, rates, material valuation FIFO/WA/lot-actual);
Q-035 (scrap absorption / regrind value); Q-004/036 (tooling cost model —
customer-paid vs. amortized); Q-006/037 (over/under-delivery & invoicing basis);
Q-061 (accounting / GL / AR / AP boundary).

### Priority 3 — quality & BOM rules

Q-039/040 (inspection plans, methods, AQL vs. 100% sampling); Q-043 (rework-vs-
scrap rules & reason codes); Q-027 + Q-016/042 (consumption bases, waste factors,
standard scrap %); Q-003 (first-article/sampling mandatory rules); Q-051
(shelf-life / FEFO enforcement).

### Priority 4 — approvals, roles & coding

Q-054/056 (approval hierarchy & threshold **content** — the engine + admin UI are
built, only the matrix is missing); Q-053/055 (final role catalogue & data-scoping
rules); Q-019 (product coding/numbering scheme); Q-024 (spec-revision trigger rule
& approver).

### Priority 5 — deployment & platform (needed before go-live)

Q-060 (hosting model & data residency — on-prem vs. cloud); Q-058 (authentication
mechanism — local/SSO/AD/kiosk); Q-061 (migration from existing spreadsheets/
tools); **DR-000 is CONFIRMED (custom build)** — the D365 recommendation was considered and rejected.

### Deferred by choice (not blocking, out of scope for early phases)

APS/scheduling optimization (DR-012); IoT/PLC/SCADA integration (Q-062/DR-013);
advanced OEE analytics (Q-017); WhatsApp/SMS/email delivery (DR-008); formal
recall automation (Q-044/DR-035, design traceability to allow it); barcode/QR/RFID
hardware (DR-006).

---

## Runtime verification checklist

**Done 2026-08-22 (Windows dev machine, no Docker):**

```bash
# Backend — all green
cd erp/backend
pip install -r requirements/dev.txt
flake8 apps config && black --check apps config && isort --check-only apps config
python manage.py makemigrations --check --dry-run   # no drift
python manage.py test --settings=config.settings.test --noinput   # 245/245 OK

# Frontend — all green
cd ../frontend
npm ci
npm run typecheck && npm run lint && npm run test && npm run build  # 25 files / 83 tests OK
```

**Still pending (needs Docker on the dev machine / a host):**

```bash
docker compose up --build              # Postgres + Redis + backend + celery + frontend
docker compose exec backend python manage.py migrate      # against real PostgreSQL
docker compose exec backend python manage.py seed_rbac    # loads all seeded permissions
```

Until that last block passes, the deployment stack itself (Postgres schema,
Redis cache/broker, WhiteNoise static serving in-container) remains unverified;
all application logic is verified.

---

## Definitive pre-decision status (2026-08-22)

**CURRENTLY IMPLEMENTED** — platform foundation complete and usable:
identity/RBAC/JWT/throttling, organization masters, audit trail with
snapshots/diff viewer, documents register with in-context attachment panels,
localization incl. Jalali display, notifications, workflow engine with
approvals inbox, all master-data modules (partners w/ contacts+addresses,
catalog incl. UoM conversions, hr), versioned engineering (customer products,
spec revisions, tooling), manufacturing definition (work centers, machines,
BOM/routing roots+revisions), warehouse foundation with access grants,
quality characteristics + versioned plans, procurement requisition/PO with
state machines, sales orders, production orders — each with detail pages,
order-book summaries, roles admin.

**CURRENTLY RUNTIME VERIFIED** — backend suite green on SQLite;
frontend typecheck/lint/vitest/build green; migration drift gate clean; both
enforced in CI. PostgreSQL/Redis/Celery/Docker path remains unexecuted here.

**BUSINESS BLOCKERS** — see `docs/business-decision-package.md`
(workshop-ready): Q-046/Q-048/Q-049/Q-026 execution cluster; Q-055/Q-053
multi-tenancy (CRITICAL security exposure until closed); costing cluster
Q-031/033/034; KPIs Q-038; build-vs-buy DR-000; secondary batch Q-019/024/
027/029/039/040/043/047/051/052/054/060/062.

**INFRASTRUCTURE BLOCKERS** — requires a Docker-capable machine:
`docker compose up --build` then `migrate` + `seed_rbac` inside the backend
container (entrypoint already waits for Postgres and applies committed
migrations). Static audit of Dockerfile/compose/CI found no defects to fix.

**NEXT ENGINEERING ACTION AFTER EACH DECISION:**
- Q-046 answered — inventory movement/lot-roll schema + GRN + issue +
  output + genealogy, following `execution-preparation.md` seams.
- Q-048 answered — consumption posting engine + shop-floor issue UX.
- Q-049 answered — labeling/packing units + recall query depth.
- Q-026 answered — BOM structure finalization + intermediate storage.
- Q-055/Q-053 answered — systematic scoping sweep per
  `multi-tenancy-preparation.md` (read choke point + write assignment +
  generic-surface resolution + cross-company regression tests).
- Q-031/033/034 answered — valuation/costing engine on configurable
  formula seams (already data-only).
- Q-038 answered — KPI views on confirmed dimensions.

---

## Recommended next step

Answer **Q-046** (with Q-048/049/026). That one cluster unblocks more downstream
engineering than everything else combined — the traceability/stock/execution layer
across procurement, inventory, quality, sales, and production. With those four
decisions, autonomous implementation can resume immediately without further input.