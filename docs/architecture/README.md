# SLZ ERP — Architecture Documentation

This directory documents the **platform foundation** for the SLZ ERP/MES — the
custom system for صنایع لفاف زرین (Zarrin Laff Industries), a made-to-order
flexible-packaging manufacturer.

These documents describe *how the platform is built and how future modules must
build on it*. They deliberately do **not** describe business modules (sales,
engineering, inventory, manufacturing, quality, purchasing, finance, …). The
foundation exists so those modules can be added consistently and safely.

## Reading order

1. [system-architecture.md](system-architecture.md) — the modular monolith, apps,
   layers, request lifecycle, and the domain-event bus.
2. [api-conventions.md](api-conventions.md) — REST surface under `/api/v1/`,
   the standardized error envelope, pagination, filtering, sorting, auth.
3. [database-conventions.md](database-conventions.md) — UUID keys, business
   numbers, naming, indexing, bilingual fields, migrations.
4. [data-lifecycle.md](data-lifecycle.md) — soft delete (opt-in), audit trail,
   correlation IDs, and how records are created / changed / retired.
5. [versioning.md](versioning.md) — the reusable versioning pattern
   (`VersionedRoot` / `Revision`) modules use for revisable master data.
6. [transactions.md](transactions.md) — the validate → begin → apply → audit →
   commit strategy and post-commit event publication.
7. [security.md](security.md) — authentication, RBAC, file security, transport
   and secret handling, and the security baseline.
