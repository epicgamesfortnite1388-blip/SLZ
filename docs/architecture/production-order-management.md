# Production Order Management — Work Orders (Task 011)

Production owns **the shop-floor commitment to manufacture**. Task 011 ships the
first, deliberately un-gated slice of the make side: the `ProductionOrder` (a.k.a.
Work Order, WO) — a **header-only** document driven by an explicit **status state
machine** enforced server-side. It is the manufacturing counterpart of Task 009's
purchase order and Task 010's sales order, converting confirmed demand into a
commitment to make a given quantity of a customer product to a **frozen
engineering definition**. It is the eighth business module and reuses the
platform's soft-delete base, audited write path, company scoping and RBAC without
introducing any new mechanism.

## Scope discipline

The production domain's *value* extends far beyond a released work-order document:
material issue / consumption / backflush and **roll/lot genealogy** (SR-08, #19),
operation confirmations with produced/scrap quantity capture and downtime tables
(SR-05 / SR-06, #9 / #12), inline / final **QC results** with auto stop + rework
spawning (SR-06, row 20), **margin-based prioritization** (SR-13), the
**outsourcing execution locus** (SR-14 / DR-043 / NQ-004), and **ATP / capacity
feasibility** scheduling (SR-12 / R-30, #12). **Every one of those is either gated
on an open business decision or belongs to a later phase** — most critically on
**Q-046** (roll serialization vs. lot + count), the highest-priority gate blocking
the traceability + stock + execution layer; C-003 forbids migrating that schema
until it is decided.

So Task 011 follows the same discipline as Tasks 004–010: build the **committed
document layer** and defer everything gated. Concretely, it ships the WO paper
trail and its lifecycle transitions, and nothing that would require inventing an
SLZ rule.

### Deliberately NOT built (open gates / later phases)

- **Material issue / consumption / backflush and roll/lot genealogy** (SR-08,
  #19) — bound to the traceability + stock layer gated on **Q-046** (#18).
- **Operation confirmations, produced / scrap quantity capture, downtime** and
  the allowed-scrap / downtime threshold tables (SR-05 / SR-06, #9 / #12) — no
  execution record exists; `COMPLETED` is a **manual** flag, never derived.
- **Inline / final QC results** and auto stop + rework spawning (SR-06, row 20) —
  the Task 008 quality layer defines plans; results need Q-046.
- **Margin-based prioritization** (SR-13) and the **outsourcing execution locus**
  (SR-14 / DR-043 / NQ-004) — no priority or make-vs-buy rule is invented.
- **ATP / promised date and capacity feasibility** (SR-12 / R-30, #12) —
  `scheduled_start` / `scheduled_end` are plain fields; nothing is computed or
  promised.

## Entities

Production orders are **transactional documents with a status state machine** —
deliberately *not* the `VersionedRoot` / `Revision` pattern (which models
engineering revisions, not shop paper). The order is **header-only**: the material
lines and operations already live on the frozen BOM / Routing revisions, so
duplicating them here as editable order lines would either be redundant or would
be execution tracking (gated).

| Model | Base | Key fields | Constraints |
| --- | --- | --- | --- |
| `ProductionOrder` | `SoftDeleteModel` | `company` (PROTECT), `site` (nullable PROTECT), `number`, `customer_product` (engineering.CustomerProduct PROTECT), `spec_revision` (engineering.SpecificationRevision PROTECT), `bom_revision` (manufacturing.BomRevision nullable PROTECT), `routing_revision` (manufacturing.RoutingRevision nullable PROTECT), `sales_order_line` (sales.SalesOrderLine nullable SET_NULL), `status`, `planned_quantity`, `uom` (PROTECT), `scheduled_start`/`scheduled_end` (nullable), `notes` | `UniqueConstraint(company, number)` → `uq_production_order_company_number` |

`status` defaults to `DRAFT` (`db_index`); `number` is a **manual** business
number (auto-numbering / WO coding is OPEN, #14). The order pins WHAT to make
(`customer_product`), the FROZEN definition it is built to (`spec_revision`;
optional `bom_revision` / `routing_revision`, which may be unresolved at draft
time — Q-026 keeps BOM level OPEN), and HOW MUCH (`planned_quantity` + `uom`).
`sales_order_line` records demand provenance for this made-to-order business and
is `SET_NULL` so the order survives if the source line is later removed (an order
may also be make-to-stock). Master-data / engineering FKs use `PROTECT` — history
is never erased.

## Status state machine (server-authoritative)

The transitions live in `apps/production/services.py` (`transition(...)`), which
rejects any move whose source status is not in the allowed set with
`ConflictError(code="invalid_status_transition")` (HTTP `409`) and, on success,
updates `status` under `atomic_with_events` and emits
`EntityUpdated(changes={"status": ...})` so the change is **audited**.

**Production order** (`ProductionOrderStatus`, deliberately minimal — execution
states such as issued / in-operation / confirmed are absent because they belong to
the gated traceability + stock layer):

- `DRAFT → RELEASED` (`release`) — the authorization to the shop floor.
- `RELEASED → COMPLETED` (`complete`) — a **manual** administrative mark (NOT
  derived from confirmations or produced-quantity roll-ups).
- `COMPLETED → CLOSED` (`close`) — a **manual** administrative close.
- `DRAFT | RELEASED | COMPLETED → CANCELLED` (`cancel`).

The order is **editable only while `DRAFT`**: header update/destroy pass through
`assert_document_editable`, which raises
`ConflictError(code="document_not_editable")` (HTTP `409`) once the order has left
`DRAFT` (a released order is a commitment). **No approval hierarchy, priority or
capacity gate is encoded** — those policies are OPEN (SR-12 / SR-13, #7 / #12).

## Reused mechanisms (nothing new)

- **Audited write path** — the viewset extends `AuditedModelViewSet`; creates,
  updates and deletes emit domain events, so the audit subscriber records
  `CREATE` / `UPDATE` / `DELETE` with `entity_type` `production.ProductionOrder`.
  Status transitions emit `EntityUpdated` (not the audit-ignored `EntityApproved`),
  so every lifecycle move is captured.
- **Editability guard** — header writes call `assert_document_editable`, raising
  `ConflictError` (`document_not_editable`, HTTP `409`) against a non-DRAFT order.
- **RBAC** — two permissions (`production.order.view|manage`) seeded in
  `seed_rbac.py`; enforced by `HasPermission` via the viewset's `permission_map`
  / `required_permission`. The `@action` transition endpoints require the
  POST→`manage` permission.
- **Duplicate rejection** — the non-conditional `UniqueConstraint(company,
  number)` surfaces as a DRF validator returning `400` on a duplicate order
  number within a company.

## API surface

Under `/api/v1/production/`:

- `GET/POST /orders/`, `GET/PUT/PATCH/DELETE /orders/{id}/`, plus
  `POST {id}/release|complete|close|cancel/`

Orders filter on `company` / `site` / `customer_product` / `spec_revision` /
`sales_order_line` / `status` and search `number` / `notes`. The router basename
is `productionorder` to avoid a DRF reverse-name collision with the procurement /
sales `order` basenames.

## Frontend

- `api/production.ts` — typed `ProductionOrder` shape, the `ProductionOrderStatus`
  union, `createProductionOrder`, and `transitionProductionOrder` (action name →
  endpoint).
- `pages/production/` — `ProductionOrdersPage` browses the collection and renders
  **contextual transition buttons** per the current status (visible to a user with
  `manage`); `ProductionOrderCreatePage` is the audited create form. The form
  joins `/engineering/specifications/` to `/engineering/customer-products/` on the
  spec-revision `root` id to render a readable specification label.
- The status→actions map in the browse page mirrors the server state machine **for
  display only**; the backend is the authority and rejects any illegal move with
  `409`. Routes under `/production/*` and the sidebar entry are gated by the
  `production.order.view` permission.

## Verification status

The backend source is `py_compile`-clean and mirrors the established Task 006–010
patterns; both locale bundles parse as valid JSON with matching `production` key
sets (26 keys). Runtime verification was **not** possible in the authoring sandbox
(no PostgreSQL / package installs / TypeScript compiler). Before relying on this
module, run in a proper environment: `python manage.py makemigrations production &&
migrate`, `python manage.py seed_rbac` (to load the two new permissions), `python
manage.py test apps.production`, and the frontend `npm run build` / `vitest`.
