# Product Engineering (Task 005)

Product Engineering turns a customer's request into a **versioned technical
specification** — the authoritative "how this product is made" record that later
domains (BOM/routing, costing, production, quality) will reference. This
milestone builds the specification *spine* and its lifecycle only; it is the
first business module to exercise the platform's `VersionedRoot`/`Revision`
pattern for real.

## Scope discipline

Task 005 implements the versioned specification **structure and mechanics**, and
nothing that depends on an open business decision. Concretely, it ships:

- `CustomerProduct` — the versioned *root*: a made-to-order product identity for
  a specific customer. Its `code` is entered manually; it is **not** derived by
  any SKU/parameter scheme (that scheme is open, Q-019 / NQ-005 / #14).
- `SpecificationRevision` — one immutable-once-active revision of the product's
  technical spec, carrying the geometry, print, lamination and finish header
  fields plus effective-date stamps.
- `SpecLayer` — the ordered film/laminate structure (substrate → adhesive →
  sealant …), each layer pointing at a `catalog.Material` with an optional
  micron target and tolerance band.
- `SpecColor` — the ink/color formulation, each color pointing at a `Material`
  that **must** be of subtype `INK` (with an optional alternative ink), plus
  coverage and a ΔE tolerance.
- `SpecParameter` — a typed, extensible key/value bag (text / number / bool with
  unit and tolerance) so specification attributes that are still being discovered
  can be captured without a schema change or an invented enum.

The **mechanical lifecycle** is: create a `DRAFT` revision (monotonic
`revision_number` per root); edit the draft and its child rows freely; then
*activate* it, which atomically supersedes the prior `ACTIVE` revision of the
same root and stamps `effective_from` / `effective_to`. A non-`DRAFT` revision
(and its children) is immutable.

### Deliberately NOT built (open gates)

These are recorded in `docs/requirements/do-not-build-yet.md` and were left out
on purpose, because each depends on a business decision that is still open:

- **What *triggers* a new revision, and who approves it** (Q-024, #7/#13). The
  code performs the *mechanical* draft → activate transition; it applies **no**
  approver, threshold, or change-control policy. Activation is gated only by the
  `engineering.specification.manage` permission.
- **The SKU / product-coding derivation scheme** (Q-019 / NQ-005, #14).
  `CustomerProduct.code` is a manual field.
- **Default tolerance values** (Q-022). Tolerance fields are nullable with **no
  invented default** — a missing tolerance means "not specified", never a
  guessed number.
- **A fixed bag-type list** (Q-014 / Q-020). `bag_type` is a free `CharField`,
  not an enum, until the canonical list is confirmed.
- **Tooling / cliché cost model and mandatory-sampling rules** (#5 / #15).
- **Artwork revisions** as a separate linked lifecycle. They are a real future
  entity; this milestone does not model them (the tooling asset's optional
  `customer_product` link is the stand-in until artwork lands).

## Tooling / cliché assets (SR-03)

A later engineering slice adds the SR-03 **cliché / sheet (برگ) / set (دست)**
printing-tooling asset — a first-class SLZ domain object that generic ERPs treat
as a plain fixed asset or consumable. It is intentionally the **confirmed
identity + usage-life layer only**:

- `ToolingAsset` (`SoftDeleteModel`) is company-scoped (DR-040), `PROTECT`-links
  to its `customer` (`partners.Partner`) and, optionally, to the specific
  `CustomerProduct` it prints. `(company, code)` is unique (clean `400` on
  duplicate). It carries a `tooling_type` (`CLICHE`/`SHEET`/`SET`), a
  `status` (`ACTIVE`/`RETIRED`), the usage-life counters
  `usage_life_limit` (nullable — *how* life is measured is open, never a guessed
  default) and `usage_count`, an optional `warehouse` pointer, and notes.
- The optional `warehouse` must be a **cliché store**
  (`inventory.WarehouseStoreType.CLICHE`, SR-10) in the same company — validated
  in the serializer. A linked `customer_product` must share the asset's company
  **and** customer. These are integrity checks, not invented business policy.
- `is_life_exceeded` is a pure arithmetic helper (`usage_count >=
  usage_life_limit`, false when no limit is set); it applies **no**
  end-of-life policy.

Deliberately **not** built: the tooling **cost model** (customer-paid vs
amortized — OPEN, Q-004/036, do-not-build-yet #5), and any **automatic**
`usage_count` increment from a work-order/operation confirmation, which belongs
to the gated execution/traceability layer (Q-046). Here `usage_count` is plain
audited master data.

The lifecycle lives in `services.py` alongside the spec lifecycle:
`retire_tooling` (ACTIVE → RETIRED) and `reactivate_tooling` (RETIRED → ACTIVE)
each guard the source status (`ConflictError`, code `invalid_status_transition`,
HTTP `409`) and emit `EntityUpdated` so the change is audited. `status` is
read-only on the serializer, so it can only move through these actions.

Under `/api/v1/engineering/`: `tooling-assets/` — CRUD plus `POST {id}/retire/`
and `POST {id}/reactivate/`; gated by `engineering.tooling.view` / `.manage`.
The React app adds an engineering **Tooling & clichés** browse (showing
`usage_count / limit`, flagged when life is exceeded) with contextual
retire/reactivate buttons and a permission-gated create form.

## Entities

`engineering` is a new app. `CustomerProduct` extends `VersionedRoot` (so it is
itself an audited `BaseModel`) and is company-scoped: `(company, code)` is unique
via a non-conditional `UniqueConstraint`, which DRF surfaces as a clean `400` on
duplicate rather than a `500` integrity error. It links (all `PROTECT`) to
`partners.Partner` (the customer), the `catalog` taxonomy (`ProductGroup`,
`ProductFamily`) and a `base_uom`.

`SpecificationRevision` extends `Revision` (giving it `revision_number`,
`status`, `effective_from`/`effective_to`, `change_reason` and the
`is_active`/`is_editable` helpers). It `PROTECT`-links to its root and holds the
spec header: format, free-text bag type, width/length/gusset with low/high
tolerance columns, print process, number of colors, lamination/cold-seal flags,
and surface finish. `(root, revision_number)` is unique.

`SpecLayer`, `SpecColor` and `SpecParameter` are `SoftDeleteModel`s that
`CASCADE` from their revision. Each enforces order/identity with a
`UniqueConstraint` — `(revision, sequence)` for layers and colors,
`(revision, key)` for parameters.

## Writes are audited by construction

Like every module, engineering never writes to the database outside the audited
path. Simple CRUD (customer products and the spec child rows) goes through
`AuditedModelViewSet`, which routes create/update/delete through
`apps.core.service` and emits `EntityCreated` / `EntityUpdated` / `EntityDeleted`
domain events; the audit subscriber records each one.

The specification **lifecycle** is not simple CRUD, so it lives in
`apps/engineering/services.py`:

- `create_specification_draft(root, actor, **fields)` allocates the next
  `revision_number` and creates the `DRAFT` inside `atomic_with_events()`,
  emitting `EntityCreated`.
- `activate_specification(revision, actor)` refuses to activate anything but a
  `DRAFT` (`ConflictError`, code `revision_not_draft`), then — in one
  transaction — supersedes the prior `ACTIVE` revision (`select_for_update`,
  status → `SUPERSEDED`, `effective_to` stamped) and activates this one,
  emitting an `EntityUpdated` for each change.

> **Note:** activation emits `EntityUpdated` (not `EntityApproved`). The audit
> subscriber only listens to Created/Updated/Deleted, so a state change that must
> be audited has to be published as `EntityUpdated`.

Immutability of non-`DRAFT` revisions is enforced in **two** places so it holds
regardless of entry point: the viewset's `perform_update`/`perform_destroy` (and
each child serializer's `validate`) call `assert_revision_editable`, which raises
`ConflictError` (code `revision_not_editable`, HTTP `409`) when the target
revision is not editable.

## API surface

Under `/api/v1/engineering/`:

- `customer-products/` — CRUD; view/manage gated by
  `engineering.customerproduct.view` / `.manage`.
- `specifications/` — CRUD on the draft header plus `POST
  {id}/activate/`; gated by `engineering.specification.view` / `.manage`.
- `spec-layers/`, `spec-colors/`, `spec-parameters/` — child CRUD, sharing the
  `engineering.specification.*` permissions (a spec's children are part of the
  spec).

## Frontend

The React app adds an `engineering` route group: a **Customer products** browse
with a permission-gated create form (the representative audited write path), and
a **Specifications** browse that renders each revision's number/status and — for
a `DRAFT` row, to a user with `manage` — an **Activate** button that calls the
lifecycle endpoint and reloads. All business rules stay server-side; the UI
surfaces the backend's error message rather than duplicating any rule.

## Verification status

The source is `py_compile`-clean and mirrors the established Task 004 patterns.
Runtime verification was **not** possible in the authoring sandbox (no
PostgreSQL / package installs). Before relying on this module, run in a proper
environment: `python manage.py makemigrations engineering && migrate`,
`python manage.py seed_rbac` (to load the four new permissions),
`python manage.py test apps.engineering`, and the frontend `npm run build` /
`vitest`.
