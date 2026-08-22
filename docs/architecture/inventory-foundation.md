# Inventory Foundation — Warehouses & Access (Task 007)

Inventory owns **where stock lives and who may touch it**. Task 007 ships the
first, deliberately minimal slice of that domain: the `Warehouse` master (with
the SR-10 special store types) and the per-user `WarehouseAccess` grant. It is
the fourth business module and reuses the platform's audited write path,
company/site scoping, and RBAC without introducing any new mechanism.

## Scope discipline

The inventory domain's *value* is transactional — stock movements, a kardex,
lot/roll/batch identity, genealogy, two-stage receipt, reservations, and
consumption. Almost all of that is **gated on open business decisions** (see
below), and the highest-priority gate (Q-046, roll serialization vs. lot+count)
must be resolved before the traceability schema can even be migrated (C-003).
Building the transactional layer now would mean inventing unresolved SLZ rules.

So Task 007 follows the same discipline as Tasks 004/006: build the **confirmed
master data** and defer everything gated. Concretely, it ships:

- `Warehouse` — a company-scoped, optionally site-pinned storage location with a
  `store_type` drawn from the SR-10 special store types (raw material, WIP,
  finished goods, scrap, quarantine, cliché/plates, line-side, consignment,
  stagnant/slow-moving, shipping staging, returns, plus a general default).
  `code` is unique per company; `is_active` supports soft retirement and the
  record is soft-deletable.
- `WarehouseAccess` — an explicit grant binding one user to one warehouse at an
  `access_level` of `VIEW` or `OPERATE` (SR-10's per-user warehouse access
  mechanism). Unique per (warehouse, user).

### Deliberately NOT built (open gates)

Recorded in `docs/requirements/do-not-build-yet.md`; each depends on a business
decision that is still open:

- **Lot / roll / batch identity, serialization, and genealogy** (Q-046, #18).
  This is the highest-priority gate — C-003 forbids migrating the traceability
  schema until roll serialization vs. lot+count is decided. No stock-identity
  model, no genealogy edge, nothing.
- **Stock movements & the kardex / stock ledger** — no `StockMovement`,
  balance, or ledger model. There is no on-hand quantity anywhere in Task 007.
- **Two-stage goods receipt** (SR-09) and **quarantine→release** flow — the
  `QUARANTINE` store *type* exists as data, but no receipt/inspection/release
  transaction is implemented.
- **Reservations / allocations**, **consumption permit**, and the **issue
  method** (FIFO/LIFO/FEFO/…) (Q-048/#21, Q-051 FEFO/#16).
- **Inventoried BOM levels / stocking granularity** (Q-026/#19, Q-049/#20) and
  **recall** (#31).
- **Location / Zone / bin sub-structure** — deferred because Q-047 (whether
  bin-level tracking is even required) is open. A `Warehouse` is the finest
  storage grain in this slice.

## Entities

| Model | Base | Key fields | Constraints |
| --- | --- | --- | --- |
| `Warehouse` | `SoftDeleteModel` | `company` (PROTECT), `site` (nullable, PROTECT), `code`, `name_fa`, `name_en`, `store_type`, `is_active`, `notes` | `UniqueConstraint(company, code)` → `uq_warehouse_company_code` |
| `WarehouseAccess` | `BaseModel` | `warehouse` (CASCADE), `user` (CASCADE), `access_level` | `UniqueConstraint(warehouse, user)` → `uq_warehouse_access_wh_user` |

`store_type` defaults to `GENERAL`; `access_level` defaults to `VIEW`. Master-data
FKs use `PROTECT` (a warehouse pins its company/site); the child grant `CASCADE`s
with its warehouse and user. `name_fa` is required, `name_en` optional.

## Reused mechanisms (nothing new)

- **Audited write path** — both viewsets extend `AuditedModelViewSet`; creates
  and updates emit domain events, so the audit subscriber records
  `CREATE`/`UPDATE`/`DELETE` with `entity_type` `inventory.Warehouse` and
  `inventory.WarehouseAccess`. No bespoke service layer is needed because the
  gated transactional operations that would justify one are not built.
- **RBAC** — four permissions (`inventory.warehouse.view|manage`,
  `inventory.warehouseaccess.view|manage`) seeded in `seed_rbac.py`; enforced by
  `HasPermission` via each viewset's `permission_map` / `required_permission`.
- **Duplicate rejection** — the non-conditional `UniqueConstraint`s surface as
  DRF validators returning `400` on duplicate code / duplicate grant.
- **API/UI conventions** — standard pagination, filtering (`company`, `site`,
  `store_type`, `is_active` for warehouses; `warehouse`, `user`, `access_level`
  for grants), search, the fa/en + RTL/LTR frontend, and `ProtectedRoute`
  permission gating — all identical to the master-data and manufacturing
  modules.

## API surface

Under `/api/v1/inventory/`:

- `GET/POST /warehouses/`, `GET/PUT/PATCH/DELETE /warehouses/{id}/`
- `GET/POST /warehouse-access/`, `GET/PUT/PATCH/DELETE /warehouse-access/{id}/`

## Frontend

- `api/inventory.ts` — typed `Warehouse` / `WarehouseAccess` shapes, the SR-10
  `WarehouseStoreType` union + `WAREHOUSE_STORE_TYPES` list, and `createWarehouse`.
- `pages/inventory/` — `WarehousesPage` (browse + create action), a
  `WarehouseCreatePage` write form (the representative audited path, with a
  store-type select), and a read-only `WarehouseAccessPage` browse.
- Routes under `/inventory/*` and sidebar entries, each gated by the matching
  view permission.
