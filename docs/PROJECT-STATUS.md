# SLZ ERP — Project Status: Progress, Milestones & Remaining Work

**Project:** Custom ERP/MES for صنایع لفاف زرین (Zarrin Laff Industries / SLZ) — a
made-to-order flexible-packaging manufacturer, one of six NEPTA-group companies
(phase-1 = SLZ/Tehran + Helena/Saveh).
**Workspace:** `E:\Code\Project\ERP` (backend `erp/backend`, frontend `erp/frontend`).
**Last updated:** 2026-08-22.

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
| **STATICALLY CHECKED** | `py_compile`/`compileall` clean + JSON/i18n parity verified in the authoring sandbox. |
| **RUNTIME VERIFIED** | Actually executed: lint suite, migrations generated, backend tests green (SQLite), frontend typecheck/lint/vitest/build green. |
| **BLOCKED** | Cannot proceed without an SLZ business decision (must not be invented). |
| **DEFERRED** | Consciously out of scope for the current phase. |

> **Verification status (2026-08-22, Task 023).** The codebase is now
> **RUNTIME VERIFIED** on a Windows dev machine: flake8/black/isort clean, all
> app migrations generated (`makemigrations --check` → no drift), backend suite
> **245/245 OK**, frontend `tsc --noEmit` + ESLint (0 warnings) + vitest
> **75/75 OK** + production build OK. Scope caveat: tests run on SQLite per
> `config.settings.test`; the PostgreSQL/Redis/Celery stack via
> `docker compose up --build` has **not** been exercised yet (no Docker on this
> machine) and remains the only unverified deployment path.

---

## Snapshot

- **18 backend apps** implemented (8 foundation + 10 domain), **30+ test modules**
  (**245 tests** at last count — suite kept green through concurrent additions).
- **Frontend:** 18 domain page areas + login/dashboard/error pages; 16 API layers;
  **23 test files / 75 tests** (all passing); production build verified.
- **23 architecture documents** + full requirements baseline, decision register,
  traceability, contradictions, and do-not-build-yet lists.
- **Phase reached:** platform foundation + confirmed master-data / document /
  definition layers across all modules are complete. The **execution &
  traceability layer is not started** — it is blocked on business decisions.

<!-- APPEND-MILESTONES -->

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
**8 foundation apps, no business logic:** `core` (UUID PKs, `BaseModel`, opt-in
soft delete, standardized error envelope, in-process domain-event bus,
`AuditedModelViewSet`, `atomic_with_events`), `identity` (RBAC
`module.resource.action`, JWT, `HasPermission`), `organization`, `audit`
(event-driven append-only trail), `documents`, `localization` (Jalali/Gregorian
via jdatetime, UTC canonical), `notifications`, `workflow` (generic approval
engine). Reusable `VersionedRoot`/`Revision` pattern shipped but unused by any
business model. **Status: IMPLEMENTED + STATICALLY CHECKED.**

### Domain modules (confirmed layers only)

Each domain module below ships **only the business-confirmed slice** — masters,
versioned definitions, or header/line transactional documents with a
server-authoritative status state machine. The **execution/traceability layer of
each is deliberately deferred behind Q-046 and related gates.**

- **Task 004 — Master Data:** partners, product taxonomy + thin product,
  materials, units of measure, site capabilities, minimal employee. (`catalog`,
  `partners`, `hr` apps.)
- **Task 005 — Product Engineering:** versioned `CustomerProduct` root +
  `SpecificationRevision` (draft → activate → supersede). First real use of the
  versioning pattern.
- **Task 005b — Tooling / Cliché Asset (SR-03):** `ToolingAsset` identity +
  usage-life master with retire/reactivate lifecycle. Cost model and automatic
  usage capture deferred.
- **Task 006 — Manufacturing:** `WorkCenter` / `Machine` resource masters +
  versioned `BillOfMaterials` and `Routing` bound to a spec revision.
