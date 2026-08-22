# Procurement Foundation — Requisitions & Purchase Orders (Task 009)

Procurement owns **the commercial documents that commit the company to buy
materials**. Task 009 ships the first, deliberately un-gated slice of that
domain: the internal `PurchaseRequisition` (PR) and the supplier-facing
`PurchaseOrder` (PO), each a header + lines document driven by an explicit
**status state machine** enforced server-side. It is the sixth business module
and reuses the platform's soft-delete base, audited write path, company scoping
and RBAC without introducing any new mechanism.

## Scope discipline

The procurement domain's *value* extends far beyond the two documents: goods
receipt (GRN) and the two-stage temporary→QC→definitive receipt (SR-09, #17),
MRP-driven auto-requisition (#14), RFQ / sourcing, an approval hierarchy with
monetary thresholds (#7), import / foreign-trade / sanctions handling with FX,
supplier invoice / accounts-payable matching (Finance, #23), and inventory
valuation (#1 / #2). **Every one of those is either gated on an open business
decision or belongs to a later phase.** Receipt in particular is bound to the
traceability + stock layer whose highest-priority gate (Q-046, roll
serialization vs. lot+count) must be resolved before that schema can migrate.

So Task 009 follows the same discipline as Tasks 004–008: build the **confirmed
document layer** and defer everything gated. Concretely, it ships the PR→PO
paper trail and its lifecycle transitions, and nothing that would require
inventing an SLZ rule.

### Deliberately NOT built (open gates / later phases)

- **Goods receipt / GRN** and the two-stage temporary→QC→definitive receipt
  (SR-09, #17) — requires the traceability + stock layer gated on Q-046.
- **MRP / auto-requisition** (#14) — no netting, no planned-order explosion.
- **RFQ / sourcing / supplier quotes** and any supplier-selection scoring.
- **Approval hierarchy & monetary thresholds** (#7) — `approve` is a single
  manual, permission-gated transition. **No threshold or routing rule is
  hard-coded**; SLZ's approval matrix is OPEN.
- **Import / foreign trade / sanctions / FX** — `currency` is a plain 3-letter
  code with no conversion; no landed-cost, duty, or LC handling.
- **Supplier invoice / accounts-payable / 3-way match** (Finance, #23).
- **Inventory valuation** from PO pricing (#1 / #2) — `unit_price` is captured
  but never used to value stock.

## Entities

Procurement documents are **transactional documents with a status state
machine** — deliberately *not* the `VersionedRoot`/`Revision` pattern (which
models engineering revisions, not commercial paper). Headers and lines both use
`SoftDeleteModel` to preserve history.

| Model | Base | Key fields | Constraints |
| --- | --- | --- | --- |
| `PurchaseRequisition` | `SoftDeleteModel` | `company` (PROTECT), `site` (nullable PROTECT), `number`, `status`, `requested_by` (nullable, hr.Employee PROTECT), `need_by_date` (nullable), `notes` | `UniqueConstraint(company, number)` → `uq_purchase_requisition_company_number` |
| `PurchaseRequisitionLine` | `SoftDeleteModel` | `requisition` (CASCADE), `sequence`, `material` (PROTECT), `quantity`, `uom` (PROTECT), `notes` | `UniqueConstraint(requisition, sequence)` → `uq_pr_line_requisition_sequence` |
| `PurchaseOrder` | `SoftDeleteModel` | `company` (PROTECT), `site` (nullable PROTECT), `number`, `supplier` (partners.Supplier PROTECT), `status`, `order_date`/`expected_date` (nullable), `currency` (default `IRR`), `notes` | `UniqueConstraint(company, number)` → `uq_purchase_order_company_number` |
| `PurchaseOrderLine` | `SoftDeleteModel` | `order` (CASCADE), `sequence`, `material` (PROTECT), `quantity`, `uom` (PROTECT), `unit_price` (nullable), `requisition_line` (nullable SET_NULL), `notes` | `UniqueConstraint(order, sequence)` → `uq_po_line_order_sequence` |

`status` defaults to `DRAFT` (`db_index`); `unit_price` is nullable with **no
invented pricing rule**; the optional `requisition_line` link lets a PO line
trace back to the PR line it fulfils without enforcing any coverage rule.
Master-data FKs use `PROTECT`; each child line `CASCADE`s with its header.

## Status state machines (server-authoritative)

The transitions live in `apps/procurement/services.py`
(`transition(...)`), which rejects any move whose source status is not in the
allowed set with `ConflictError(code="invalid_status_transition")` (HTTP `409`)
and, on success, updates `status` under `atomic_with_events` and emits
`EntityUpdated(changes={"status": ...})` so the change is **audited**.

**Requisition** (`PurchaseRequisitionStatus`):

- `DRAFT → SUBMITTED` (`submit`)
- `SUBMITTED → APPROVED` (`approve`)
- `SUBMITTED → REJECTED` (`reject`)
- `DRAFT | SUBMITTED | APPROVED → CANCELLED` (`cancel`)

**Purchase order** (`PurchaseOrderStatus`, truncated before goods receipt):

- `DRAFT → APPROVED` (`approve`)
- `APPROVED → SENT` (`send`)
- `SENT → CLOSED` (`close`)
- `DRAFT | APPROVED | SENT → CANCELLED` (`cancel`)

Both documents are **editable only while `DRAFT`**: header update/destroy and
every line write pass through `assert_document_editable`, which raises
`ConflictError(code="document_not_editable")` (HTTP `409`) once the header has
left `DRAFT`.

## Reused mechanisms (nothing new)

- **Audited write path** — all four viewsets extend `AuditedModelViewSet`;
  creates, updates and deletes emit domain events, so the audit subscriber
  records `CREATE` / `UPDATE` / `DELETE` with `entity_type`
  `procurement.PurchaseRequisition`, `procurement.PurchaseRequisitionLine`,
  `procurement.PurchaseOrder`, `procurement.PurchaseOrderLine`. Status
  transitions emit `EntityUpdated` (not the audit-ignored `EntityApproved`), so
  every lifecycle move is captured.
- **Editability guard** — header and line writes call
  `assert_document_editable`, raising `ConflictError` (`document_not_editable`,
  HTTP `409`) against a non-DRAFT document.
- **RBAC** — four permissions (`procurement.requisition.view|manage`,
  `procurement.order.view|manage`) seeded in `seed_rbac.py`; enforced by
  `HasPermission` via each viewset's `permission_map` / `required_permission`.
  The `@action` transition endpoints require the POST→`manage` permission.
- **Duplicate rejection** — the non-conditional `UniqueConstraint(company,
  number)` surfaces as a DRF validator returning `400` on a duplicate document
  number within a company.

## API surface

Under `/api/v1/procurement/`:

- `GET/POST /requisitions/`, `GET/PUT/PATCH/DELETE /requisitions/{id}/`, plus
  `POST {id}/submit|approve|reject|cancel/`
- `GET/POST /requisition-lines/`, `GET/PUT/PATCH/DELETE /requisition-lines/{id}/`
- `GET/POST /orders/`, `GET/PUT/PATCH/DELETE /orders/{id}/`, plus
  `POST {id}/approve|send|close|cancel/`
- `GET/POST /order-lines/`, `GET/PUT/PATCH/DELETE /order-lines/{id}/`

Requisitions filter on `company` / `site` / `status` / `requested_by`; orders on
`company` / `site` / `supplier` / `status`; both search `number` / `notes`.

## Frontend

- `api/procurement.ts` — typed `PurchaseRequisition` / `PurchaseOrder` shapes,
  the `PurchaseRequisitionStatus` / `PurchaseOrderStatus` unions,
  `createPurchaseRequisition` / `createPurchaseOrder`, and
  `transitionRequisition` / `transitionOrder` (action name → endpoint).
- `pages/procurement/` — `PurchaseRequisitionsPage` and `PurchaseOrdersPage`
  browse each collection and render **contextual transition buttons** per the
  current status (visible to a user with `manage`); `PurchaseRequisitionCreatePage`
  and `PurchaseOrderCreatePage` are the audited create forms. The PO form joins
  `/partners/suppliers/` to `/partners/partners/` on the partner id to render a
  readable supplier label, because the supplier serializer exposes no name.
- The status→actions maps in the browse pages mirror the server state machine
  **for display only**; the backend is the authority and rejects any illegal
  move with `409`. Routes under `/procurement/*` and sidebar entries are each
  gated by the matching view permission.

## Verification status

The backend source is `py_compile`-clean and mirrors the established Task
006–008 patterns; both locale bundles parse as valid JSON with matching
`procurement` key sets. Runtime verification was **not** possible in the
authoring sandbox (no PostgreSQL / package installs). Before relying on this
module, run in a proper environment: `python manage.py makemigrations
procurement && migrate`, `python manage.py seed_rbac` (to load the four new
permissions), `python manage.py test apps.procurement`, and the frontend
`npm run build` / `vitest`.
