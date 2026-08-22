# Execution-Layer Preparation — Extension Points & Boundary Contracts

**Status: PREPARATION ONLY.** This document maps where the future
execution/traceability layer plugs in and which invariants are already
guaranteed. It deliberately does **not** choose any gated business semantics.

## The gates this document respects

| Gate | Question | What it decides |
|---|---|---|
| Q-046 | Roll serialization vs lot + count | Traceability schema (rolls/lots), genealogy shape |
| Q-048 | Material issue method | Explicit issue vs backflush |
| Q-026 | Inventoried intermediates / BOM levels | Whether semi-finished goods carry stock |
| Q-049 | Traceability granularity | Roll / pallet / carton handling units |

Until these are answered, the modules below expose **no execution behavior** —
by design, not by omission.

## Already-shipped seams (verified in code)

### 1. Domain-event bus (`apps.core.events`)

- `DomainEvent` base with `EntityCreated/Updated/Deleted/Approved/Rejected`.
- Handlers are registered subscribers; a failing subscriber can never break the
  publisher (pinned by `test_failing_subscriber_does_not_break_publish`).
- Execution hooks (stock postings, genealogy edges, QC triggers) should be
  **new subscribers**, not calls inside document services.

### 2. Transactional outbox pattern (`apps.core.transactions.atomic_with_events`)

- Events publish via `transaction.on_commit`, so subscribers only ever see
  committed state; tests drain callbacks explicitly.
- Any stock-ledger write triggered by a document transition inherits exactly-once
  per-commit semantics for free.

### 3. Locked status transitions (`apps.*.services.transition`)

- All document state machines re-check source status on a
  `select_for_update()` row inside one transaction (first committer wins,
  loser gets `409 ConflictError`). Verified by
  `apps.procurement.tests.test_transition_safety`.
- Production order release/complete/close/cancel already use it — the moment
  Q-046 lands, material-issue hooks attach to **existing** transitions without
  changing their locking contract.

### 4. Immutable versioned structures

- Spec/BOM/Routing/QualityPlan revisions freeze on activation
  (`Revision.is_editable`, child-row serializers reject non-DRAFT parents).
- Execution consumption must reference an **ACTIVE revision id**; the reference
  integrity rule "child rows belong to the pinned revision" is already
  serializer-enforced and audited.

### 5. Audited writes (`AuditedModelViewSet` + `apps.core.service`)

- Every create/update/delete emits events carrying before/after snapshots.
- Stock movements, issues, receipts will get trail coverage automatically by
  routing through `atomic_with_events` + the audit subscriber — no bespoke
  audit code needed.

## Proposed boundary contracts (interfaces only — no semantics chosen)

These are the seams the execution layer must implement once gates resolve.
Each is a service-module function signature; none exists yet in code.

```text
inventory.post_movement(...)      # direction, qty, handling-unit ref, refs to doc lines
inventory.handle_units(...)       # shape decided by Q-046/Q-049
production.issue_materials(...)   # method decided by Q-048
production.confirm_output(...)    # qty + handling units produced
quality.record_check_result(...)  # plan/characteristic + result set
sales.allocate_order_line(...)    # reservation semantics post-Q-046
procurement.receive_goods(...)    # GRN line → stock posting bridge
```

Common rules they must honor (already true platform-wide):

1. Run inside `atomic_with_events`; emit domain events instead of direct audit
   writes.
2. Reference documents/revisions by UUID; never duplicate frozen definition
   data into movement rows beyond what traceability requires.
3. Multi-company consistency is validated at the serializer/service boundary
   today (see `ProductionOrderSerializer.validate`) — execution rows must keep
   the same company invariant pending Q-055 scoping (see
   [multi-tenancy-preparation.md](multi-tenancy-preparation.md)).

## What changes when each gate is answered

- **Q-046/Q-049** → new models under `apps.inventory` (handling units) +
  `post_movement` gains its unit-reference argument; production confirmations
  start emitting `EntityCreated(manufacturing.Roll|Lot)`-style events.
- **Q-048** → picks whether `issue_materials` is invoked explicitly from a UI
  action or as a subscriber of `production` completion transitions.
- **Q-026** → decides whether intermediates appear as `catalog.Material`s with
  their own BOM roots (schema already supports this — no migration expected).

None of these require touching the document services listed above; that is the
point of this preparation.