8. [workflow-approvals.md](workflow-approvals.md) — the generic, configuration-
   driven approval engine (definition / instance / step), its self-guarding
   decision service, the per-user approvals inbox and the API's per-action
   authorization. Carries **no** business approval policy (matrices are gated,
   #7).
9. [notifications.md](notifications.md) — the in-app notification channel: the
   per-user inbox, its self-authorizing read/clear API and the header unread
   badge. Email / SMS / push are deferred delivery interfaces (DR-008, #30).
10. [audit-log.md](audit-log.md) — the append-only audit trail's **read** API and
    its searchable viewer (`/audit/logs`, gated by `audit.log.view`). How entries
    are *written* is in data-lifecycle.md; this covers the compliance surface.
11. [organization-master.md](organization-master.md) — the `Company` → `Site`
    structural master surface (company/site scoping roots, DR-040), the
    audit-consistency hardening of its write path, and its browse + create
    frontend. Carries no business rule beyond the pre-existing unique-code
    constraints.
12. [documents.md](documents.md) — the generic, entity-keyed **attachment** store
    (upload / list / authenticated download / soft delete) and its document-
    register frontend. A reusable mechanism keyed by (`entity_type`,
    `entity_id`); it carries no rule about what may attach to what.

## Domain modules

Business modules build on the foundation above. The first is:

- [master-data.md](master-data.md) — Task 004 master-data foundation: partners,
  product taxonomy + thin product, materials, units of measure, site
  capabilities, and a minimal employee — all written through the audited service
  layer.
- [product-engineering.md](product-engineering.md) — Task 005 product
  engineering: the versioned `CustomerProduct` root and its
  `SpecificationRevision` (layers, colors, typed parameters) with the
  draft → activate → supersede lifecycle. The first module to use the
  `VersionedRoot`/`Revision` pattern for real. A later slice adds the SR-03
  `ToolingAsset` (cliché / sheet / set printing tooling with usage-life counters
  and a retire/reactivate lifecycle) — the confirmed identity + usage-life layer
  only; the tooling cost model (Q-004/036) and automatic usage capture (Q-046)
  are deferred.
- [manufacturing-bom-routing.md](manufacturing-bom-routing.md) — Task 006
  manufacturing: `WorkCenter` / `Machine` resource masters (data-driven
  capability profiles) plus the versioned `BillOfMaterials` and `Routing`
  structures bound to a specification revision, sharing one generic
  draft → activate → supersede lifecycle service.
- [inventory-foundation.md](inventory-foundation.md) — Task 007 inventory
  foundation: the company/site-scoped `Warehouse` master (SR-10 special store
  types) and per-user `WarehouseAccess` grants. The confirmed master-data slice
  only — the gated transactional / traceability layer (stock movements, kardex,
  lots/rolls, genealogy) is deferred behind Q-046 and related open decisions.
- [quality-foundation.md](quality-foundation.md) — Task 008 quality foundation:
  the company-scoped `QualityCharacteristic` catalogue and the versioned
  `QualityPlan` (bound to a specification revision) with its immutable revisions
  and plan items. The confirmed definition layer only — check execution, results,
  NCR/QC_HOLD, scrap/rework, COA and recall are deferred behind Q-039/040/043/
  044/046 and related open decisions.
- [procurement-foundation.md](procurement-foundation.md) — Task 009 procurement
  foundation: the `PurchaseRequisition` and `PurchaseOrder` header+line
  transactional documents with a server-authoritative status state machine
  (submit/approve/reject/cancel; approve/send/close/cancel). The confirmed
  commercial-document layer only — goods receipt/GRN, MRP, RFQ, approval
  thresholds, import/FX, supplier-invoice matching and valuation are deferred
  behind #7/#14/#17/#23 and related open decisions.
- [sales-order-management.md](sales-order-management.md) — Task 010 sales-order
  foundation: the `SalesOrder` header+line transactional document (the MTO demand
  origin) with a server-authoritative status state machine
  (confirm/close/cancel). The confirmed commercial-document layer only — pricing/
  proforma, ATP/promised dates, allocation/shipment/invoicing, credit and
  tolerance enforcement are deferred behind R-14/SR-12/Q-046/#11/#12/#18 and
  related open decisions.
- [production-order-management.md](production-order-management.md) — Task 011
  production-order foundation: the header-only `ProductionOrder` (Work Order)
  transactional document — a shop-floor commitment built to a frozen engineering
  definition (spec/BOM/routing revision) — with a server-authoritative status
  state machine (release/complete/close/cancel). The committed document layer
  only — material issue/genealogy, operation confirmations/scrap/downtime, QC
  results, margin priority, outsourcing locus and ATP/capacity are deferred
  behind Q-046/SR-05/SR-06/SR-08/SR-12/SR-13/SR-14/#9/#12/#18/#19.
- [multi-tenancy-preparation.md](multi-tenancy-preparation.md) — Q-055 impact
  map: every model/queryset/service/serializer/frontend surface that will need
  company scoping once the tenancy decision lands. Preparation only; no
  behavior change.
- [execution-preparation.md](execution-preparation.md) — execution-layer
  extension points: the already-shipped seams (event bus, transactional outbox,
  locked transitions, versioned structures, audited writes) and the boundary
  contracts the future stock/genealogy/QC/allocation services must implement.
  Preparation only; no gated semantics chosen.

## Scope boundary (important for future agents)

The foundation provides **mechanisms, not policy**:

- RBAC engine and permission format — but only the *platform* roles/permissions
  are seeded. Business roles are defined by the modules that own them.
- A versioning pattern — but no versioned business entity is shipped.
- A workflow engine — minimal, configurable approvals; **not** a BPM.
- Notification channels — in-app works; email/SMS/push are interfaces to be
  implemented per deployment.

Do not add business logic to foundation apps. See
[system-architecture.md](system-architecture.md#dependency-rules).

## Verification status

Application logic is runtime-verified on the SQLite test profile (backend and
frontend suites, migration-drift gate, lint/typecheck/build — see
`docs/PROJECT-STATUS.md` for current counts). The container path (Docker,
PostgreSQL, Redis, nginx) has **not** been executed in the authoring
environment; `docs/RELEASE-CHECKLIST.md` records it as the outstanding
deployment verification step.
