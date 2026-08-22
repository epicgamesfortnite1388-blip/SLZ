# Sales Order Management — Customer Orders (Task 010)

Sales owns **the commercial documents that record what a customer has ordered**.
Task 010 ships the first, deliberately un-gated slice of the sell side: the
customer-facing `SalesOrder` (SO) — a header + lines document driven by an
explicit **status state machine** enforced server-side. It is the sell-side
mirror of Task 009's procurement documents and the **demand origin** for this
made-to-order (MTO) business. It is the seventh business module and reuses the
platform's soft-delete base, audited write path, company scoping and RBAC
without introducing any new mechanism.

## Scope discipline

The sales domain's *value* extends far beyond a confirmed order document: sales
inquiry → quotation / proforma and the **pricing algorithm** (R-14, #11), ATP /
promised-delivery-date calculation from capacity + stock (SR-12, #12),
allocation / reservation / shipment / delivery note / invoicing (which need the
gated stock + traceability layer, Q-046, #18, and Finance, #23/#26), credit
management and settlement terms, over/under-delivery tolerance enforcement
(DR-028), multi-level packaging & marking per order (SR-11, #25), new-vs-repeat
routing to engineering (A-001, #4), and the drawing/proof customer-approval gate
(R-16, #6). **Every one of those is either gated on an open business decision or
belongs to a later phase.**

So Task 010 follows the same discipline as Tasks 004–009: build the **confirmed
document layer** and defer everything gated. Concretely, it ships the SO paper
trail and its lifecycle transitions, and nothing that would require inventing an
SLZ rule.

### Deliberately NOT built (open gates / later phases)

- **Sales inquiry → quotation / proforma** and the **pricing algorithm**
  (R-14, #11) — `unit_price` is a nullable manual field; **no price is derived
  or invented**.
- **ATP / promised delivery date** from capacity + stock (SR-12, #12) —
  `requested_date` records only what the customer *asked for*, never a promise.
- **Allocation / reservation / shipment / delivery note / invoicing** — bound to
  the traceability + stock layer gated on Q-046 (#18) and Finance (#23/#26).
- **Credit management, settlement terms, over/under-delivery tolerance
  enforcement** (DR-028) — the tolerance field on `partners.Customer` is data
  only; no rule reads it here.
- **Multi-level packaging & marking per order** (SR-11, #25), **new-vs-repeat
  routing to engineering** (A-001, #4), and the **drawing/proof customer-approval
  gate** (R-16, #6).

## Entities

Sales orders are **transactional documents with a status state machine** —
deliberately *not* the `VersionedRoot`/`Revision` pattern (which models
engineering revisions, not commercial paper). Header and lines both use
`SoftDeleteModel` to preserve history.

| Model | Base | Key fields | Constraints |
| --- | --- | --- | --- |
| `SalesOrder` | `SoftDeleteModel` | `company` (PROTECT), `site` (nullable PROTECT), `number`, `customer` (partners.Customer PROTECT), `status`, `order_date`/`requested_date` (nullable), `currency` (default `IRR`), `notes` | `UniqueConstraint(company, number)` → `uq_sales_order_company_number` |
| `SalesOrderLine` | `SoftDeleteModel` | `order` (CASCADE), `sequence`, `customer_product` (engineering.CustomerProduct PROTECT), `quantity`, `uom` (PROTECT), `unit_price` (nullable), `notes` | `UniqueConstraint(order, sequence)` → `uq_so_line_order_sequence` |

`status` defaults to `DRAFT` (`db_index`); `number` is a **manual** business
number (auto-numbering / document coding is OPEN, #14); `unit_price` is nullable
with **no invented pricing rule**. The ordered item is an
`engineering.CustomerProduct` — the durable, customer-specific orderable identity
that carries the versioned specification. Master-data FKs use `PROTECT`; the
child line `CASCADE`s with its header. `customer` references `partners.Customer`
(the role extension) to parallel procurement's `partners.Supplier` reference.

## Status state machine (server-authoritative)

The transitions live in `apps/sales/services.py` (`transition(...)`), which
rejects any move whose source status is not in the allowed set with
`ConflictError(code="invalid_status_transition")` (HTTP `409`) and, on success,
updates `status` under `atomic_with_events` and emits
`EntityUpdated(changes={"status": ...})` so the change is **audited**.

**Sales order** (`SalesOrderStatus`, deliberately minimal — fulfilment states
are absent because they belong to the gated stock/production layers):

- `DRAFT → CONFIRMED` (`confirm`) — the accepted customer commitment.
- `CONFIRMED → CLOSED` (`close`) — a manual administrative close.
- `DRAFT | CONFIRMED → CANCELLED` (`cancel`).

The order is **editable only while `DRAFT`**: header update/destroy and every
line write pass through `assert_document_editable`, which raises
`ConflictError(code="document_not_editable")` (HTTP `409`) once the header has
left `DRAFT` (a confirmed order is a commitment). **No approval-hierarchy or
credit gate is encoded** — that policy is OPEN (#7 / Finance).

## Reused mechanisms (nothing new)

- **Audited write path** — both viewsets extend `AuditedModelViewSet`; creates,
  updates and deletes emit domain events, so the audit subscriber records
  `CREATE` / `UPDATE` / `DELETE` with `entity_type` `sales.SalesOrder` and
  `sales.SalesOrderLine`. Status transitions emit `EntityUpdated` (not the
  audit-ignored `EntityApproved`), so every lifecycle move is captured.
- **Editability guard** — header and line writes call `assert_document_editable`,
  raising `ConflictError` (`document_not_editable`, HTTP `409`) against a
  non-DRAFT order.
- **RBAC** — two permissions (`sales.order.view|manage`) seeded in
  `seed_rbac.py`; enforced by `HasPermission` via the viewsets' `permission_map`
  / `required_permission`. The `@action` transition endpoints require the
  POST→`manage` permission.
- **Duplicate rejection** — the non-conditional `UniqueConstraint(company,
  number)` surfaces as a DRF validator returning `400` on a duplicate order
  number within a company.

## API surface

Under `/api/v1/sales/`:

- `GET/POST /orders/`, `GET/PUT/PATCH/DELETE /orders/{id}/`, plus
  `POST {id}/confirm|close|cancel/`
- `GET/POST /order-lines/`, `GET/PUT/PATCH/DELETE /order-lines/{id}/`

Orders filter on `company` / `site` / `customer` / `status` and search
`number` / `notes`; lines filter on `order` / `customer_product`. Router
basenames are `salesorder` / `salesorderline` to avoid a DRF reverse-name
collision with procurement's `order` / `orderline`.

## Frontend

- `api/sales.ts` — typed `SalesOrder` shape, the `SalesOrderStatus` union,
  `createSalesOrder`, and `transitionSalesOrder` (action name → endpoint).
- `pages/sales/` — `SalesOrdersPage` browses the collection and renders
  **contextual transition buttons** per the current status (visible to a user
  with `manage`); `SalesOrderCreatePage` is the audited create form. The form
  joins `/partners/customers/` to `/partners/partners/` on the partner id to
  render a readable customer label, because the customer serializer exposes no
  name.
- The status→actions map in the browse page mirrors the server state machine
  **for display only**; the backend is the authority and rejects any illegal
  move with `409`. Routes under `/sales/*` and the sidebar entry are gated by
  the `sales.order.view` permission.

## Verification status

The backend source is `py_compile`-clean and mirrors the established Task
006–009 patterns; both locale bundles parse as valid JSON with matching `sales`
key sets (17 keys). Runtime verification was **not** possible in the authoring
sandbox (no PostgreSQL / package installs). Before relying on this module, run
in a proper environment: `python manage.py makemigrations sales && migrate`,
`python manage.py seed_rbac` (to load the two new permissions), `python
manage.py test apps.sales`, and the frontend `npm run build` / `vitest`.