- **Task 007 — Inventory Foundation:** company/site-scoped `Warehouse` master +
  per-user `WarehouseAccess`. Stock movements/kardex/lots deferred behind Q-046.
- **Task 008 — Quality Foundation:** `QualityCharacteristic` catalogue +
  versioned `QualityPlan`. Check execution/results/NCR/COA/recall deferred.
- **Task 009 — Procurement Foundation:** `PurchaseRequisition` / `PurchaseOrder`
  header+line documents with a status state machine. GRN/MRP/RFQ/thresholds/
  invoice-matching deferred.
- **Task 010 — Sales Order Management:** `SalesOrder` header+line (the MTO demand
  origin) with confirm/close/cancel. Pricing/ATP/allocation/shipment/invoicing
  deferred.
- **Task 011 — Production Order Management:** header-only `ProductionOrder` (Work
  Order) built to a frozen spec/BOM/routing revision, with release/complete/
  close/cancel. Material issue/genealogy/confirmations/QC results deferred.

### Foundation "make-it-usable" slices (2026-08-21 → 08-22)

After the domain masters, the backend-complete-but-headless foundation surfaces
were given UIs (and, where a data-integrity gap existed, hardened):

- **Workflow / Approvals engine:** per-user approvals inbox + hardened per-action
  authorization on instances (closed a gap where any authenticated user could
  cancel any workflow).
- **Notifications:** in-app inbox + header unread bell (self-authorizing; email/
  SMS/push remain deferred, DR-008).
- **Audit log viewer:** read-only searchable trail at `/audit/logs`.
- **Organization master:** Company → Site browse/create; hardened three viewsets
  to audited writes.
