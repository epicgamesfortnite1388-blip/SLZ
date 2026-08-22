# Quality Foundation — Characteristics & Quality Plans (Task 008)

Quality owns **what must be inspected and against which limits**. Task 008 ships
the first, deliberately minimal slice of that domain: the company-scoped
`QualityCharacteristic` catalogue and the versioned `QualityPlan` (bound to a
product specification revision) with its immutable revisions and plan items. It
is the fifth business module and reuses the platform's `VersionedRoot`/`Revision`
pattern, audited write path, company scoping and RBAC without introducing any
new mechanism.

## Scope discipline

The quality domain's *value* is execution — recording measured results against a
lot / roll / work order, raising non-conformances, holding stock, and issuing
certificates. Almost all of that is **gated on open business decisions** (below),
and the check-execution layer is bound to traceability, whose highest-priority
gate (Q-046, roll serialization vs. lot+count) must be resolved before the
traceability schema can even be migrated (C-003). Building execution now would
mean inventing unresolved SLZ rules (methods, sampling, tolerances, reason
codes).

So Task 008 follows the same discipline as Tasks 004–007: build the **confirmed
definition layer** and defer everything gated. Concretely, it ships:

- `QualityCharacteristic` — a company-scoped catalogue of measurable attributes
  (thickness, ΔE, bond/seal strength, COF, a dimension, an attribute pass/fail).
  It records *what* is measured, *how* (`method` — a free-text standard /
  instrument reference; SLZ's actual methods are OPEN, Q-039), the generic
  `datatype` (number / text / boolean) and an optional `default_uom`. `code` is
  unique per company; `is_active` supports soft retirement. Spec **limits are
  not** stored here — the same characteristic has different limits per product,
  so limits live on the plan item.
- `QualityPlan` / `QualityPlanRevision` / `QualityPlanItem` — a versioned plan
  root bound to one `engineering.SpecificationRevision` (one plan per revision,
  mirroring Routing), its immutable revisions, and the inspected-characteristic
  lines. Each item binds a characteristic to an optional `work_center` and a
  free-text `stage_label` (inspection points are OPEN, Q-039), with nullable
  `lower_limit` / `upper_limit` / `target` (SLZ's tolerances are OPEN, Q-022 —
  no default invented; limits ultimately trace to the spec revision), a
  free-text `sampling` rule (100%-vs-AQL is OPEN, Q-040), an optional
  `method_override`, and a descriptive `is_mandatory` flag.

### Deliberately NOT built (open gates)

Recorded in `docs/requirements/do-not-build-yet.md`; each depends on a business
decision that is still open:

- **Quality CHECK execution & results** (measured values, PASS / FAIL /
  CONDITIONAL) — append-only records tied to a lot / roll / work order / batch,
  which requires the traceability + stock layer gated on Q-046 (#18, the
  highest-priority gate). No result model, no measurement, nothing.
- **Non-conformance (NCR) / QC_HOLD**, disposition (accept-as-is / rework /
  scrap / return / downgrade), and **scrap & rework reason codes** (Q-041 /
  Q-043 / Q-016·042, #12).
- **COA (Certificate of Analysis)** issuance (Q-045) and **formal recall / CAPA /
  8D** (Q-044, #31).
- **Any single terminal inspection gate** or hard-coded plan / characteristic /
  tolerance / sampling set (skill 06 FORBIDDEN list, #11) — plans are authored
  per product, never generated or assumed.

## Entities

| Model | Base | Key fields | Constraints |
| --- | --- | --- | --- |
| `QualityCharacteristic` | `BaseModel` | `company` (PROTECT), `code`, `name_fa`, `name_en`, `datatype`, `method`, `default_uom` (nullable, PROTECT), `is_active`, `notes` | `UniqueConstraint(company, code)` → `uq_quality_characteristic_company_code` |
| `QualityPlan` | `VersionedRoot` | `spec_revision` (PROTECT), `is_active` | `UniqueConstraint(spec_revision)` → `uq_quality_plan_specrev` |
| `QualityPlanRevision` | `Revision` | `root` (PROTECT) | `UniqueConstraint(root, revision_number)` → `uq_quality_plan_revision_root_number` |
| `QualityPlanItem` | `SoftDeleteModel` | `revision` (CASCADE), `sequence`, `characteristic` (PROTECT), `work_center` (nullable, PROTECT), `stage_label`, `lower_limit`/`upper_limit`/`target` (nullable), `unit`, `sampling`, `method_override`, `is_mandatory`, `notes` | `UniqueConstraint(revision, sequence)` → `uq_quality_plan_item_revision_sequence` |

`datatype` defaults to `NUMBER`; limits are nullable with **no invented
default**; `sampling` / `stage_label` / `method_override` are free text.
Master-data FKs use `PROTECT`; the child item `CASCADE`s with its revision.

## Reused mechanisms (nothing new)

- **Versioning lifecycle** — `QualityPlanRevision` subclasses
  `core.versioning.Revision`, so `apps/quality/services.py` reuses the generic
  `create_revision_draft` / `assert_revision_editable` / `activate_revision`
  implementation (identical in shape to `apps.manufacturing.services`, kept
  per-module for consistency with the established architecture). Draft →
  activate → supersede is atomic (`atomic_with_events`, `select_for_update`) and
  emits `EntityUpdated` on state change.
- **Audited write path** — all four viewsets extend `AuditedModelViewSet`;
  creates and updates emit domain events, so the audit subscriber records
  `CREATE` / `UPDATE` / `DELETE` with `entity_type` `quality.QualityCharacteristic`,
  `quality.QualityPlan`, `quality.QualityPlanRevision`, `quality.QualityPlanItem`.
- **Immutability guard** — revision update/destroy call `assert_revision_editable`
  and each plan-item write goes through `_ChildOfRevisionSerializer`, which
  raises `ConflictError` (`revision_not_editable`, HTTP `409`) against a
  non-DRAFT revision.
- **RBAC** — four permissions (`quality.characteristic.view|manage`,
  `quality.plan.view|manage`) seeded in `seed_rbac.py`; enforced by
  `HasPermission` via each viewset's `permission_map` / `required_permission`.
- **Duplicate rejection** — the non-conditional `UniqueConstraint`s surface as
  DRF validators returning `400` on duplicate characteristic code / second plan
  per spec revision.

## API surface

Under `/api/v1/quality/`:

- `GET/POST /characteristics/`, `GET/PUT/PATCH/DELETE /characteristics/{id}/`
- `GET/POST /plans/`, `GET/PUT/PATCH/DELETE /plans/{id}/`
- `GET/POST /plan-revisions/` (with `POST {id}/activate/`),
  `GET/PUT/PATCH/DELETE /plan-revisions/{id}/`
- `GET/POST /plan-items/`, `GET/PUT/PATCH/DELETE /plan-items/{id}/`

## Frontend

- `api/quality.ts` — typed `QualityCharacteristic` / `QualityPlan` /
  `QualityPlanRevision` shapes, the `CharacteristicDatatype` union +
  `CHARACTERISTIC_DATATYPES` list, `createQualityCharacteristic` and
  `activateQualityPlanRevision`.
- `pages/quality/` — `CharacteristicsPage` (browse + create action), a
  `CharacteristicCreatePage` write form (the representative audited path, with a
  datatype select and free-text method), and `QualityPlanRevisionsPage` (browse
  over plan revisions exposing an **Activate** button for a DRAFT row to a user
  with `manage`).
- Routes under `/quality/*` and sidebar entries, each gated by the matching view
  permission. All business rules stay server-side; the UI surfaces the backend's
  error message rather than duplicating any rule.

## Verification status

The backend source is `py_compile`-clean and mirrors the established Task 006
patterns; both locale bundles parse as valid JSON with matching `quality` key
sets. Runtime verification was **not** possible in the authoring sandbox (no
PostgreSQL / package installs). Before relying on this module, run in a proper
environment: `python manage.py makemigrations quality && migrate`,
`python manage.py seed_rbac` (to load the four new permissions),
`python manage.py test apps.quality`, and the frontend `npm run build` /
`vitest`.
