# Manufacturing — BOM & Routing (Task 006)

Manufacturing owns the **engineering definition of how a product is made**: the
resources it runs on (work centers and machines) and the two versioned
structures bound to a specification revision — the **Bill of Materials** (what is
consumed) and the **Routing** (the ordered operations that produce output). It
is the third business module and reuses the platform's `VersionedRoot`/`Revision`
pattern that Product Engineering established.

## Scope discipline

Task 006 implements the resource masters and the versioned BOM/Routing
**structure and mechanics**, and nothing that depends on an open business
decision. Concretely, it ships:

- `WorkCenter` — a logical production stage (Extrusion, Printing, Lamination,
  Slitting, Converting, Packing) that groups interchangeable machines.
  Company-scoped, optionally site-pinned; `sequence_hint` is a display-only
  ordering aid and defines **no** routing.
- `Machine` — a physical resource in a work center. Its `capability_profile` is
  free-form JSON (web width, thickness range, speeds, color stations, supported
  structures, …). Planning/validation reads these attributes **generically** —
  adding a machine is adding data, never code (constraint #9).
- `BillOfMaterials` / `BomRevision` / `BomLine` — a versioned BOM root bound to
  one `engineering.SpecificationRevision`, its immutable revisions, and the
  consumed-material lines (quantity per output + UoM, with free-text consumption
  basis and nullable scrap).
- `Routing` / `RoutingRevision` / `RoutingOperation` — a versioned routing root
  (one per spec revision), its immutable revisions, and the ordered operations
  (work center + optional output material + setup/run-rate captured as data).

The **mechanical lifecycle** is identical to Product Engineering: create a
`DRAFT` revision (monotonic `revision_number` per root); edit the draft and its
child rows freely; then *activate* it, which atomically supersedes the prior
`ACTIVE` revision of the same root and stamps `effective_from` /
`effective_to`. A non-`DRAFT` revision (and its children) is immutable. Because
`BomRevision` and `RoutingRevision` are both `core.versioning.Revision`
subclasses, **one generic service** (`create_revision_draft` / `activate_revision`
/ `assert_revision_editable`) drives both — adding another versioned structure
later is wiring, not new lifecycle code.

### Deliberately NOT built (open gates)

Recorded in `docs/requirements/do-not-build-yet.md`; each depends on a business
decision that is still open:

- **BOM consumption bases, waste factors, standard scrap %** (Q-027, #9).
  `BomLine.consumption_basis` is a free `CharField` (not a locked enum) and
  `scrap_pct` is nullable with **no invented default** — a missing scrap means
  "not specified", never a guessed number.
- **Standard routing templates & stage-skip rules** (Q-029, #10). Routings are
  authored per spec revision; the system generates none.
- **Which intermediates are inventoried / real BOM levels** (Q-026, #19). A BOM's
  `output_material` is optional and no level is derived or assumed.
- **Alternates/substitutes** (A-014 / Q-028), the **changeover matrix**,
  machine-qualification pools, required skills, QC-plan links, and tooling links.
- **Outsourcing execution locus** (DR-043 / NQ-004) and **all production
  execution** (production/work orders, consumption, genealogy) — later tasks.

## Entities

`manufacturing` is a new app. `WorkCenter` and `Machine` extend `BaseModel`, are
company-scoped (`(company, code)` unique via a non-conditional
`UniqueConstraint`, surfaced by DRF as a clean `400` on duplicate) and
optionally link to a `Site` (`PROTECT`). `Machine` also `PROTECT`-links to its
`WorkCenter`.

`BillOfMaterials` and `Routing` extend `VersionedRoot` and each `PROTECT`-link to
an `engineering.SpecificationRevision`. A BOM is unique per
`(spec_revision, output_material)`; a routing is unique per `spec_revision` (one
routing per revision). `BomRevision` and `RoutingRevision` extend `Revision`
(giving `revision_number`, `status`, effective dates, `change_reason`, and the
`is_active`/`is_editable` helpers), `PROTECT`-link to their root, and are unique
per `(root, revision_number)`.

`BomLine` and `RoutingOperation` are `SoftDeleteModel`s that `CASCADE` from their
revision and enforce `(revision, sequence)` uniqueness. `BomLine` carries the
consumed `Material`, `quantity_per_output` (Decimal), `UoM`, free-text
`consumption_basis`, nullable `scrap_pct`, and notes. `RoutingOperation` carries
the `WorkCenter`, `operation_name`, optional `output_material`, nullable
`setup_time_minutes` / `run_rate`, a free-text `run_rate_basis`, and notes.

## Writes are audited by construction

Manufacturing never writes outside the audited path. Simple CRUD (work centers,
machines, BOM/routing roots, and the child rows) goes through
`AuditedModelViewSet`, which routes create/update/delete through
`apps.core.service` and emits `EntityCreated` / `EntityUpdated` / `EntityDeleted`;
the audit subscriber records each one.

The BOM/Routing **lifecycle** is not simple CRUD, so it lives in
`apps/manufacturing/services.py` as a single generic implementation:

- `create_revision_draft(revision_model, entity_type, root, actor, **fields)`
  allocates the next `revision_number` and creates the `DRAFT` inside
  `atomic_with_events()`, emitting `EntityCreated`.
- `activate_revision(revision, entity_type, actor)` refuses to activate anything
  but a `DRAFT` (`ConflictError`, code `revision_not_draft`), then — in one
  transaction — supersedes the prior `ACTIVE` revision (`select_for_update`,
  status → `SUPERSEDED`, `effective_to` stamped) and activates this one,
  emitting an `EntityUpdated` for each change.

> **Note:** activation emits `EntityUpdated` (not `EntityApproved`). The audit
> subscriber only listens to Created/Updated/Deleted, so a state change that must
> be audited has to be published as `EntityUpdated`.

Immutability of non-`DRAFT` revisions is enforced in **two** places so it holds
regardless of entry point: the revision viewsets' `perform_update` /
`perform_destroy` and each child serializer's `validate` call
`assert_revision_editable`, which raises `ConflictError` (code
`revision_not_editable`, HTTP `409`) when the target revision is not editable.

## API surface

Under `/api/v1/manufacturing/`:

- `work-centers/`, `machines/` — CRUD; view/manage gated by
  `manufacturing.workcenter.*` / `manufacturing.machine.*`.
- `boms/`, `bom-revisions/` (with `POST {id}/activate/`), `bom-lines/` — gated by
  `manufacturing.bom.view` / `.manage`.
- `routings/`, `routing-revisions/` (with `POST {id}/activate/`),
  `routing-operations/` — gated by `manufacturing.routing.view` / `.manage`.

## Frontend

The React app adds a `manufacturing` route group: a **Work centers** browse with
a permission-gated create form (the representative audited write path), a
**Machines** browse (rendering the capability-profile key count, since the
profile itself is free-form data), and **Bills of materials** / **Routings**
browses over their revisions, each exposing — for a `DRAFT` row, to a user with
`manage` — an **Activate** button that calls the lifecycle endpoint and reloads.
All business rules stay server-side; the UI surfaces the backend's error message
rather than duplicating any rule.

## Verification status

The backend source is `py_compile`-clean and mirrors the established Task 005
patterns; both locale bundles parse as valid JSON. Runtime verification was
**not** possible in the authoring sandbox (no PostgreSQL / package installs).
Before relying on this module, run in a proper environment:
`python manage.py makemigrations manufacturing && migrate`,
`python manage.py seed_rbac` (to load the eight new permissions),
`python manage.py test apps.manufacturing`, and the frontend `npm run build` /
`vitest`.
