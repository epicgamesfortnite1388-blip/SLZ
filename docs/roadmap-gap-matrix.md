# SLZ ERP â€” Roadmap Gap Matrix

**Generated:** 2026-08-22, from direct repository inspection (not from task
notes). Ground truth at time of writing: **245** backend tests / **85+**
frontend tests green, migration-drift gate clean, lint/typecheck/build green,
88 frontend page modules, 46 registered backend viewsets.

## Status definitions

| Mark | Meaning |
|---|---|
| âœ… | IMPLEMENTED + VERIFIED (exercised by the automated suites and/or the live local profile) |
| ðŸŸ¡ | PARTIAL â€” some confirmed scope present, a listed remainder missing |
| â›” | BLOCKED by an open SLZ business decision (must not be invented) |
| ðŸ”§ | Infrastructure-gated (environment capability, not code) |

---

## Master data

| Entity | List | Create | Detail | Edit | Notes |
|---|---|---|---|---|---|
| Companies | âœ… | âœ… | â€”Â¹ | â€”Â¹ | Â¹ small entities; detail/edit not yet built |
| Sites | âœ… | âœ… | â€”Â¹ | â€”Â¹ | incl. timezone field |
| Departments | âœ… | âœ… | â€”Â¹ | â€”Â¹ | parent hierarchy supported server-side |
| Site capabilities | âœ… | âœ… | â€”Â¹ | â€”Â¹ | SR-15 |
| Employees | âœ… | âœ… | âœ… | â€”Â² | |
| Partners | âœ… | âœ… | âœ… | âœ… | **reference edit flow**; contacts/addresses sub-panels; customer/supplier role-profile panels âœ…; attachments; audit history |
| â†³ Customer role profile | â€” | âœ… | âœ… | âœ… | COA requirement, delivery tolerance, sales line â€” panel on partner detail |
| â†³ Supplier role profile | â€” | âœ… | âœ… | âœ… | approval flag, evaluation stub, lead time â€” panel on partner detail |
| Products | âœ… | âœ… | âœ… | â€”Â² | taxonomy Group/Type/Class/Family all have list+create |
| Materials | âœ… | âœ… | âœ… | â€”Â² | hazardous flag, subtypes |
| UoMs | âœ… | âœ… | â€”Â¹ | â€”Â¹ | conversions list+create âœ… |
| Product coding scheme | | | | | â›” Q-019 â€” numbering scheme undecided |

Â² Edit flows exist **only** for Partner (the reference pattern:
`PartnerEditPage` + PATCH contract tests). Replicating it per entity is the
largest remaining unblocked UI workstream.

## Engineering

| Area | Status | Notes |
|---|---|---|
| Customer products | âœ… list/create/detail | detail = identity + full revision chain + selected-revision content + audit |
| Specification revisions | âœ… view/activate | revision chain rendered in CP detail; layers/colors/parameters tables âœ… |
| New draft revision creation (UI) | ðŸŸ¡ | backend service exists; UI intentionally absent pending Q-024 (revision trigger rule) |
| BOM roots/revisions/lines | âœ… | root detail with lines table; `consumption_basis` free text (Q-027 open) |
| Routing roots/revisions/operations | âœ… | operations table; templates OPEN (Q-029) |
| Tooling assets | âœ… | list/create/detail, retire/reactivate, usage-life flag |

## Procurement / Sales / Production

| Area | List | Create | Detail | Status transitions | Blocked remainder |
|---|---|---|---|---|---|
| Purchase requisitions | âœ… | âœ… (+inline lines) | âœ… | submit/approve/reject/cancel âœ… | approval thresholds â›” #7 |
| Purchase orders | âœ… | âœ… (+inline lines) | âœ… | approve/send/close/cancel âœ… | GRN â›” Q-046/#17/#18; valuation â›” |
| Sales orders | âœ… | âœ… (+inline lines) | âœ… | confirm/close/cancel âœ… | allocation/shipment/invoicing â›” Q-046/#11/#12 |
| Production orders | âœ… | âœ… | âœ… | release/complete/close/cancel âœ… | material issue/genealogy/confirmations/QC results â›” Q-046 cluster |

## Foundation surfaces

| Surface | Status |
|---|---|
| Auth (login/refresh/logout/me, throttled) | âœ… |
| RBAC (seeded catalogue, fail-closed enforcement, drift guards both sides) | âœ… |
| Audit trail (viewer + before/after diff + per-record history panels) | âœ… |
| Documents/attachments (register + upload/download + in-context panels) | âœ… |
| Notifications (in-app inbox + unread bell) | âœ… |
| Workflow engine (approvals inbox + definitions admin) | âœ… |
| Users admin (read-only) | âœ… â€” mutation stays CLI until Q-053 |
| Roles admin (list/create) | âœ… â€” assignment matrix content â›” Q-053/054/056 |
| Dashboard (module counts, order-book strips, recent activity) | âœ… |
| Localization (fa/en parity guard, Jalali display, RTL) | âœ… |
| Drift guards (permissions â†” seed, i18n keys, API paths) | âœ… |

## Blocked (business decisions) â€” recorded once, not re-litigated

- **Execution & traceability layer** across inventory/production/quality/sales/
  procurement: â›” Q-046 (with Q-048/049/026). Extension points documented in
  [architecture/execution-preparation.md](architecture/execution-preparation.md).
- **Approval hierarchy/threshold content:** â›” #7, Q-054/056 (engine + admin built).
- **Costing, scrap absorption, tooling cost model:** â›” Q-031/033/034/035, Q-004/036.
- **Multi-company data-scoping rules + scoping UI:** â›” Q-055/Q-053 â€” impact map in
  [architecture/multi-tenancy-preparation.md](architecture/multi-tenancy-preparation.md).
- **Attachment upload privilege policy:** needs an RBAC seed decision (documented
  in PROJECT-STATUS Task 021).

## Infrastructure-gated

- ðŸ”§ Container path (image builds, PostgreSQL/Redis under Compose, nginx):
  **NOT EXECUTED â€” DOCKER UNAVAILABLE** in the authoring environment.
  Application logic itself is fully verified on the SQLite test profile;
  `RELEASE-CHECKLIST.md` Â§12â€“13 is the outstanding runbook step.

## Remaining unblocked workstreams (ranked)

1. **Replicate the edit flow** to remaining master-data entities (products,
   materials, companies, sites, employees, work centers, machines, warehousesâ€¦)
   using `PartnerEditPage` as the pattern; each gets a PATCH contract test.
3. **Detail/edit polish for the small entities** flagged Â¹ above, if desired.
4. Everything else requires the business decisions above.
