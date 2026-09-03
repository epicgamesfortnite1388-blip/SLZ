# SLZ ERP — Roadmap Gap Matrix

**Generated:** 2026-08-22, from direct repository inspection (not from task
notes). Ground truth at time of writing: **245** backend tests / **85+**
frontend tests green, migration-drift gate clean, lint/typecheck/build green,
88 frontend page modules, 46 registered backend viewsets.

## Status definitions

| Mark | Meaning |
|---|---|
| ✅ | IMPLEMENTED + VERIFIED (exercised by the automated suites and/or the live local profile) |
| 🟡 | PARTIAL — some confirmed scope present, a listed remainder missing |
| ⛔ | BLOCKED by an open SLZ business decision (must not be invented) |
| 🔧 | Infrastructure-gated (environment capability, not code) |

---

## Master data

| Entity | List | Create | Detail | Edit | Notes |
|---|---|---|---|---|---|
| Companies | ✅ | ✅ | —¹ | —¹ | ¹ small entities; detail/edit not yet built |
| Sites | ✅ | ✅ | —¹ | —¹ | incl. timezone field |
| Departments | ✅ | ✅ | —¹ | —¹ | parent hierarchy supported server-side |
| Site capabilities | ✅ | ✅ | —¹ | —¹ | SR-15 |
| Employees | ✅ | ✅ | ✅ | —² | |
| Partners | ✅ | ✅ | ✅ | ✅ | **reference edit flow**; contacts/addresses sub-panels; customer/supplier role-profile panels ✅; attachments; audit history |
| ↳ Customer role profile | — | ✅ | ✅ | ✅ | COA requirement, delivery tolerance, sales line — panel on partner detail |
| ↳ Supplier role profile | — | ✅ | ✅ | ✅ | approval flag, evaluation stub, lead time — panel on partner detail |
| Products | ✅ | ✅ | ✅ | —² | taxonomy Group/Type/Class/Family all have list+create |
| Materials | ✅ | ✅ | ✅ | —² | hazardous flag, subtypes |
| UoMs | ✅ | ✅ | —¹ | —¹ | conversions list+create ✅ |
| Product coding scheme | | | | | ⛔ Q-019 — numbering scheme undecided |

² Edit flows exist **only** for Partner (the reference pattern:
`PartnerEditPage` + PATCH contract tests). Replicating it per entity is the
largest remaining unblocked UI workstream.

## Engineering

| Area | Status | Notes |
|---|---|---|
| Customer products | ✅ list/create/detail | detail = identity + full revision chain + selected-revision content + audit |
| Specification revisions | ✅ view/activate | revision chain rendered in CP detail; layers/colors/parameters tables ✅ |
| New draft revision creation (UI) | 🟡 | backend service exists; UI intentionally absent pending Q-024 (revision trigger rule) |
| BOM roots/revisions/lines | ✅ | root detail with lines table; `consumption_basis` free text (Q-027 open) |
| Routing roots/revisions/operations | ✅ | operations table; templates OPEN (Q-029) |
| Tooling assets | ✅ | list/create/detail, retire/reactivate, usage-life flag |

## Procurement / Sales / Production

| Area | List | Create | Detail | Status transitions | Blocked remainder |
|---|---|---|---|---|---|
| Purchase requisitions | ✅ | ✅ (+inline lines) | ✅ | submit/approve/reject/cancel ✅ | approval thresholds ⛔ #7 |
| Purchase orders | ✅ | ✅ (+inline lines) | ✅ | approve/send/close/cancel ✅ | GRN ⛔ Q-046/#17/#18; valuation ⛔ |
| Sales orders | ✅ | ✅ (+inline lines) | ✅ | confirm/close/cancel ✅ | allocation/shipment/invoicing ⛔ Q-046/#11/#12 |
| Production orders | ✅ | ✅ | ✅ | release/complete/close/cancel ✅ | material issue/genealogy/confirmations/QC results ⛔ Q-046 cluster |

## Foundation surfaces