- **Workflow definitions admin:** browse/create approval *shapes* (no rule matrix,
  #7); hardened the definition viewset to audited writes.
- **Documents / Attachments** (2026-08-22): generic entity-keyed
  attachment register with multipart upload + authenticated blob download +
  soft-delete. Added `postForm`/`getBlob` transport to the shared API client.
- **Live home dashboard** (2026-08-22): the placeholder landing page now
  shows live per-module record counts (partners, products, materials, customer
  products, sales/purchase/production orders, warehouses), each tile gated by the
  module's own `*.view` permission and linking to its list page. Counts read the
  authoritative `count` from existing paginated endpoints via a `page_size=1`
  probe — no metric is fabricated and no KPI is defined.
- **Record-detail pattern + in-context attachments** (2026-08-22, latest): a
  reusable read-only detail view (`useRecord` hook + `RecordDetail` +
  `AttachmentPanel`) applied to the Partner entity as the reference
  (`/master-data/partners/:id`). Surfaces only existing retrieve-endpoint data and
  embeds the generic attachment store in the owning record's context; other
  modules can adopt the same pattern verbatim when prioritized.

All foundation apps now have a working UI or are self-authorizing. **Un-gated
"make-the-foundation-usable" work is complete.**

### Runtime verification (2026-08-22)

**Task 012 — Runtime Verification** (same day). Executed the previously
never-run verification checklist in a real dev environment and fixed what it
surfaced. The whole platform moves from *IMPLEMENTED + STATICALLY CHECKED* to
*RUNTIME VERIFIED* (SQLite test scope; Docker/Postgres path still pending).

What was run: `pip install -r requirements/dev.txt`; flake8 + black + isort;
`makemigrations` for all 18 apps (21 initial migration files, `--check` clean);
full Django suite; `npm install` + typecheck + lint + vitest + `vite build`.

What it found & fixed:
- **Latent import crash:** `identity.User.timezone` field shadowed the
  `django.utils.timezone` module inside the class body, so `default=timezone.now`
  would have blown up at first import — invisible to static checking. Import
  aliased (`dj_timezone`); field/API names unchanged.
- **Tests never saw audit rows:** `atomic_with_events` defers event publishing
  via `transaction.on_commit`, which never fires under `TestCase`. Fixed once,
  centrally, in the shared factory: `auth_client()` now returns an
  `OnCommitExecutingClient` that drains post-commit callbacks after each request
  (production behavior untouched). ~25 audit assertions across every module now
  exercise the real trail.
- **Error-envelope assertion bugs:** nine domain tests asserted serializer error
  keys at the response top level instead of the standardized
  `error.details.<field>` envelope; corrected to the documented shape.
- **Missing permission grant** in `core.test_errors.test_not_found_envelope`
  (403 vs 404).
- **Frontend tsconfig defects:** missing `@types/node` (`node:url` unresolved)
  and invalid `composite`+`noEmit` project reference (TS6310). Unified into one
  tsconfig (references dropped, scripts off `tsc -b`), pinned `@types/node`.
- **Type/lint errors surfaced by real toolchain:** `CardProps.title` conflict
  with native DOM attrs (`Omit<…, 'title'>`), unused translation hook in
  `MachinesPage`, two fast-refresh lint warnings scoped off for the idiomatic
  provider+hook / local-fallback files.
- **Tooling hardening:** test DB moved from in-memory shared-cache SQLite to a
  throwaway file-backed SQLite (stability on Windows); `--noinput` added to
  Makefile + CI test targets so stale test DBs can't block on the interactive
  destroy prompt.

Result: backend **203/203**, frontend **52/52**, builds green.

### Audit trail completeness & diff viewer (2026-08-22)

**Task 013 — Audit Trail: State Snapshots + Entry Detail** (same day, un-gated
work per the module matrix). Two halves:

*Backend — make every trail row diff-capable.* The generic write service
(`apps.core.service`) now captures best-effort JSON snapshots of the record and
carries them on the domain events: `EntityCreated.state` (after),
`EntityDeleted.state` (before), `EntityUpdated.before_state`/`after_state`
(around the save; `changes` keeps the validated_data view). The audit subscriber
maps them onto the existing `before_state`/`after_state` columns — **no schema
change**, the columns already existed. Domain services that publish
`EntityUpdated` directly (status transitions) still work unchanged; their rows
keep the validated_data view until/unless they adopt full snapshots.

*Frontend — entry detail with before → after diff.* Clicking a row in the audit
viewer (`CollectionView` gained an optional `onRowClick`) opens a read-only modal
(`AuditEntryDetail`) that fetches the entry via the existing retrieve endpoint
and renders who/what/when plus a field-level diff table; changed rows are
highlighted. CREATE entries show the recorded state on the "After" side, DELETE
on the "Before" side. en/fa locale parity maintained.

Tests: 3 new snapshot tests in `apps.audit` (create/update/soft-delete via the
real service layer with `captureOnCommitCallbacks`), 3 component tests for the
detail modal (fetch + diff rendering, backdrop close). Suite green throughout.

### Order-book reporting (2026-08-22)

**Task 014 — Order-Book Status Summaries** (same day, un-gated reporting on
confirmed data only). A shared `StatusSummaryMixin`
(`apps/core/viewsets.py`) adds `GET <prefix>/summary/` to the four transactional
document views (`sales/orders`, `procurement/orders`,
`procurement/requisitions`, `production/orders`). It aggregates the same
filtered, permission-gated queryset as the list endpoint and zero-fills every
status choice the model declares — pure counting of existing rows, no execution
semantics invented. The dashboard gained an **Order book** card: per-document-type
totals plus per-status chips (only non-zero statuses render), permission-gated
exactly like the existing count tiles, en/fa localized.

Tests: 4 backend tests (aggregation + zero-fill, list-filter parity,
per-endpoint RBAC gate, remaining endpoints wired), 1 frontend API test.
Suite: backend 221/221, frontend 56/56, typecheck/lint/build green.

### Sales-order detail & in-context audit history (2026-08-22)

**Task 015 — Document Detail Page + Audit History Panel** (same day, un-gated
frontend completion). Transactional documents previously had list+create pages
only. Added:

* `AuditHistoryPanel` (`src/components`) — generic, reusable panel showing the
  most recent trail entries for one record via the existing
  `audit.log.view`-gated entity filters; clicking an entry opens the Task-013
  before/after detail modal. Rendered only for holders of `audit.log.view`.
* `SalesOrderDetailPage` (route `/sales/orders/:id`, permission-gated) — order
  header summary, its lines (`/sales/order-lines/?order=`), and the record's
  audit history. The orders list rows now navigate to it via the shared
  `onRowClick`. en/fa locale parity maintained.

No backend change was required — both surfaces consume existing endpoints.
Tests: history-fetcher URL contract test added; suite green throughout.

### Procurement & production detail pages (2026-08-22)

**Task 016 — Remaining Document Detail Pages** (same day). The Task-015
pattern extended to every transactional document:

* `PurchaseOrderDetailPage` (`/procurement/orders/:id`) — header, material
  lines (incl. unit price / source requisition line), audit history.
* `PurchaseRequisitionDetailPage` (`/procurement/requisitions/:id`) — header,
  material lines, audit history.
* `ProductionOrderDetailPage` (`/production/orders/:id`) — full frozen
  definition (customer product, spec/BOM/routing revisions, sales-order line,
  planned qty) plus audit history. No lines section by design — the document is
  header-only until the execution layer unblocks (Q-046 cluster).

All three list pages navigate to their detail via row click. en/fa parity kept;
no backend change (existing endpoints only).

### Customer-product detail with revision chain (2026-08-22)

**Task 017 — Product Engineering Detail** (same day). `CustomerProductDetailPage`
(`/engineering/customer-products/:id`, row-click from the list): identity
header, the complete specification revision chain (draft → active → superseded,
with effective dates and change reasons), the selected revision's full spec
(dimensions + tolerances, print process, lamination/cold-seal, surface finish),
its structure-layer / print-color / parameter tables, and the record's audit
history. Preselects the ACTIVE revision. Consumes only existing
`engineering.*.view` endpoints. en/fa parity kept.

*Integration note:* a concurrent agent initially shipped `SpecificationDetailPage`
(single-revision view) at the same time; App.tsx collisions (duplicate
imports/routes from simultaneous edits) were repaired and the design was then
converged onto the single root-centric surface — the separate revision-detail
page was removed and the specifications list rows navigate to the owning
product's revision chain instead (`/engineering/customer-products/:rootId`).

### Parallel-agent work: shared API layer, convergence & hardening (2026-08-22)

**Task 018 — Engineering API foundation + document-download hardening**
(same day, parallel implementation agent). Ran alongside Tasks 016/017:

*Engineering API layer (consumed by Task 017's page).* `api/engineering.ts`
extended with complete serializer-mirroring types (`SpecificationRevision`
gained width/length/gusset + tolerance fields) and typed fetchers:
`fetchCustomerProduct`, `fetchSpecification`, `listSpecificationRevisions`
(newest-first), `listSpecLayers/Colors/Parameters` (stable ordering);
`listToolingAssetsByCustomerProduct` in `api/tooling.ts`. All URL contracts
regression-tested. The specifications list also navigates rows to the owning
product detail, and a mojibake em-dash in its code column was fixed.

*Concurrent-edit repair.* Simultaneous edits by both agents duplicated
`CustomerProductDetailPage` imports/routes in `App.tsx`; resolved to exactly
one route per path (build-breaking otherwise).

*Security hardening — documents.* Attachment download echoed the raw stored
filename into `Content-Disposition`; a name containing `"` could break out of
the quoted-string and CR/LF would crash header serialization. New
`quoted_header_filename` validator escapes `"`, `\`, CR, LF; regression tests
cover both the endpoint and the helper.

*Policy observation (not changed):* attachment **upload** currently requires
only `documents.attachment.view` because no `documents.attachment.manage`
code exists in the RBAC seed (`view`/`delete` only); POST falls through to
the view code via `permission_map`. If uploads should be a distinct privilege,
a seed code must be added first — left to the architecture owner.

*Drift guards (new regression class).* Two automated guards now fail CI on
referential drift between layers:

- Backend `apps/identity/tests/test_seed_covers_declared_permissions.py` —
  every `required_permission` / `permission_map` code declared on any viewset
  must exist in `seed_rbac.PLATFORM_PERMISSIONS` (a declared-but-unseeded code
  can never be granted → permanent 403) and must keep the
  `module.resource.action` shape.
- Frontend `src/auth/__tests__/permissionCodes.test.ts` — every
  `hasPermission('…')` / `requiredPermission="…"` literal in UI source must
  exist in the backend seed file itself (single source of truth). Mutation-
  verified: a typo'd resource fails the test.
- Frontend `src/i18n/__tests__/translationKeys.test.ts` — every static
  `t('…')` key must exist in BOTH en.json and fa.json, and every dynamic
  template prefix (`t(\`prefix.${x}\`)`) must match at least one real key per
  locale. Mutation-verified.

Verification after this task: backend **225/225**, frontend **66/66**,
`makemigrations --check` clean, typecheck/lint/build green both sides.

### Silent-action-failure fix + shared async-action hook (2026-08-22)

**Task 019 — Row actions now surface their errors** (same day, parallel
agent). List-page row actions (`try/finally`, no `catch`) failed silently:
an illegal transition or network error cleared the spinner and showed nothing,
leaving the user to assume success. Added the shared
`useAsyncAction` hook (`src/hooks`) — never rejects, tracks per-row busy state,
captures the `ApiError` for inline rendering — with unit tests including a
stale-response guard. Adopted in Tooling assets (retire/reactivate), Approvals
inbox (approve/reject) and Notifications (read/read-all). The document list
pages (sales/procurement/production transitions, specification activation)
still use the old pattern and are adoption candidates for whoever touches them
next.

Verification: frontend **69/69**, typecheck/lint/build green.

### Gap audit #1 — encoding repair + Jalali presentation layer (2026-08-22)

**Task 020 — Repository Hygiene & Persian Dates.**

*Encoding repair.* A systematic scan found double-encoded UTF-8 mojibake
(`â€”`/`â†'`-style cp1252 artifacts, plus stray BOMs) in 16 files — partly
pre-existing from the authoring sandbox, partly introduced by shell round-trips
during this session. All repaired deterministically (exact codepoint mapping);
backend suite re-run green, confirming comment/docstring-only damage.

*Jalali dates (frontend).* The fa-first UI had zero Jalali rendering despite
the documented convention (UTC canonical; Jalali at presentation layer).
Added `src/i18n/dates.ts` on `jalaali-js`: `formatDateTime(iso, lang)` renders
Solar-Hijri with Persian digits for `fa`, Gregorian otherwise; date-only strings
drop the time part. Wired into every user-visible timestamp surface (audit
viewer list/detail/history panel and all five document detail pages). API
contract untouched. 6 new formatter unit tests incl. the Nowruz anchor
(2026-03-21 → ۱۴۰۵/۰۱/۰۱).

*RBAC / error-contract audit results (no changes needed):* every registered
viewset declares permissions; `HasPermission` fails closed (undeclared ⇒ deny
unless explicit `allow_any_authenticated` opt-in); notifications are
self-scoped by queryset; workflow authorizes per action with object-level
guards in the service; no raw `status=4xx` responses exist outside the
standardized handler. Recorded here as the audit baseline.

### Final quality/security/gap audit (2026-08-22)

**Task 021 — Independent audit pass** (same day, parallel agent). Systematic
security / contract / reliability sweep. Findings and fixes:

*Auth brute-force resistance (new).* `POST /auth/login/` and
`/auth/refresh/` accepted unlimited attempts per IP. Added scoped
`AuthAnonThrottle` (per-IP, rate `auth` = env `AUTH_THROTTLE_RATE`, default
30/min) on both views, plus `ThrottledError` (429) in the standardized error
hierarchy — previously a DRF `Throttled` would have fallen through to a 500
SystemError envelope. Frontend `ApiErrorType` union and status mapping extended
with `ThrottledError`; DRF's `Retry-After` header is preserved. Tests: within-
rate behavior, 429 envelope + header, credential-correctness cannot bypass,
refresh scope covered, production rate wiring guard.

*Self-profile data integrity.* `PATCH /auth/me/` applied raw `setattr`: an
over-long `full_name` produced a 500 (DB DataError), an unknown `language`
code persisted silently and broke locale rendering, arbitrary `timezone`
strings were accepted. Now validated (`MeUpdateSerializer`: model max-lengths,
language choices, IANA time-zone check via `zoneinfo`); auth-relevant fields
remain unreachable. Tests: valid update persists; each bad value → clean 400
envelope; `is_superuser` stays ignored.

*CI gaps.* Backend job never verified migration drift — added
`makemigrations --check --dry-run --noinput` step. Frontend job used
`npm install` despite a committed lockfile — switched to `npm ci` (locked,
reproducible) plus npm dependency caching.

*Audited, no change required:* CORS allow-list, ALLOWED_HOSTS, JWT rotation +
blacklist, workflow decision object-level guards, notifications self-scoping,
attachment upload-under-view policy (documented above), SVG-served-as-
attachment XSS surface (mitigated by forced download disposition).

*Error-envelope quality.* SimpleJWT raises `AuthenticationFailed` with a
*dict* detail; the handler's `str(detail)` leaked a Python repr
(`"{'detail': ErrorDetail(…)…}"`) into client messages on invalid refresh
tokens. `_clean_detail` now flattens dict details to their readable message.
Regression-tested against the live refresh endpoint.

Verification: backend **237/237**, frontend **75/75**, migration check clean,
flake8/black/isort green, typecheck/lint/build green.


### QA cycle: object-level authorization regression test (2026-08-22)

**Task 022 — Workflow decision guard pinned** (independent QA agent). The
decision endpoint deliberately admits any authenticated user at the permission
layer (approvers must not need broad instance rights); the actual guard lives
in `record_decision` (only an assigned, still-pending approver may act).
That security-relevant behavior had no direct regression test. Added
`test_decision_by_unassigned_user_is_rejected`: an outsider POSTing a
decision gets a 422 BusinessRuleError and the instance stays UNDER_REVIEW.
Suite: backend 238/238.

Audit sweeps this cycle found no defects requiring code changes: documents
surface (sanitized names, opaque storage keys, escaped Content-Disposition,
extension/size policy, permission-gated upload/download/delete — all covered
by existing tests), auth endpoints (throttled login/refresh, refresh-token
blacklist on logout, LOGIN/LOGOUT audited), transition concurrency
(`select_for_update` in every domain service), and frontend error-contract
interpretation (`ApiError` mirrors the envelope exactly).

### Usability completion pass (2026-08-22)

**Task 023 — Detail pages, create forms, dashboard activity, error rendering**
(same day). Systematic completion of the user-facing surface where the backend
was already complete.

*Detail pages for all list entities.* Every master-data browse screen now has
a read-only detail view: `MaterialDetailPage` (subtype, planning attrs, MSDS,
attachments, audit history), `ProductsDetailPage`, `WarehouseDetailPage` (store
type, site, notes), and `EmployeeDetailPage`. All follow the established
`RecordDetail` + `AttachmentPanel` + `AuditHistoryPanel` pattern. Partner
detail gained the audit-history panel it was missing.

*Material create form.* `MaterialCreatePage` with company/UoM pickers, subtype
dropdown, optional planning fields (lead time, shelf life, reorder point,
safety/min/max stock), hazardous flag and MSDS ref. Routes through the audited
service layer.

*Dashboard recent activity.* A `RecentActivity` widget on the home dashboard
shows the newest 8 audit-trail entries (permission-gated to `audit.log.view`).
Pure read — no metric invented.

*Error rendering on document list pages.* The three transactional document list
pages that adopted `useAsyncAction` (Sales Orders, Production Orders, Purchase
Requisitions) now show inline error alerts when a status transition fails —
they were previously silent (the hook captured errors but the component never
rendered them).

*Encoding fix.* Repaired 3 mojibake artifacts (`Â±` → `±`, `â€¦` → `…`) in the
CustomerProductDetailPage tolerance fields, a carryover from the earlier
encoding repair pass.

*Variable-shadowing fix.* Three document list pages (SalesOrdersPage,
ProductionOrdersPage, PurchaseRequisitionsPage) had a `run(id, action)` function
whose parameter `action` shadowed the outer `useAsyncAction()` result, causing
`action.run()` to resolve to the string parameter instead of the hook. Renamed
parameters to avoid shadowing.

Verification: backend **238/238**, frontend **75/75**, migration check clean,
flake8/black/isort green, typecheck/lint/build green.

<!-- APPEND-MODULE-TABLE -->

## Module status matrix

| Module (app) | Built & usable now | Deferred (gated) layer | Gate |
|---|---|---|---|
| **core / identity** | Base models, soft delete, error envelope, event bus, audited viewsets, RBAC, JWT | — | — |
| **organization** | Company → Site masters (audited, with UI) | Department/capability UI, cross-company scoping UI | Q-055 |
| **audit** | Append-only trail + read-only viewer + entry detail with before/after diff | Export, tamper-evidence | — |
| **documents** | Generic attachment register (upload/download/delete) | Attachment policy, in-context panels, controlled-doc/e-sign | — |
| **localization** | Jalali/Gregorian, number/calendar utilities | — | — |
| **notifications** | In-app inbox + bell | Email / SMS / push channels | DR-008 |
| **workflow** | Generic engine + approvals inbox + definitions admin | Approval hierarchy/threshold **content**, escalation/SLA | Q-054/056, #7 |
| **catalog / partners / hr** | Master data (products, materials, UoM, partners, employee) | Product coding scheme | Q-019 |
| **engineering** | Versioned CustomerProduct + SpecificationRevision; ToolingAsset | Tooling cost model; spec-revision trigger rule; auto usage capture | Q-004/036, Q-024, Q-046 |
| **manufacturing** | WorkCenter/Machine; versioned BOM + Routing | Consumption bases/waste factors; routing templates | Q-027, Q-016/042, Q-029 |
| **inventory** | Warehouse master + access grants | **Stock movements, kardex, lots/rolls, genealogy** | **Q-046**, Q-048/049 |
| **quality** | Characteristic catalogue + versioned QualityPlan | Check execution, results, NCR/hold, scrap/rework, COA, recall | Q-039/040/043/044, Q-046 |
| **procurement** | PR / PO header+line + status machine | Goods receipt/GRN, MRP, RFQ, thresholds, invoice matching, valuation | #7/#14/#17/#23, Q-034 |
| **sales** | SalesOrder header+line + status machine | Pricing/proforma, ATP, allocation, shipment, invoicing, credit | Q-046, #11/#12/#18 |
| **production** | ProductionOrder header + status machine | Material issue/genealogy, confirmations/scrap/downtime, QC results | **Q-046**, SR-05/06/08 |

<!-- APPEND-REMAINING -->

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

**Done 2026-08-22 (Task 012, Windows dev machine, no Docker):**

```bash
# Backend — all green
cd erp/backend
pip install -r requirements/dev.txt
flake8 apps config && black --check apps config && isort --check-only apps config
python manage.py makemigrations        # done: 21 initial migration files committed
python manage.py makemigrations --check --dry-run   # no drift
python manage.py test --settings=config.settings.test --noinput   # 238/238 OK

# Frontend — all green
cd ../frontend
npm install
npm run typecheck && npm run lint && npm run test && npm run build  # 75/75 OK
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

## Recommended next step

Answer **Q-046** (with Q-048/049/026). That one cluster unblocks more downstream
engineering than everything else combined — the traceability/stock/execution layer
across procurement, inventory, quality, sales, and production. With those four
decisions, autonomous implementation can resume immediately without further input.



