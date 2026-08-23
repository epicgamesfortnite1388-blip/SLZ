# SLZ ERP — Implementation Gap Matrix

**Generated:** 2026-08-22. **Updated:** 2026-08-23 (final hardening — master audit).
Statuses:

- **VERIFIED** — implemented, tested, typechecked, linted, built green.
- **GATED** — blocked by unresolved SLZ decision.
- **NOT STARTED** — deliberately out of scope so far.

---

## Platform foundation

| Requirement | Status |
|---|---|
| Identity/JWT login-refresh-logout-throttle | VERIFIED |
| Self-profile (`/auth/me/`) validated updates | VERIFIED |
| RBAC roles + permissions catalogue + users list | VERIFIED |
| Company/Site/Department/SiteCapability + UI | VERIFIED |
| Audit trail + snapshots + viewer + diff + company scoping (Q-055) | VERIFIED |
| Documents register + in-context panels on all detail pages | VERIFIED |
| Localization (Jalali display, en↔fa 100% parity) | VERIFIED |
| Notifications inbox + bell | VERIFIED |
| Workflow engine + approvals inbox + definitions admin | VERIFIED |

---

## Domain modules — execution layer (all VERIFIED following Q-046/Q-048/Q-049/Q-026 answers)

| Module | What's built |
|---|---|
| **partners** | Partner CRUD + contacts/addresses + customer/supplier profiles |
| **catalog** | Products, materials, UoM, conversions, taxonomy (group/type/class/family) |
| **hr** | Employee list/create/detail |
| **engineering** | CustomerProduct + SpecificationRevision + revision chain + layers/colors/params + ToolingAsset lifecycle |
| **manufacturing** | WorkCenter/Machine + BOM/Routing roots + revisions + inline lines/operations |
| **inventory** | Warehouse + access + traceability units (BATCH/ROLL/CARTON/PALLET) + movements/balances/kardex + genealogy (forward/backward) |
| **quality** | Characteristics + versioned plans + QC check results (PASS/FAIL/HOLD per Q-046) |
| **procurement** | PR/PO + GRN (PO matching, over-receipt guard, traceability creation, IN movements, costing) |
| **sales** | SalesOrder (confirm/close/cancel) |
| **production** | ProductionOrder + MaterialIssue (EXPLICIT/BACKFLUSH per Q-048) + ProductionOutput (WIP per Q-026) + ExecutionCenter |
| **costing** | Dated weighted-average engine, RECEIPT + ISSUE layers, cost_summary (bulk-optimized), 13 tests |
| **shipment** | Allocation (reserve/release + over-allocation guard + select_for_update) + delivery (OUT movements + genealogy) |

---

## Sample-product integration tests

8 end-to-end tests in `test_sample_product_lifecycle.py` tracing both sample products:
`PO → GRN → traceability → warehouse → production → material issue → WIP → output → QC → allocation → shipment → genealogy`

All pass on SQLite.

---

## Remaining gated features

| Gate | Blocks | Severity |
|---|---|---|
| Docker daemon | PostgreSQL/Redis/Celery container verification | Infrastructure — blocks deployment verification |
| Q-034 | MRP/reorder logic, cost rates | Low — costing architecture supports it |
| Q-044 | Recall automation | Low — genealogy model supports it |
| Q-047 | Bin tracking | Low — not addressed |
| DR-008 | Email/SMS push notifications | Low — in-app notifications work |
| Q-019 | Product coding scheme | Low — manual codes work |

---

## Infrastructure

PostgreSQL/Docker end-to-end verification **NOT EXECUTED** (no Docker on dev machine).
All application logic verified on SQLite (312 backend + 90 frontend tests).
Dockerfiles, nginx, compose, entrypoint, healthchecks statically audited — no defects found.

---

## Summary

**All confirmed business decisions are implemented.** The execution layer is complete
and tested. Multi-tenancy is enforced server-side. Frontend is polished with consistent
UX, 100% i18n parity, permission gates, and loading/empty/error states on all pages.

The only remaining work before alpha deployment is Docker daemon verification
(container build against PostgreSQL, Redis, Celery) — which is an infrastructure
requirement, not an application gap.