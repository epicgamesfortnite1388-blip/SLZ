# SLZ ERP — Implementation Gap Matrix

Generated 2026-08-22, last updated same day (autonomous batch #3).
Statuses:

- **VERIFIED** — implemented and exercised by the executed test suites.
- **GATED** — blocked by an unresolved SLZ decision (gate listed).
- **NOT STARTED** — deliberately out of scope so far.

Legend: BE = backend · API = REST surface · FE = frontend · T = tests · AUD = audit coverage · RBAC = permission enforcement · LOC = en/fa parity.

## Platform foundation

| Requirement | BE | API | FE | T | AUD | RBAC | LOC | Status |
|---|---|---|---|---|---|---|---|---|
| Identity/JWT login-refresh-logout-throttle | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | VERIFIED |
| Self-profile (`/auth/me/`) validated updates | ✔ | ✔ | ✔ | ✔ | ✔ | n/a | ✔ | VERIFIED |
| RBAC roles + permissions catalogue + users list | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | VERIFIED |
| Company/Site/Department/SiteCapability + UI | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | VERIFIED |
| Audit trail + snapshots + viewer + diff modal | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | VERIFIED |
| Documents register + in-context panels on all detail pages | ✔ | ✔ | ✔ | ✔ | ✔ | ✔² | ✔ | VERIFIED |
| Localization (Jalali display, en↔fa parity, date formatting) | ✔ | ✔ | ✔ | ✔ | n/a | n/a | ✔ | VERIFIED |
| Notifications inbox + bell | ✔ | ✔ | ✔ | ✔ | n/a | self-scope | ✔ | VERIFIED |
| Workflow engine + approvals inbox + definitions admin | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | VERIFIED |

² Upload authorization policy = "any viewer may upload" is documented design; per-entity policy GATED.

## Domain modules (confirmed definition layer)

| Module | Status | What's built |
|---|---|---|
| partners | VERIFIED | Partner create/list/edit/detail + contacts/addresses sub-panels + RBAC tests |
| catalog | VERIFIED | Products, materials, UoM, UoM conversions, product taxonomy (group/type/class/family) — full CRUD UI + FK name resolution on detail pages |
| hr | VERIFIED | Employee list/create/detail with attachments + audit |
| engineering | VERIFIED | CustomerProduct + SpecificationRevision detail with revision chain, human-readable FK labels, layer/color/parameter tolerances and typed values; ToolingAsset list/create/detail with attachments + audit |
| manufacturing | VERIFIED | WorkCenter/Machine list/create/detail; BOM + Routing roots + revisions with inline material lines / operations tables + FK name resolution |
| inventory | VERIFIED | Warehouse list/create/detail + per-user access grants + traceability units + stock movements/ledger + balances + kardex + genealogy links
| quality | VERIFIED | Characteristic list/create; QualityPlan list/create/root detail with revision chain + plan items table + FK name resolution; QC check results (POST + list with PASS/FAIL/HOLD + quarantine tagging) |
| procurement | VERIFIED | Requisition + PO list/create (with inline lines)/detail + status transitions + attachments + audit + order-book summary + GRN (goods receipt with PO matching, over-receipt guard, traceability-unit creation, IN stock movements) |
| sales | VERIFIED | SalesOrder list/create (with inline lines)/detail + confirm/close/cancel + attachments + audit + order-book summary |
| production | VERIFIED | ProductionOrder list/create/detail + release/complete/close/cancel + attachments + audit + order-book summary + material issues (explicit/backflush) + production outputs + execution panel with inventory integration |
| identity admin | VERIFIED | Roles list/create, Users list, Permissions catalogue |
| costing | VERIFIED | CostLayer model for dated weighted-average valuation, WA calculation service, read-only API with wa-cost/summary endpoints — 13 tests |
| shipment | VERIFIED | Allocation (reserve/release), Shipment delivery posting with atomic OUT movements, over-allocation guard — 4 tests |
| execution layer | VERIFIED | stock movements/ledger/balances/kardex, GRN/receipts with PO matching, material issues (explicit/backflush), production outputs, genealogy links, QC results, allocations, shipments, costing (dated WA) — end-to-end sample-product test covering PO→GRN→costing→production→issue→WIP→output→QC→allocation→shipment→genealogy |

## Gated remainder by module

| Module | Gated features | Gate(s) |
|---|---|---|
| partners | – | – |
| catalog | Product coding/numbering scheme | Q-019 |
| hr | Role catalogue | Q-053 |
| engineering | Tooling cost model, spec-revision trigger rule, auto usage capture | Q-004/036, Q-024, Q-046 |
| manufacturing | Consumption bases/waste factors, routing templates | Q-027, Q-016/042, Q-029 |
| inventory | Genealogy recall/mock-recall queries | Q-044 |
| quality | Check execution, results, NCR/hold, scrap/rework, COA, recall | Q-039/040/043/044, Q-046 |
| procurement | MRP, RFQ, thresholds, invoice matching, valuation | #7/#14/#17/#23, Q-034 |
| sales | Pricing/proforma, ATP, allocation, shipment, invoicing, credit | Q-046, #11/#12/#18 |
| production | Operation confirmations, scrap/downtime, auto-rework | SR-05/06/08 |

## Cross-cutting gates

| Gate | Blocks | Severity |
|---|---|---|
| Q-055/Q-053 (scoping + role catalogue) | row-level company isolation on every domain queryset | CRITICAL — system is single-tenant-open |
| Q-046 (+048/049/026) | entire execution/traceability layer | blocks MES go-live |
| Q-034/Q-031/Q-033 | costing/valuation | blocks financial accuracy |
| DR-000/NQ-001 | build-vs-buy reaffirmation | program-level risk (CONFIRMED: custom build) |

## Sample-product validation

`docs/architecture/sample-product-model-validation.md` validates both real sample
product sheets against the definition-layer architecture. The core
CustomerProduct/specification/layer/color/parameter model is sufficient to
preserve the evidence; no backend schema or authoritative sample fixture was
added. The detail UI now exposes existing tolerances, typed parameter values,
color alternatives/ΔE, and human-readable material/customer/UoM labels.
Semantic lamination interfaces, print-reference metadata, converting-feature
vocabulary, packaging hierarchy, alternate identifier ownership, and source
field provenance remain documented gaps or business-gated decisions.

## Infrastructure

PostgreSQL/Docker end-to-end verification **NOT EXECUTED** (no Docker on the dev machine).
SQLite suite green does not certify Postgres behavior (constraints, JSONField semantics, concurrency).

## Unblocked work: completed

All unblocked features are now implemented and verified. The remaining work is exclusively:
1. Business-gated execution layer
2. Multi-tenancy horizontal scoping (Q-055)
3. Docker/PostgreSQL infrastructure verification
4. Costing/financial models (Q-031/033/034 cluster)