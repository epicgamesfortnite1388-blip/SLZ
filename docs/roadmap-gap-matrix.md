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
| Partners | ✅ | ✅ | ✅ | ✅ | **reference edit flow**; contacts/addresses sub-panels; attachments; audit history |
| ↳ Customer role profile | — | — | — | — | 🟡 backend complete (`requires_coa`, sales line) — **no UI surface yet** |
| ↳ Supplier role profile | — | — | — | — | 🟡 backend complete (`is_approved`, evaluation stub) — **no UI surface yet** |
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

- **Execution & traceability layer** across inventory/production/quality/sales/
  procurement: ⛔ Q-046 (with Q-048/049/026). Extension points documented in
  [architecture/execution-preparation.md](architecture/execution-preparation.md).
- **Approval hierarchy/threshold content:** ⛔ #7, Q-054/056 (engine + admin built).
- **Costing, scrap absorption, tooling cost model:** ⛔ Q-031/033/034/035, Q-004/036.
- **Multi-company data-scoping rules + scoping UI:** ⛔ Q-055/Q-053 — impact map in
  [architecture/multi-tenancy-preparation.md](architecture/multi-tenancy-preparation.md).
- **Attachment upload privilege policy:** needs an RBAC seed decision (documented
  in PROJECT-STATUS Task 021).

## Infrastructure-gated

- 🔧 Container path (image builds, PostgreSQL/Redis under Compose, nginx):
  **NOT EXECUTED — DOCKER UNAVAILABLE** in the authoring environment.
  Application logic itself is fully verified on the SQLite test profile;
  `RELEASE-CHECKLIST.md` §12–13 is the outstanding runbook step.

## Remaining unblocked workstreams (ranked)

1. **Replicate the edit flow** to remaining master-data entities (products,
   materials, companies, sites, employees, work centers, machines, warehouses…)
   using `PartnerEditPage` as the pattern; each gets a PATCH contract test.
2. **Customer/Supplier role-profile panels** on the partner detail page
   (backend done; follow `PartnerSubPanels`).
3. **Detail/edit polish for the small entities** flagged ¹ above, if desired.
4. Everything else requires the business decisions above.
