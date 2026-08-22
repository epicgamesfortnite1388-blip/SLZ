# Data Lifecycle

How records are created, changed, retired, and traced across the platform.

## Creation & change tracking

Models built on `AuthoredModel` / `BaseModel` capture `created_by` /
`updated_by` and `created_at` / `updated_at` automatically. The acting user is
resolved from the request context (see correlation & context below). Every
create/update/delete of interest also produces:

1. a **domain event** on the bus, and
2. an **audit-log** entry (via the audit subscriber).

## Soft delete — opt-in, not universal

Soft delete is available through `SoftDeleteModel` but is applied **only where
retention matters** (e.g. documents, organizational structure). Applying it
blindly everywhere is an explicit anti-goal.

Semantics (`apps/core/managers.py`, `models.py`):

- `SoftDeleteModel.delete()` sets `deleted_at` (does **not** remove the row).
- `objects` (`AliveManager`) returns only rows with `deleted_at IS NULL`;
  soft-deleted rows are invisible to normal queries and thus resolve as
  `404 / NotFoundError`.
- `all_objects` (`AllObjectsManager`) sees everything, alive and dead.
- `hard_delete()` permanently removes the row.
- `restore()` clears `deleted_at`.

Models that should be permanently deleted simply do **not** extend
`SoftDeleteModel`.

## Audit trail — generic and module-independent

`apps/audit` records a uniform trail for any entity without knowing that
entity's type:

```
AuditLog(
  actor, action, entity_type, entity_id,
  before (JSON), after (JSON),
  correlation_id, metadata, created_at
)
```

Actions: `CREATE`, `UPDATE`, `DELETE`, `APPROVE`, `REJECT`, `CANCEL`,
`LOGIN`, `LOGOUT`.

The audit app **subscribes to the event bus** (`EntityCreated/Updated/Deleted`)
and serializes instances generically, so a new module gets audit coverage for
free the moment it publishes standard events. Auth flows record `LOGIN` /
`LOGOUT` directly; workflow records `APPROVE` / `REJECT` / `CANCEL`.

Audit is **append-only**: entries are never edited or deleted through the API,
and the audit viewset is read-only and permission-gated
(`audit.log.view`).

## Correlation & acting-user context

`CorrelationIdMiddleware` (`apps/core/middleware.py`) stores the correlation ID
and current user id in `contextvars` for the duration of the request. This lets
services and the audit layer attach the correlation ID and actor **without
threading the request object through every function**. The same ID appears in
logs, audit rows, and the error/response envelope, giving one thread to follow
a request across the stack.

## Retirement patterns

| Pattern            | Use when …                                              |
|--------------------|---------------------------------------------------------|
| Soft delete        | The record may need to be seen/restored; history matters |
| Hard delete        | Truly transient data with no retention value             |
| Status / lifecycle | The entity is retired but kept (e.g. `is_active=False`, or a versioned root superseded by a new revision — see [versioning.md](versioning.md)) |

Prefer status transitions over deletion for master data referenced by history.

## Events observe only committed state

Domain events publish **after** the database transaction commits (see
[transactions.md](transactions.md)), so audit entries and notifications never
reflect changes that were rolled back.