| Surface | Status |
|---|---|
| Auth (login/refresh/logout/me, throttled) | ✅ |
| RBAC (seeded catalogue, fail-closed enforcement, drift guards both sides) | ✅ |
| Audit trail (viewer + before/after diff + per-record history panels) | ✅ |
| Documents/attachments (register + upload/download + in-context panels) | ✅ |
| Notifications (in-app inbox + unread bell) | ✅ |
| Workflow engine (approvals inbox + definitions admin) | ✅ |
| Users admin (read-only) | ✅ — mutation stays CLI until Q-053 |
| Roles admin (list/create) | ✅ — assignment matrix content ⛔ Q-053/054/056 |
| Dashboard (module counts, order-book strips, recent activity) | ✅ |
| Localization (fa/en parity guard, Jalali display, RTL) | ✅ |
| Drift guards (permissions ↔ seed, i18n keys, API paths) | ✅ |

## Blocked (business decisions) — recorded once, not re-litigated

- **Approval hierarchy/threshold content:** ⛔ #7, Q-054/056 (engine + admin built).
- **Costing scrap/tooling cost model extras:** ⛔ Q-004/036 — dated WA costing
  engine itself is ✅ (RECEIPT + ISSUE + PRODUCTION_OUTPUT auto-posted, 2026-09-03).
- **Multi-company data-scoping UI:** ⛔ Q-053 — the RULES are implemented
  (Q-055: company_scope_lookup on all viewsets, audited writes, cross-company
  regression tests); the role-assignment *matrix UI* remains open.
- **Attachment upload privilege policy:** needs an RBAC seed decision (documented
  in PROJECT-STATUS Task 021).

### Implemented since this matrix was generated (2026-08-22 → 2026-09-03)

- ✅ **Execution & traceability layer** (Q-046/048/049/026): GRN receiving with
  traceability-unit creation + IN movements + RECEIPT cost layers; material
  issues (explicit/backflush); production outputs; genealogy links; QC check
  results per roll (PASS/FAIL/HOLD); allocations (reserve/release); shipment
  deliveries with atomic OUT movements; warehouse transfers; PRODUCTION_OUTPUT
  auto-costing. Container-verified on a VPS (PostgreSQL/Redis/Celery/nginx).
- ✅ **Concurrency hardening:** OUT postings serialized via advisory xact locks;
  delivery locks the allocation; GRN/shipment nonce idempotency; workflow
  decisions/cancel row-locked; two-thread PostgreSQL regression tests.
- ✅ **Production hardening:** standalone `docker-compose.prod.yml` (zero public
  ports), real secrets (`scripts/gen-env.sh`), nightly backups
  (`scripts/backup-erp.sh`), Cloudflare Tunnel connector. Public DNS routing of
  the hostname remains P2 infrastructure (documented in `.agent-work/STATE.md`;
  no Cloudflare/DNS changes without explicit authorization).

## Infrastructure-gated

- ✅ Container path verified (2026-09-03): images build, full prod compose stack
  healthy on a 1-vCPU/4 GB VPS — PostgreSQL/Redis/Celery/nginx, readiness probes,
  JWT login, audited writes, and the PG-only concurrency suites all green.

## Remaining unblocked workstreams (ranked)

1. **Replicate the edit flow** to remaining master-data entities (products,
   materials, companies, sites, employees, work centers, machines, warehouses…)
   using `PartnerEditPage` as the pattern; each gets a PATCH contract test.
2. **Detail/edit polish for the small entities** flagged ¹ above, if desired.
3. Everything else requires the business decisions above.

## Adversarial audit additions (2026-08-23, QA agent)

| Finding | Severity | Status |
|---|---|---|
| Attachments had NO company scoping (cross-company list/download/upload/delete) | P0 | FIXED — resolver + stamping + scoped register; 8 regression tests |
| Stock movement OUT balance check is check-then-write without locking | P2 (race under concurrent writers on Postgres) | FIXED 2026-09-03 — advisory xact lock keyed on company/warehouse/material|unit inside the posting; two-thread PG regression tests |
| Sample product data fit: per-layer material COLOR and layer treatments (corona/sealability/chemical/reflection) have no structured fields; print-cylinder metadata (repeat/sleeve/plate) unmodeled | P3 | DOCUMENTED - representable today only via free-form SpecParameter conventions; needs a modeling decision |
| nginx nested asset location suppressed inherited security headers | P2 | FIXED in committed hardening pass (06cc64d lineage) - verify headers duplicated into the assets location at next deploy review |
| .env.example contained stray "[TEMPLATE]" line | P4 | check current state |
| GRN frontend path drift (/grns/ vs /goods-receipts/) | P2 | FIXED by Agent 1 (d64cdd9); apiPathDrift guard now prevents recurrence |
