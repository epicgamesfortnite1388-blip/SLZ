# SLZ ERP — Implementation Gap Matrix

Generated 2026-08-22 from direct repository inspection (not from status
documents). Statuses:

- **VERIFIED** — implemented and exercised by the executed test suites this cycle.
- **PARTIAL** — implemented; known unblocked gaps remain (listed).
- **GATED** — blocked by an unresolved SLZ decision (gate listed).
- **NOT STARTED** — deliberately out of scope so far.

Legend: BE = backend · API = REST surface · FE = frontend · T = tests · AUD =
audit coverage · RBAC = permission enforcement · LOC = en/fa parity.

## Platform foundation

| Requirement | BE | API | FE | T | AUD | RBAC | LOC | Status |
|---|---|---|---|---|---|---|---|---|
| Identity/JWT login-refresh-logout-throttle | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | VERIFIED |
| Self-profile (`/auth/me/`) validated updates | ✔ | ✔ | ✔ | ✔ | ✔ | n/a | ✔ | VERIFIED |
| RBAC roles/permissions/seed catalogue | ✔ | ✔ | partial¹ | ✔ | ✔ | ✔ | ✔ | VERIFIED |
| Company/Site masters + UI | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | VERIFIED |
| Department/SiteCapability + UI | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | VERIFIED |
| Audit trail + snapshots + viewer + diff modal | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | VERIFIED |
| Documents register + panels + policy tests | ✔ | ✔ | ✔ | ✔ | ✔ | ✔² | ✔ | VERIFIED |
| Localization utilities (Jalali/dual-calendar) | ✔ | ✔ | display³ | ✔ | n/a | n/a | ✔ | PARTIAL |
| Notifications inbox + bell | ✔ | ✔ | ✔ | ✔ | n/a | self-scope | ✔ | VERIFIED |
| Workflow engine + approvals inbox + definitions admin | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | VERIFIED |

¹ Role management UI absent (API complete) — minor unblocked gap.
² Upload authorization policy = "any viewer may upload" is documented design;
per-entity attachment policy GATED (no gate ID assigned — needs business input).
³ Jalali *display* shipped (`i18n/dates.ts`); Jalali **input** convention GATED
(needs confirmed convention).

## Domain modules (confirmed definition layer)

| Module | Confirmed layer built | Unblocked gaps remaining | Gated remainder | Status |
|---|---|---|---|---|
| partners | Partner/Customer/Supplier/Contact/Address + detail page + attachments | Contact/Address list UIs inside partner detail | – | PARTIAL→near complete |
| catalog | UoM+conversions, product taxonomy, Product, Material + create pages | Material/product detail pages; conversions UI | Coding scheme Q-019 | PARTIAL |
| hr | Employee master + list/create/detail | – | Role catalogue Q-053 | VERIFIED (layer) |
| engineering | CustomerProduct + spec revisions chain + tooling assets, detail page w/ revisions+layers+colors+params | Tooling detail page | Cost model Q-004/036; trigger rule Q-024 | PARTIAL |
| manufacturing | WorkCenter/Machine/BOM/Routing masters + versioned roots + create forms | BOM/routing detail views; operations/lines UI in detail | Consumption bases Q-027/Q-016/042; templates Q-029 | PARTIAL |
| inventory | Warehouse master + per-user access grants + detail page | Kardex-style read-only views impossible pre-Q-046 | Stock/movements/lots Q-046 cluster | PARTIAL |
| quality | Characteristic catalogue + versioned QualityPlan (+create) | Plan detail view w/ items | Execution/NCR/sampling Q-039/040/043/044 | PARTIAL |
| procurement | Requisition/PO header+line + state machine + detail pages + order-book summary | Supplier performance reporting (needs defined metrics) | GRN/MRP/thresholds/invoice-match #7/#14/#17/#23, Q-034 | PARTIAL |
| sales | SO header+line + state machine + detail page + order-book summary | Pricing/proforma shapes (data-only fields exist) | Pricing/ATP/allocation/shipment/invoice #11/#12/#18, Q-046 | PARTIAL |
| production | ProductionOrder frozen-definition document + detail page + summary | Planning board (manual) | All execution semantics Q-046 cluster | PARTIAL |
| reporting | Dashboard counts + order-book breakdowns | Cross-module operational summaries (safe) | KPI/profitability Q-038 | PARTIAL |
| execution layer | – | – | stock/GRN/issue/genealogy/QC-exec/allocation/shipment | GATED Q-026/046/048/049 |

## Cross-cutting gates

| Gate | Blocks | Severity if forced into production today |
|---|---|---|
| Q-055/Q-053 (scoping + role catalogue) | row-level company isolation on every domain queryset | CRITICAL — system is single-tenant-open |
| Q-046 (+048/049/026) | entire execution/traceability layer | blocks MES go-live |
| Q-034/Q-031/Q-033 | costing/valuation | blocks financial accuracy features |
| DR-000/NQ-001 | build-vs-buy reaffirmation | program-level risk |

## Infrastructure

PostgreSQL/Docker end-to-end verification **NOT EXECUTED** (no Docker on the
dev machine). SQLite suite green does not certify Postgres behavior (constraints,
JSONField semantics, concurrency).
