# Stage 3 — State
## Verified baseline facts
- on_hand_quantity(company, warehouse, material) sums the append-only ledger (material-level OK).
- balances() returns grouped rows {warehouse, material, traceability_unit, uom, on_hand}.
- GRN over-receipt = sum(GoodsReceiptLine.po_line) vs po_line.quantity → "incoming" = PO.quantity - received (approved/sent POs).
- ProductionOrder pins customer_product + spec_revision; outputs are rows; open supply = released.planned - sum(outputs).
- Allocation RESERVED = committed/allocated stock (per unit, company-scoped).
- Confirmed SalesOrderLines = open demand (no reservation until shipment allocation).
- GenealogyLink(parent, child, production_order_id) + TraceabilityUnit.parent — directed, company-scoped units.
- ShipmentLine -> traceability_unit -> shipment -> customer (forward trace to customers works).
- seed_rbac: PLATFORM_PERMISSIONS list of (code, en, fa) tuples; drift guards exist.
- Email provider stub exists (NotImplementedError); notify() catches per-provider failures.
- Dashboard = per-module counts + status summaries + recent audit activity (real data).
- Frontend: App.tsx <Routes>; nav in Sidebar; pages per module; i18n fa/en; vitest behavior tests.
- ProductionOrder must be in a RELEASED state to issue/output; outputs post stock.
## Scope decisions
- Locations: ship descriptive WarehouseLocation master CRUD; balance-level location tracking DEFERRED
  (derived ledger would need a new dimension + backfill on all movement paths — destabilizing; documented).
- Planning: suggestions only (no auto PO/MO creation) — human review + existing workflows.
- Exports: reuse module view permission (same module, read-only).
