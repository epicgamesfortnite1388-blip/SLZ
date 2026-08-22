# Execution & Traceability — Confirmed Foundation

**Status: FOUNDATION IMPLEMENTED.** SLZ has confirmed the Q-046/Q-048/Q-049/Q-026
cluster. This document records the resulting boundary and the execution slice
now present in code. It does not expand the decisions beyond the reply in
`docs/Replied business-decision-package.md`.

## Confirmed policy

| Gate | Confirmed rule | Code boundary |
|---|---|---|
| Q-046 | Rolls are serialized physical entities; QC is expected per produced reel | `inventory.TraceabilityUnit` with `ROLL` identity and roll dimensions |
| Q-048 | Mixed by process: film production may backflush; printing, lamination, slitting, and sealing use explicit issue | `manufacturing.RoutingOperation.issue_method`, copied onto each `production.MaterialIssue` |
| Q-049 | Film uses roll/pallet tracking; cartonized bags/pouches use carton tracking; purchased PE granules use batch tracking | Material/customer-product traceability modes plus pallet parent handling units |
| Q-026 | Production stages create stocked WIP for later conversion | `catalog.Material` supports `SEMI_FINISHED`; BOM `output_material` and production outputs identify staged stock |

## Implemented entities

### `inventory.TraceabilityUnit`

A company-scoped, uniquely identified handling unit. It preserves material or
customer-product provenance, unit type, quantity/UoM, roll dimensions (`weight`,
`length`, `width`, `core`), notes, and an optional parent. Material and product
traceability modes reject incompatible non-pallet unit types. Pallets are explicit
parent units; the system does not infer pallet contents or quantities.

Supported unit types:

- `BATCH` — purchased bulk/raw-material identity such as PE granules.
- `ROLL` — serialized film identity.
- `CARTON` — cartonized bag/pouch identity.
- `PALLET` — handling parent for film rolls or other confirmed packed units.

### `inventory.StockMovement`

Append-only movement rows hold company, warehouse, optional unit/material,
direction, quantity, UoM, and a UUID reference to the source execution record.
Material issues and production outputs create the corresponding `OUT`/`IN`
movement atomically. No on-hand balance, valuation, reservation, or correction
policy is inferred; balances remain derived/reporting work.

### `inventory.GenealogyLink`

Append-only parent→child links preserve company-local genealogy and optional
production-order/operation provenance. The model rejects cross-company and
self-links. Full recall traversal and quality disposition are not implemented.

### `production.MaterialIssue` and `production.ProductionOutput`

Both are immutable execution records. A material issue requires a `RELEASED`
production order, a warehouse, material, quantity, UoM, and method. `EXPLICIT`
requires a selected traceability unit; `BACKFLUSH` identifies material without a
selected unit. Each write posts an append-only stock movement in the same
transaction and emits audited domain events. A production output requires a
produced traceability unit and posts an `IN` movement.

### Operation-level mixed issue configuration

`manufacturing.RoutingOperation.issue_method` is nullable configuration. It is
not populated by process-name matching. When an issue includes a routing
operation UUID, the selected method must match that operation's configured
method. This preserves the confirmed process distinction without inventing a
universal rule or a process vocabulary.

## API surface

Under `/api/v1/inventory/`:

- `GET/POST /traceability-units/`
- `GET/POST /genealogy-links/`
- `GET/POST /movements/` (updates/deletes rejected as append-only)
- Existing warehouse and warehouse-access endpoints remain unchanged.

Under `/api/v1/production/`:

- `GET/POST /material-issues/` (updates/deletes rejected as append-only)
- `GET/POST /outputs/` (updates/deletes rejected as append-only)
- Existing production-order lifecycle endpoints remain unchanged.

RBAC permissions are `inventory.traceability.view/manage`,
`inventory.movement.view/manage`, and `production.execution.view/manage`.
All mutations use the audited service/event path.

## Frontend

The production-order detail page includes a permission-gated **Traceability and
execution** panel. Users with execution view permission can inspect issues and
outputs. Users with execution manage permission can register units, post
explicit/backflush issues, and post outputs. English and Persian labels are
provided. The UI exposes identifiers and raw UUID fallbacks without pretending
to resolve unknown material/warehouse names.

## Explicitly outside this implementation

The confirmed cluster does not answer or authorize the following work:

- temporary receipt → QC → definitive receipt and quarantine release (SR-09);
- quality check result, NCR, hold, disposition, or per-reel QC workflow (Q-039/Q-040/Q-041/Q-043);
- reservations, availability, allocations, shipment, or delivery;
- inventory valuation, dated weighted-average behavior, or costing formulas;
- barcode/QR/RFID hardware or scanner integration (DR-006);
- formal recall/mock-recall query workflow (Q-044);
- scrap, rework, downtime, operation confirmation, or outsourcing execution;
- bin/location hierarchy (Q-047);
- final role catalogue and company/site policy (Q-053/Q-055).

These remain documented dependencies rather than hidden defaults.

## Verification target

Focused backend tests cover unit-mode validation, pallet parentage, explicit and
backflush issue rules, atomic movement creation, output posting, append-only
protection, and operation method matching. Frontend API tests cover the new
endpoint paths; typecheck/lint/test/build and migration checks must be rerun after
this implementation batch. Docker/PostgreSQL verification remains separate from
SQLite application tests when Docker is unavailable.
