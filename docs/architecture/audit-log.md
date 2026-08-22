# Audit Log (viewer)

The `audit` app records an **append-only** trail of every audited action across
the platform. The mechanism — how entries are written (the domain-event
subscriber and explicit `record_audit` calls), correlation IDs and before/after
capture — is described in [data-lifecycle.md](data-lifecycle.md). This document
covers the **read API and its viewer**, the compliance surface SLZ relies on for
traceability.

## Read-only by construction

There is no create/update/delete path over the wire. `AuditLogViewSet` exposes
**list + retrieve only**, gated by a single permission `audit.log.view` (seeded
in `seed_rbac`). Entries are never edited or removed through the API; the trail's
value is that it cannot be rewritten from the application.

## API surface

Under `/api/v1/audit/logs/`:

- `GET logs/` — the paginated trail (newest first; the model orders by
  `-timestamp`). Server-side filters: `action`, `entity_type`, `entity_id`,
  `actor`, `correlation_id`. Free-text `search` spans `entity_type`,
  `entity_id`, `actor_label`. Orderable by `timestamp` / `action`.
- `GET logs/{id}/` — one entry with its full `before_state` / `after_state`
  JSON, `correlation_id` and `metadata`.

`actor_label` is denormalized on write, so the acting identity survives even if
the user record is later removed (`actor` FK is `SET_NULL`).

## Frontend

An **Audit log** screen (`/audit/logs`, sidebar entry shown only to holders of
`audit.log.view`) lists the trail through the standard `CollectionView`. Columns:
timestamp, actor, action (localized), the generic entity reference
(`entity_type #entity_id`) and correlation id. The search box maps to the
backend `search_fields`, so an operator can trace every recorded action on one
record by typing its type or id.

**Entry detail.** Clicking a row opens a read-only modal (`AuditEntryDetail`)
that retrieves the full entry via `fetchAuditEntry(id)` and renders the
who / what / when summary plus the recorded state: a field-level
**before → after diff table** (union of both snapshot keys, changed rows
highlighted). CREATE entries carry their state on the "After" side, DELETE
entries on the "Before" side; entries with no snapshots render an explicit
"no state recorded" note. No write affordance exists anywhere in the UI.

## Deliberately NOT built

- Any mutation of audit rows (by design — append-only).
- Export / e-signature / tamper-evidence hashing — not a confirmed requirement.
- Full-table dumps in snapshots: `model_to_dict` covers editable fields only;
  identity/timestamps live in dedicated columns (`entity_id`, `timestamp`).

## Verification status

RUNTIME VERIFIED (2026-08-22). State capture is exercised end-to-end by
`apps.audit.tests.test_audit.AuditStateSnapshotTests` through the real service
layer, and the detail modal by component tests (`AuditEntryDetail.test.tsx`).
