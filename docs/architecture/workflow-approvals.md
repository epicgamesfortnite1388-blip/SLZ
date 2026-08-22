# Workflow & Approvals

The `workflow` app is the platform's **generic approval engine** — a foundation
mechanism, not a business module. It carries **no** business approval policy
(who approves what, at which threshold): those matrices are still open
(Q-054/056, DR-032; `do-not-build-yet.md` #7, *"engine may be built; rules must
not be hard-coded"*). The engine only knows how to route an entity through an
ordered set of approvers and record the outcome for audit.

## Model

Three small entities (`apps/workflow/models.py`):

- `WorkflowDefinition` — the approval *shape*: a unique `code`, bilingual name,
  an `approval_mode` (`SEQUENTIAL` / `PARALLEL`) and a free-form `config`
  JSON bag interpreted by callers (never hard-coded here).
- `WorkflowInstance` — one entity's journey: a `definition`, the target
  (`entity_type` + `entity_id`, indexed together), and a `state` from the
  standard set `DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED / REJECTED /
  CANCELLED`.
- `ApprovalStep` — one approver's slot: `sequence`, `approver`, `decision`
  (`PENDING` / `APPROVED` / `REJECTED`), `comment`, `decided_at`, unique per
  `(instance, sequence)`.

## Service (the only sanctioned mutation path)

`apps/workflow/services.py` owns every state change; each is atomic, writes an
audit entry, publishes a domain event and notifies the relevant users:

- `start_workflow(definition, entity_type, entity_id, approvers, actor)` —
  creates the instance and its ordered steps, moves it to `UNDER_REVIEW`, and
  notifies the first pending approver(s) (all of them in `PARALLEL`, only the
  earliest in `SEQUENTIAL`).
- `record_decision(instance, approver, approve, comment)` — **self-guarding**:
  it only accepts a decision from a user who has a still-`PENDING` step, and in
  `SEQUENTIAL` mode only from the *earliest* pending step. A rejection finalizes
  immediately; the final approval flips the instance to `APPROVED` and publishes
  `EntityApproved`.
- `cancel_workflow(instance, actor, reason)` — finalizes to `CANCELLED` unless
  already terminal.

Finalization emits `EntityApproved` / `EntityRejected` on the bus and an
`APPROVAL_COMPLETED` notification to the original requester.

## API surface

Under `/api/v1/workflow/`:

- `definitions/` — CRUD on the approval shapes; gated by
  `workflow.definition.view` / `.manage`.
- `instances/` — list + retrieve of the register, gated by
  `workflow.instance.view`; plus three POST actions:
  - `instances/{id}/decision/` — approve/reject. **Authentication only** at the
    permission layer, because the service self-guards to assigned approvers, so
    an approver needs no broad `view`/`manage` grant to act on their own item.
  - `instances/mine/` — the caller's **personal inbox**: open instances on which
    they still hold a `PENDING` step. Authentication only (it can only ever
    expose the caller's own steps).
  - `instances/{id}/cancel/` — requires `workflow.instance.manage`. This closes
    the earlier gap where any authenticated user could cancel any workflow.

Per-action authorization is resolved in `WorkflowInstanceViewSet.get_permissions`
rather than a single `permission_map`, precisely because `decision` and `cancel`
are both `POST` yet must be gated differently.

### Definitions are audited configuration

`WorkflowDefinitionViewSet` extends `AuditedModelViewSet`, so creating or editing
a definition is transactional, stamps `created_by`, and lands in the audit trail
(`entity_type` `workflow.WorkflowDefinition`) exactly like any other master
write — a definition is engine *configuration* and its provenance matters.
Writes are gated by `workflow.definition.manage`, reads by
`workflow.definition.view`. Defining a shape is not the same as encoding a
business rule: no approver matrix or threshold is seeded (#7).

## Frontend

The React app adds a **My approvals** screen (`/workflow/approvals`, in the
sidebar for every authenticated user) backed by `instances/mine/`. Each row
shows the workflow, the target entity, the current state and a comment field,
with **Approve** / **Reject** buttons that call the decision endpoint and
reload. No business rule is duplicated client-side; the server remains the
authority and surfaces its own error messages.

A **Workflow definitions** admin (`/workflow/definitions`, gated by
`workflow.definition.view`) lets an operator browse the configured shapes and,
with `.manage`, create a new one (code, bilingual name, `approval_mode`). The
form deliberately captures only the approval *shape* — approver assignment and
any routing policy stay server-side configuration (#7), so no rule matrix is
exposed in the UI.

## Deliberately NOT built (open gates)

- **Approval hierarchy & thresholds content** (Q-054/056, DR-032, #7) — no
  matrix is seeded; wiring a specific business document (e.g. a spec revision,
  a purchase order over a limit) to a definition and approver set is left to the
  owning module once the policy is confirmed.
- **Escalation / delegation / SLA timers**, parallel-quorum rules beyond
  all-must-approve, and email/SMS approval channels (DR-008, deferred).

## Verification status

IMPLEMENTED + STATICALLY CHECKED (`py_compile` clean; i18n en/fa parity). Tests
are IMPLEMENTED, not EXECUTED (no Postgres/npm in the authoring sandbox). Before
relying on this slice run: `python manage.py seed_rbac` (loads the two new
`workflow.instance.*` permissions), `python manage.py test apps.workflow`, and
the frontend `npm run build` / `vitest`.
