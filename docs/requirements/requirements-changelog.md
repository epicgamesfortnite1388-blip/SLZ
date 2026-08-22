# Requirements Changelog

Chronological record of **what changed in the requirements baseline and why**, preserving traceability and history. Requirement *text* lives in `requirements-baseline.md`; decisions in `decision-register.md`; this file records the *deltas* and their justification. Nothing here is silently applied — each entry cites its evidence source.

---

---

## 2026-08-22 — Foundation: Generic record-detail pattern + in-context attachments (Partner reference)

**Trigger:** Every module shipped browse (list) screens, but there was no way to open a single record, and the documents/attachments store — though usable via a standalone register — could not be reached *in the context of the record a file belongs to*. This slice establishes a reusable read-only detail-view pattern and an embeddable attachment panel, and applies both to the Partner entity as the reference implementation. It surfaces only data already returned by the existing retrieve endpoint and reuses the generic attachment API; it introduces **no** business rule (no attachment policy, no edit/write semantics beyond the already-audited upload/delete). Source-of-truth: `docs/architecture/documents.md`.

**What was built (no requirement text changed):** (1) `hooks/useRecord.ts` — a single-record fetch hook mirroring `useCollection` (loading/error/data/reload, stale-response cancellation, `path=null` defers fetching). (2) `components/RecordDetail.tsx` — a generic, presentation-only label/value view driven by a `DetailField[]` the caller maps from a typed record (encodes no per-entity knowledge). (3) `components/AttachmentPanel.tsx` — a reusable in-context file panel for a `(entity_type, entity_id)` target: lists via a new `listAttachments()` API helper, uploads, authenticated-downloads, and delete-gated soft-delete, all reusing the generic `/documents/attachments/` surface. (4) `pages/masterData/PartnerDetailPage.tsx` — the reference detail screen (`/master-data/partners/:id`, gated `partners.partner.view`) combining `RecordDetail` with the `AttachmentPanel` (mounted only when the user holds `documents.attachment.view`, entity type `partners.Partner`). (5) A per-row **View** link added to the partners list; route wired in `App.tsx`. (6) fa/en keys (`common.view`/`actions`, `partners.role.*`, `partners.fields.*`, `partners.detail.*`, `documents.panel.*`; parity checked), detail/attachment CSS, and an extended `documents.test.ts` covering `listAttachments`.

**Open gates explicitly NOT implemented:** none apply — un-gated foundation. Deliberately out of scope (no confirmed requirement): inline record editing, attachment policy (types/quotas/retention/AV), and rolling this detail+panel pattern out to every other module (Partner is the reference; other modules follow verbatim when their detail screens are prioritized). No requirement added, modified, or removed.

**RBAC delta:** none — reuses `partners.partner.view` and `documents.attachment.view/delete`; no schema migration.

---

## 2026-08-22 — Foundation: Live home dashboard (per-module record counts)

**Trigger:** The home `DashboardPage` shipped as a static placeholder ("no data" tile) even though every domain module already exposes a paginated, permission-gated list endpoint whose envelope carries an authoritative `count`. This slice turns the landing page into a live, at-a-glance summary without inventing any metric — every number is read straight from an existing endpoint, and each tile is gated by the same `*.view` permission as the module it counts, so the dashboard never surfaces data the user cannot already browse. Un-gated foundation; introduces **no** business rule or KPI definition.

**What was built (no requirement text changed):** (1) `api/dashboard.ts` — a `fetchCount(path)` helper that issues a single `page_size=1` request through the existing `fetchCollection` and returns only the envelope `count` (no rows transferred). (2) `DashboardPage.tsx` rewritten — a `STAT_DEFS` table of eight tiles (partners, products, materials, customer products, sales orders, purchase orders, production orders, warehouses), each a permission-gated `StatCard` that fetches its own count and links to the module's list route; users with no view permissions see a `noAccess` note instead of fabricated tiles. (3) `dashboard.stats` fa/en i18n keys extended (error, noAccess + the eight labels; parity checked). (4) `.stat-card-link` styling and a vitest api test (`dashboard.test.ts`) asserting `fetchCount` builds the `?page_size=1` URL and returns `count`.

**Open gates explicitly NOT implemented:** none apply — this is un-gated foundation. Deliberately out of scope (no confirmed requirement): business KPIs / charts / trend metrics, cross-module rollups, and any aggregate that would require choosing a definition (e.g. "open" order semantics, WIP value). No requirement was added, modified, or removed; this entry records the build delta.

**RBAC delta:** none — reuses existing `*.view` permissions; no schema migration.

---

## 2026-08-22 — Foundation: Documents / attachments made usable (frontend + client transport)

**Trigger:** The `documents` app (a generic, (`entity_type`, `entity_id`)-keyed `Attachment` store with upload / list / retrieve / authenticated download / soft-delete, RBAC `documents.attachment.view/delete` already seeded in Task 003) had shipped with a complete backend but **no** frontend and no client-side transport for its two non-JSON operations (multipart upload, authenticated binary download), so the platform's file-attachment mechanism was unreachable from the UI. This slice surfaces the existing generic API only; it is un-gated foundation and introduces **no** business rule about what may attach to what. Source-of-truth: `docs/architecture/documents.md`, `docs/architecture/security.md` (file security).

**What was built (no requirement text changed):** (1) Client transport — `RequestOptions.form?: FormData` + `apiClient.postForm(path, form)` for multipart bodies (Content-Type deliberately left unset so the browser adds the boundary), and a new `requestBlob`/`apiClient.getBlob(path)` that performs an authenticated binary fetch (same Bearer + X-Correlation-ID + single 401→refresh→retry as `request`) returning a raw `Blob`, needed because an anchor `href` cannot carry the Authorization header. (2) Frontend — `api/documents.ts` (`Attachment` type mirroring `AttachmentSerializer`; `uploadAttachment`/`deleteAttachment`/`downloadAttachment` + a `formatBytes` helper) and a **Documents** register page (`/documents`, sidebar + route gated by `documents.attachment.view`) combining an upload card (entity_type / entity_id / description / file) with a register listing filename / target / size, a per-row Download and a delete-gated Delete. (3) fa/en `documents` i18n block (parity checked) + a vitest api test (`documents.test.ts`) asserting the multipart payload, blank-description omission, delete path and `formatBytes`.

**Open gates explicitly NOT implemented:** none apply — this is un-gated foundation. Deliberately out of scope (no confirmed requirement): attachment policy (required types / quotas / retention / AV scanning), in-context attachment panels embedded in each business record's detail screen, and versioned / controlled-document / e-signature workflows. No requirement was added, modified, or removed; this entry records the build delta.

**RBAC delta:** none — `documents.attachment.view/delete` already existed; no schema migration.

---

## 2026-08-21 — Foundation: Workflow definitions admin + audited configuration

**Trigger:** The approvals inbox slice made the workflow *engine* usable for approvers, but there was still no surface to create/browse the approval *definitions* it runs on, and a data-integrity gap: `WorkflowDefinitionViewSet` was a plain DRF `ModelViewSet`, so creating/editing a definition (engine configuration whose provenance matters) was neither transactional-with-audit nor `created_by`-stamped — inconsistent with the audited-write convention. This slice completes the generic engine's admin (un-gated foundation, #7 "engine may be built; rules must not be hard-coded"); it introduces **no** business approval policy. Source-of-truth: `docs/architecture/workflow-approvals.md`.

**What was built (no requirement text changed):** (1) Backend hardening — `WorkflowDefinitionViewSet` now extends `AuditedModelViewSet` (permission_map/required_permission unchanged), so writes route through `apps.core.service`, stamp `created_by`, and emit audit rows (`entity_type` `workflow.WorkflowDefinition`). Behavioural only, no schema migration, no new RBAC perm (`workflow.definition.view/manage` already seeded in Task 003). (2) Backend test `WorkflowDefinitionApiTests` (create persists+audits with created_by + AuditLog CREATE, duplicate code 400, view-only user cannot create → 403, unpermitted user cannot list → 403). (3) Frontend — `WorkflowDefinition`/`ApprovalMode` types + `createWorkflowDefinition` in `api/workflow.ts`; a **Workflow definitions** browse page (`/workflow/definitions`, gated by `workflow.definition.view`) and a create page (code / bilingual name / approval_mode; captures only the approval *shape*, no rule matrix); permission-gated route + sidebar entry; a `workflow` fa/en i18n block (definitions.{title,subtitle,new,mode}, modes.{SEQUENTIAL,PARALLEL}, parity checked); and an extended `workflow.test.ts`.

**Open gates explicitly NOT implemented** (unchanged; still in `do-not-build-yet.md`): approver-set assignment UI and the approval hierarchy / threshold **content** (Q-054/056, DR-032, #7 — binding a specific business document to a definition + approvers is left to the owning module once policy is confirmed); escalation / delegation / SLA timers; `config`-JSON rule editing beyond mode. No requirement was added, modified, or removed; this entry records the build delta.

**RBAC delta:** none — `workflow.definition.view/manage` already existed.

---

## 2026-08-21 — Foundation: Organization master (Company → Site) hardened + frontend

**Trigger:** The `organization` app (`Company`, `Site`, `Department`, `ProductionCapability`, `SiteCapability` — the company/site scoping roots per DR-040) had shipped in Task 003, but an audit-consistency gap was found: only `SiteCapabilityViewSet` routed writes through the audited service layer, while `CompanyViewSet`, `SiteViewSet` and `DepartmentViewSet` used a plain DRF `ModelViewSet`, so their creates/updates/deletes were neither transactional-with-audit nor `created_by`-stamped — inconsistent with every other master-data module. The scoping roots also had **no** frontend. Source-of-truth: `docs/architecture/organization-master.md`, `docs/architecture/data-lifecycle.md`, DR-040.

**What was built (no requirement text changed):** (1) Backend hardening — `CompanyViewSet`, `SiteViewSet`, `DepartmentViewSet` now extend `AuditedModelViewSet` (permission_map / required_permission unchanged; redundant `permission_classes` removed), so writes run through `apps.core.service` inside a transaction, stamp `created_by`, and emit `EntityCreated/Updated/Deleted` → audit rows (`entity_type` `organization.Company` / `.Site` / `.Department`). No schema migration (behavioural only). (2) Backend test `test_organization.py` proving create persists + audits with `created_by`, unique-code 400 (global for company, per-company for site), soft-delete + `all_objects` + audit DELETE, and a view-only user is 403 on create. (3) Frontend — `api/organization.ts` (Company/Site types + `createCompany`/`createSite`), browse (`CompaniesPage`/`SitesPage`) and create (`CompanyCreatePage`/`SiteCreatePage`, site loads its company `<select>`) pages under `/organization/{companies,sites}`, two permission-gated sidebar entries, an `organization` fa/en block (parity checked) and a vitest api test.

**Open gates explicitly NOT implemented:** none apply — this is un-gated structural foundation; the unique-code rules are pre-existing model constraints, not new business rules. Deliberately out of scope (no confirmed need): department / capability frontend, edit/detail pages, cross-company scoping UI. No requirement was added, modified, or removed; this entry records the build delta.

**RBAC delta:** none — `organization.company.*` / `organization.site.*` / `organization.department.*` were already seeded; no schema migration.

---

## 2026-08-21 — Foundation: Audit log viewer made usable (read-only frontend)

**Trigger:** The platform `audit` app (append-only `AuditLog` + a read-only `AuditLogViewSet` with list/retrieve, RBAC `audit.log.view` already seeded, filters on action/entity_type/entity_id/actor/correlation_id and search over entity_type/entity_id/actor_label) had shipped in Task 003 but had **no** frontend, so the compliance/traceability trail — a capability SLZ cares about deeply (see project conventions) — was invisible to operators. This slice surfaces the existing read API only; it is un-gated foundation and introduces **no** business rule. Source-of-truth: `docs/architecture/audit-log.md`, `docs/architecture/data-lifecycle.md`.

**What was built (no requirement text changed):** frontend only — an `api/audit.ts` layer (typed `AuditLogEntry` / `AuditAction` + a `fetchAuditEntry(id)` retrieve helper) and an **Audit log** page (`/audit/logs`, sidebar entry gated by `audit.log.view`) that lists the trail via `CollectionView` with columns timestamp / actor / action (localized) / entity (`entity_type #entity_id`) / correlation, the search box mapping to the backend `search_fields`. fa/en `audit` block added (15 keys, parity checked) plus a vitest api test. The list is a who/what/when summary; the full before/after JSON is reachable via the retrieve helper for a future diff view. **No** write affordance exists (the trail is append-only by construction).

**Open gates explicitly NOT implemented:** none apply — audit is un-gated foundation. Deliberately out of scope (no confirmed requirement): mutation of audit rows (by design), export / e-signature / tamper-evidence hashing, and a before/after diff modal. No requirement was added, modified, or removed; this entry records the build delta.

**RBAC delta:** none — `audit.log.view` already existed (seeded in Task 003); no backend change, no schema migration.

---

## 2026-08-21 — Foundation: Notifications in-app inbox made usable (tests + frontend)

**Trigger:** The platform `notifications` app (a `Notification` model + a self-authorizing `NotificationViewSet` with `read` / `read-all` / `unread-count` actions) had shipped in Task 003 but was unusable end-to-end: it had **no** frontend inbox and no header entry point, so workflow-generated alerts (approver notified on assignment, requester notified on completion — see the workflow slice) had no surface. This slice completes the *in-app channel* only — a foundation mechanism explicitly marked "safe to build regardless"; email / SMS / push remain deferred delivery interfaces (DR-008, `do-not-build-yet.md` #30). Source-of-truth: `docs/architecture/notifications.md`, `docs/architecture/system-architecture.md`.

**What was built (no requirement text changed):** (1) Backend tests — a `NotificationApiTests` suite proving the viewset is strictly per-user: list/unread-count return only the caller's rows, marking another user's notification is a **404** (not 403 — others' notifications are never disclosed), and read-all touches only the caller's unread. No backend hardening was needed (`get_queryset` already scopes to `request.user`, so the channel is self-authorizing and needs **no** RBAC permission). (2) Frontend — an `api/notifications.ts` layer, a **Notifications** inbox page (`/notifications`, sidebar entry for every authenticated user) listing type/title/body/state with per-row *Mark read* and a header *Mark all read*, a header `NotificationBell` showing a fetch-on-mount unread badge (no polling), fa/en strings (17 keys, parity checked) and a vitest api test. 

**Open gates explicitly NOT implemented** (unchanged; still in `do-not-build-yet.md`): email / SMS / push delivery (DR-008, #30); real-time push / websockets / count polling; and notification preferences / per-type mute (no confirmed business rule). No requirement was added, modified, or removed; this entry records the build delta and confirms the open gates were respected.

**RBAC delta:** none — the in-app channel is self-authorizing (every endpoint scopes to `recipient=request.user`).

---

## 2026-08-21 — Foundation: Workflow / Approvals engine made usable (API hardening + inbox)

**Trigger:** The platform `workflow` app (definition / instance / step models + a self-guarding decision service) had shipped in Task 003 but was unusable end-to-end: it had **no** frontend, no personal approvals inbox, and — a data-integrity gap — the `WorkflowInstanceViewSet.cancel` and list/retrieve endpoints carried no permission class, so any authenticated user could list every instance and cancel any workflow. This slice completes the *engine* (a foundation mechanism explicitly marked "safe to build regardless" and #7 "engine may be built; rules must not be hard-coded"); it introduces **no** business approval policy. Source-of-truth: `docs/architecture/workflow-approvals.md`, `docs/architecture/system-architecture.md`, `do-not-build-yet.md` #7.

**What was built (no requirement text changed):** (1) API hardening — `WorkflowInstanceViewSet` now resolves authorization **per action** in `get_permissions` (list/retrieve require `workflow.instance.view`; `cancel` requires `workflow.instance.manage`; `decision` and the new `mine` inbox require authentication only, because the decision service already self-guards to assigned, still-pending approvers and the inbox only exposes the caller's own steps). This closes the unauthorized-cancel gap. (2) A new `GET instances/mine/` action returning open instances on which the caller holds a `PENDING` step. (3) Frontend — an `api/workflow.ts` layer plus a **My approvals** page (`/workflow/approvals`, sidebar entry visible to every authenticated user) that lists the inbox and drives approve/reject with an optional comment; fa/en strings added (16 keys, parity checked). No approval hierarchy, threshold, escalation, delegation or document-to-workflow wiring was added.

**Open gates explicitly NOT implemented** (unchanged; still in `do-not-build-yet.md`): the **approval hierarchy & thresholds content** (Q-054/056, DR-032, #7 — no matrix seeded; binding a specific business document to a definition + approver set is left to the owning module once policy is confirmed); escalation / delegation / SLA timers; parallel-quorum rules beyond all-must-approve; and email/SMS approval channels (DR-008, deferred). No requirement was added, modified, or removed; this entry records the build delta and confirms the open gates were respected.

**RBAC delta:** two permissions seeded — `workflow.instance.view/manage` (the pre-existing `workflow.definition.view/manage` are unchanged).

---

## 2026-08-21 — Task 005b: Tooling / Cliché Asset (SR-03)

**Trigger:** SR-03 makes the **cliché / sheet (برگ) / set (دست)** printing tooling a first-class asset with usage-life and its own store — an SLZ-specific reality that generic ERPs get wrong (fixed asset or consumable, no per-use life, no dedicated store type). The `engineering` app docstring had explicitly deferred this to "a later Task 005 phase"; the SR-10 `CLICHE` warehouse store type already exists (Task 007). This slice is un-gated: only the tooling *cost model* is blocked (do-not-build-yet #5, Q-004/036), not the asset identity. Source-of-truth: `docs/reconciliation/slz-specific-rules.md` SR-03/SR-10, `docs/architecture/product-engineering.md`.

**What was built (no requirement text changed):** one master-data asset entity — `ToolingAsset` (`SoftDeleteModel`, company-scoped per DR-040; `PROTECT` FKs to `customer` → partners.Partner and optional `customer_product` → engineering.CustomerProduct; `code` unique per company → clean 400; `tooling_type` CLICHE/SHEET/SET; `status` ACTIVE/RETIRED; usage-life counters `usage_life_limit` (nullable — measurement basis is OPEN, no default invented) + `usage_count`; optional `warehouse` pointer validated to be a CLICHE store in the same company; `notes`). `is_life_exceeded` is a pure arithmetic helper (no end-of-life policy). A linked `customer_product` must share the asset's company and customer (integrity, not policy). Lifecycle in `services.py`: `retire_tooling` (ACTIVE→RETIRED) / `reactivate_tooling` (RETIRED→ACTIVE), each guarding the source status (ConflictError `invalid_status_transition`, 409) and emitting `EntityUpdated` (audited); `status` is serializer-read-only so it only moves through these actions. Full audited CRUD via `AuditedModelViewSet`; frontend adds an engineering "Tooling & clichés" browse (usage shown as count/limit, flagged when exceeded) + permission-gated create form, sidebar entry and fa/en strings.

**Open gates explicitly NOT implemented** (unchanged; still in `do-not-build-yet.md`): the tooling **cost model** — customer-paid vs amortized (#5, Q-004/036, DR-030); **automatic** `usage_count` increment from a work-order/operation confirmation (bound to the gated execution/traceability layer, Q-046, #18 — `usage_count` is plain audited master data here); and **artwork revisions** as a separate linked lifecycle (the optional `customer_product` link is the stand-in until the artwork model lands). No requirement was added, modified, or removed; this entry records the build delta and confirms the open gates were respected.

**RBAC delta:** two permissions seeded — `engineering.tooling.view/manage`.

---

## 2026-08-21 — Task 011: Production Order Foundation (work orders)

**Trigger:** Implementation of the make-side committed, un-gated commercial-document slice on top of the Task 005 engineering spine (`engineering.CustomerProduct` / `SpecificationRevision`), the Task 006 manufacturing definition (`manufacturing.BomRevision` / `RoutingRevision`) and the Task 010 sales demand (`sales.SalesOrderLine`). The production order is the manufacturing counterpart of the Task 009 purchase order and Task 010 sales order — it converts confirmed demand into a shop-floor commitment against a frozen engineering definition and is the prerequisite for the later (gated) material-issue / confirmation / genealogy execution layer. Source-of-truth: `docs/architecture/production-order-management.md`, `docs/business-analysis/manufacturing-processes.md`, and `docs/architecture/transactions.md`.

**What was built (no requirement text changed):** one **header-only** transactional document driven by a server-authoritative status state machine — `ProductionOrder` (company-scoped, `number` unique per company, optional `site`; pins `customer_product` → engineering.CustomerProduct and the FROZEN `spec_revision` → engineering.SpecificationRevision, with optional `bom_revision`/`routing_revision` and optional `sales_order_line` demand provenance via SET_NULL; `planned_quantity` + `uom`; nullable `scheduled_start`/`scheduled_end` as plain non-promised fields). Lifecycle (deliberately minimal — execution states absent): DRAFT→RELEASED→COMPLETED→CLOSED, cancellable from DRAFT/RELEASED/COMPLETED. `RELEASED` authorizes the shop floor; `COMPLETED`/`CLOSED` are MANUAL administrative marks (never derived from confirmations or produced-quantity). The order is editable only while DRAFT. No line model is built — material lines and operations already live on the frozen BOM/Routing revisions. Transitions and edits go through the audited write path; every status move emits `EntityUpdated` (not the audit-ignored `EntityApproved`) and is recorded.

**Open gates explicitly NOT implemented** (unchanged; still in `do-not-build-yet.md`): material issue / consumption / backflush and roll/lot genealogy (SR-08, #19 — bound to the traceability + stock layer gated on Q-046, #18, highest priority); operation confirmations, produced/scrap quantity capture, downtime and the allowed-scrap/downtime threshold tables (SR-05/SR-06, #9/#12 — `COMPLETED` is a manual flag, nothing is rolled up); inline/final QC results with auto stop + rework spawning (SR-06, row 20 — needs Q-046); margin-based prioritization (SR-13) and the outsourcing execution locus (SR-14/DR-043/NQ-004 — no priority or make-vs-buy rule invented); and ATP / promised-date + capacity feasibility (SR-12/R-30, #12 — scheduled dates are plain fields, nothing computed). No requirement was added, modified, or removed; this entry records the build delta and confirms the open gates were respected.

**RBAC delta:** two permissions seeded — `production.order.view/manage`.

---

## 2026-08-21 — Task 010: Sales Order Management (customer orders)

**Trigger:** Implementation of the sell-side confirmed, un-gated commercial-document slice on top of the Task 004 partner masters (`partners.Customer`) and the Task 005 engineering spine (`engineering.CustomerProduct`). Sales is the demand origin for this made-to-order business — the sell-side mirror of the Task 009 procurement documents and a prerequisite for later pricing/proforma, ATP promising, allocation, shipment and invoicing. Source-of-truth: `docs/architecture/sales-order-management.md`, `docs/business-analysis/business-processes.md`, and `docs/architecture/transactions.md`.

**What was built (no requirement text changed):** one header+line transactional document driven by a server-authoritative status state machine — `SalesOrder` (company-scoped, `number` unique per company, optional `site`, `customer` → partners.Customer, `order_date`/`requested_date` nullable, `currency` default IRR as a plain code) with `SalesOrderLine` (customer_product → engineering.CustomerProduct + quantity + uom, nullable `unit_price`). Lifecycle (deliberately minimal — fulfilment states absent): DRAFT→CONFIRMED→CLOSED, cancellable from DRAFT/CONFIRMED. The order is editable only while DRAFT. Transitions and edits go through the audited write path; every status move emits `EntityUpdated` (not the audit-ignored `EntityApproved`) and is recorded.

**Open gates explicitly NOT implemented** (unchanged; still in `do-not-build-yet.md`): sales inquiry → quotation / proforma and the pricing algorithm (R-14, #11 — `unit_price` is a nullable manual field, no price is derived); ATP / promised delivery date from capacity + stock (SR-12, #12 — `requested_date` records only what the customer asked for, never a promise); allocation / reservation / shipment / delivery note / invoicing (bound to the traceability + stock layer gated on Q-046, #18, and Finance, #23/#26); credit management, settlement terms, and over/under-delivery tolerance enforcement (DR-028 — the tolerance field on partners.Customer is data only); multi-level packaging & marking per order (SR-11, #25); new-vs-repeat routing to engineering (A-001, #4); and the drawing/proof customer-approval gate (R-16, #6). No requirement was added, modified, or removed; this entry records the build delta and confirms the open gates were respected.

**RBAC delta:** two permissions seeded — `sales.order.view/manage`.

---

## 2026-08-21 — Task 009: Procurement Foundation (requisitions & purchase orders)

**Trigger:** Implementation of the procurement domain's confirmed, un-gated commercial-document slice on top of the Task 004 partner/material masters and the Task 007 inventory scoping. Procurement follows quality in the roadmap (`docs/reconciliation/current-to-future-system.md`); the PR→PO paper trail is a prerequisite for later goods receipt, supplier-invoice matching, and MRP. Source-of-truth: `docs/architecture/procurement-foundation.md`, `docs/business-analysis/business-processes.md`, and `docs/architecture/transactions.md`.

**What was built (no requirement text changed):** two header+line transactional documents driven by a server-authoritative status state machine — `PurchaseRequisition` (company-scoped, `number` unique per company, optional `site`/`requested_by`/`need_by_date`) with `PurchaseRequisitionLine` (material + quantity + uom), and `PurchaseOrder` (company-scoped, `number` unique per company, `supplier` → partners.Supplier, `currency` default IRR as a plain code) with `PurchaseOrderLine` (material + quantity + uom, nullable `unit_price`, optional link back to a `requisition_line`). Requisition lifecycle: DRAFT→SUBMITTED→APPROVED/REJECTED, cancellable from DRAFT/SUBMITTED/APPROVED. Order lifecycle (truncated before goods receipt): DRAFT→APPROVED→SENT→CLOSED, cancellable from DRAFT/APPROVED/SENT. Both documents are editable only while DRAFT. Transitions and edits go through the audited write path; every status move emits `EntityUpdated` (not the audit-ignored `EntityApproved`) and is recorded.

**Open gates explicitly NOT implemented** (unchanged; still in `do-not-build-yet.md`): goods receipt / GRN and the two-stage temporary→QC→definitive receipt (SR-09, #17 — bound to the traceability + stock layer gated on Q-046); MRP / auto-requisition (#14); RFQ / sourcing / supplier quotes; approval hierarchy & monetary thresholds (#7 — `approve` is a single manual permission-gated transition with NO hard-coded threshold or routing rule); import / foreign trade / sanctions / FX (`currency` is a plain code, no conversion); supplier invoice / accounts-payable / 3-way match (Finance, #23); and inventory valuation from PO pricing (#1/#2 — `unit_price` captured but never used to value stock). No requirement was added, modified, or removed; this entry records the build delta and confirms the open gates were respected.

**RBAC delta:** four permissions seeded — `procurement.requisition.view/manage`, `procurement.order.view/manage`.

---

## 2026-08-21 — Task 008: Quality Foundation (characteristics & quality plans)

**Trigger:** Implementation of the quality domain's confirmed definition slice on top of the Task 006 manufacturing definition and the Task 005 specification spine. Quality follows manufacturing/inventory in the roadmap (`docs/reconciliation/current-to-future-system.md`) and its plan definition is a prerequisite for later inline/final QC execution and two-stage goods receipt. Source-of-truth: `docs/architecture/quality-foundation.md`, skill `06-quality`, `docs/business-analysis/quality-model.md`, and `docs/architecture/versioning.md`.

**What was built (no requirement text changed):** a company-scoped `QualityCharacteristic` catalogue (what is measured, a free-text `method`/standard — Q-039 OPEN, a generic `datatype`, optional `default_uom`, `code` unique per company, soft-retire via `is_active`) and a versioned `QualityPlan` (root → `QualityPlanRevision` → `QualityPlanItem`) bound to one `engineering.SpecificationRevision`, unique per spec revision. Plan items bind a characteristic to an optional `work_center` + free-text `stage_label`, with nullable `lower_limit`/`upper_limit`/`target` (no invented tolerance default), free-text `sampling` (Q-040 OPEN), optional `method_override`, and a descriptive `is_mandatory` flag. The versioned plan reuses the generic draft → activate → supersede lifecycle service; all writes are audited.

**Open gates explicitly NOT implemented** (unchanged; still in `do-not-build-yet.md`): quality CHECK execution & results (measured values, PASS/FAIL/CONDITIONAL) — append-only records tied to a lot/roll/work order/batch, which requires the traceability + stock layer gated on Q-046 (#18, highest priority); non-conformance (NCR) / QC_HOLD, disposition, and scrap & rework reason codes (Q-041/Q-043/Q-016·042, #12); COA issuance (Q-045) and formal recall/CAPA/8D (Q-044, #31); and any single terminal inspection gate or hard-coded plan/characteristic/tolerance/sampling set (skill 06 FORBIDDEN list, #11). No requirement was added, modified, or removed; this entry records the build delta and confirms the open gates were respected.

**RBAC delta:** four permissions seeded — `quality.characteristic.view/manage`, `quality.plan.view/manage`.

---

**Trigger:** Implementation of the inventory domain's confirmed master-data slice on top of the Task 006 manufacturing definition. The inventory phase follows manufacturing in the roadmap (`docs/reconciliation/current-to-future-system.md`) and is a prerequisite for later production execution. Source-of-truth: `docs/architecture/inventory-foundation.md`, skill `05-inventory-supply-chain`, `docs/business-analysis/inventory-model.md`.

**What was built (no requirement text changed):** two master records — `Warehouse` (company-scoped, optionally site-pinned, `code` unique per company, soft-deletable, `is_active`) carrying the SR-10 special `store_type` (general, raw material, WIP, finished goods, scrap, quarantine, cliché, line-side, consignment, stagnant, shipping staging, returns) and `WarehouseAccess` (per-user grant to one warehouse at `VIEW`/`OPERATE`, unique per warehouse+user, SR-10). All writes go through the audited `AuditedModelViewSet` path (`inventory.Warehouse` / `inventory.WarehouseAccess` audit entities). No bespoke service layer — the transactional operations that would justify one are gated.

**Open gates explicitly NOT implemented** (unchanged; still in `do-not-build-yet.md`): lot/roll/batch identity, serialization, and genealogy (Q-046, #18 — highest-priority gate; C-003 forbids migrating the traceability schema until roll serialization vs. lot+count is decided); stock movements and the kardex/stock ledger (no on-hand quantity anywhere); two-stage goods receipt (SR-09) and quarantine→release flow (the `QUARANTINE` store *type* exists as data only); reservations/allocations, consumption permit, and issue method / FEFO (Q-048/#21, Q-051/#16); inventoried BOM levels / stocking granularity (Q-026/#19, Q-049/#20); recall (#31); and Location/Zone/bin sub-structure (deferred behind Q-047 — a warehouse is the finest storage grain in this slice). No requirement was added, modified, or removed; this entry records the build delta and confirms the open gates were respected.

**RBAC delta:** four permissions seeded — `inventory.warehouse.view/manage`, `inventory.warehouseaccess.view/manage`.

---

## 2026-08-21 — Task 006: Manufacturing (BOM & Routing)

**Trigger:** Implementation of the manufacturing module — the engineering definition of how a product is made — on top of the Task 005 specification spine. Source-of-truth: `docs/architecture/manufacturing-bom-routing.md`, skill `03-manufacturing-mes`, `docs/business-analysis/bom-and-routing.md`, and `docs/architecture/versioning.md`.

**What was built (no requirement text changed):** resource masters `WorkCenter` and `Machine` (data-driven `capability_profile` JSON — no hard-coded machine logic, constraint #9), plus two versioned structures bound to a `SpecificationRevision` — `BillOfMaterials` (root → `BomRevision` → `BomLine`) and `Routing` (root → `RoutingRevision` → `RoutingOperation`). Both revisions reuse a single generic draft → activate → supersede lifecycle service (immutable once non-DRAFT). All writes are audited; the lifecycle lives in the service layer under `atomic_with_events`.

**Open gates explicitly NOT implemented** (unchanged; still in `do-not-build-yet.md`): BOM consumption bases / waste factors / standard scrap % (Q-027, #9) — `consumption_basis` kept as free text, `scrap_pct` nullable with no invented default; standard routing templates & stage-skip rules (Q-029, #10); inventoried intermediates / real BOM levels (Q-026, #19) — `output_material` optional, no level derived; alternates/substitutes (A-014/Q-028), changeover matrix, machine-qualification pools, skills, QC-plan and tooling links; outsourcing execution locus (DR-043/NQ-004); and all production execution (production/work orders, consumption, genealogy). No requirement was added, modified, or removed; this entry records the build delta and confirms the open gates were respected.

**RBAC delta:** eight permissions seeded — `manufacturing.workcenter.view/manage`, `manufacturing.machine.view/manage`, `manufacturing.bom.view/manage`, `manufacturing.routing.view/manage`.

---

## 2026-08-21 — Task 005: Product Engineering (versioned specification)

**Trigger:** Implementation of the product-engineering module — the versioned technical specification — on top of the Task 004 master-data foundation. Source-of-truth: `docs/architecture/product-engineering.md`, skill `04-packaging-engineering`, and `docs/architecture/versioning.md`.

**What was built (no requirement text changed):** the specification *spine* and its mechanical lifecycle only — `CustomerProduct` (versioned root, manual code), `SpecificationRevision` (draft → activate → supersede, immutable once non-DRAFT), ordered `SpecLayer`, ink `SpecColor` (ink must be `Material` subtype `INK`), and a typed extensible `SpecParameter`. All writes are audited; the lifecycle lives in the service layer under `atomic_with_events`.

**Open gates explicitly NOT implemented** (unchanged; still in `do-not-build-yet.md`): spec-revision *trigger*/approver policy (Q-024, #7/#13); SKU/parameter-derivation scheme (Q-019 / NQ-005, #14); default tolerance values (Q-022) — modelled as nullable with no invented default; canonical bag-type list (Q-014/Q-020) — kept as free text; tooling/cliché cost model and mandatory-sampling rules (#5/#15); Artwork and Tooling/Cliché as separate linked lifecycles. No requirement was added, modified, or removed; this entry records the build delta and confirms the open gates were respected.

**RBAC delta:** four permissions seeded — `engineering.customerproduct.view/manage`, `engineering.specification.view/manage`.

---

**Trigger:** A newly-supplied official SLZ document, `docs/reference/NEPTA_ERP_Feasibility_Study.md` (NEPTA.ERP.SLC.FZS V1.5, dated 1402/09 ≈ 2023-12), was read and reconciled against Task 001 (business-analysis) and Task 002 (requirements). Per the information hierarchy in `docs/SLZ-SOURCE-OF-TRUTH.md`, this official document **outranks** earlier technical proposals and generic ERP conventions. Contradictions are surfaced, not resolved.

**Full analysis:** `docs/reconciliation/slz-system-vs-task001.md`, `slz-system-vs-requirements.md`, `slz-domain-model.md`, `slz-actual-workflow.md`, `slz-specific-rules.md`, `master-data-impact.md`, `current-to-future-system.md`.

### A. Requirements CONFIRMED by the document (no text change; status/confidence raised)

FR-001/013, FR-002/003/031/035, FR-009/010/012, FR-020/021/022, FR-024, FR-034, FR-040/041/042/048, FR-043/045, FR-044, FR-050/053/055, FR-057, FR-059, FR-070/071/072/073/074, FR-076, FR-080/081/082, FR-100, FR-110/114, FR-113, NFR-010/011, NFR-022 — all now have direct evidence in the SLZ document. See `slz-system-vs-requirements.md` §1.

### B. Requirements MODIFIED (scope/shape change; text to be revised when Task 004+ implements)

1. **Org model → multi-company + multi-site.** Company (NEPTA group) and Site (Tehran/Saveh) become first-class; production capability & capacity are **site-scoped**. *Why:* SLZ is one of six NEPTA companies; phase-1 = SLZ + Helena (blown film + cutting only). *Evidence:* R-01/02/03. *Decision:* DR-040 (CONFIRMED), DR-041 (OPEN).
2. **Operation model → outsourceable.** A routing operation may be executed at this site, a sister company, or an external vendor, with costing & QC on return. *Why:* production outsourcing (برون‌سپاری). *Evidence:* R-32. *Decision:* DR-043 (OPEN, NQ-004).
3. **Material → subtyped.** resin/masterbatch, ink (مرکب), solvent (حلال), consumable, packaging, regrind; MRP treats them distinctly. *Why:* MRP explicitly spans RM/consumables/ink/solvent. *Evidence:* R-31. *Decision:* DR-042 (CONFIRMED).
4. **Product spec → explicit fields added.** MSDS/storage, ink/color formulation, targets (تارگت), per-packaging-level marking (مارکینگ), pallet spec. *Why:* product-master content in the engineering section. *Evidence:* R-21, R-17.
5. **Warehouse → special store types + per-user access + consumption permit.** scrap, quarantine, cliché, line-side, consignment, stagnant. *Evidence:* R-40.
6. **Costing → reconcile with expected full finance domain.** *Why:* the business plainly expects finance (cost, treasury, AR/AP, settlement date, assets, payroll). *Evidence:* R-45. Reinforces contradiction C-006.
7. **RBAC → company/site-scoped + sales lines by product group.** *Evidence:* R-01/R-18.

### C. Requirements ADDED (new, introduced by the document)

New requirement placeholders (to be numbered when their phase begins): FR-NEW-CRM (CRM domain), FR-NEW-FIN (finance domain), FR-NEW-HR (HR domain), FR-NEW-TRADE (import/foreign-trade + sanctions/FX), FR-NEW-OUTSRC (outsourced ops), FR-NEW-RECYCLE (recycling/grinding → regrind), FR-NEW-SKU (SKU/parameter derivation), FR-NEW-MOUNT (print mounting calc), FR-NEW-DELEST (delivery/ATP estimation), FR-NEW-CAP (capacity table by product×machine×site), FR-NEW-MSET (machine-settings library). See `slz-system-vs-requirements.md` §3.

### D. Requirements REMOVED

None. The manufacturing-centric baseline stands. The only rescoping is **strategic and contingent**: if the business reaffirms the document's **buy Microsoft Dynamics 365 F&O** recommendation, the entire custom **build** requirement set changes character (configuration vs. construction). Escalated as DR-000 / NQ-001 — not resolved here.

### E. Assumptions changed

- **INVALIDATED:** implicit single-company assumption (SLZ is one of six NEPTA companies).
- **CONFIRMED:** A-001, A-003, A-005, A-006, A-011, A-013, A-014, A-018, A-019, A-020, A-021.
- **PARTIALLY CONFIRMED:** A-002 (drawing/proof approval confirmed; physical sample still open, Q-003); A-022 (real units listed; full RBAC still open, Q-053).

### F. New open questions raised (NQ-###)

- **NQ-001 (CRITICAL)** Build vs buy — custom Django vs recommended MS Dynamics 365 F&O.
- **NQ-002** Exact company/site list beyond SLZ + Helena.
- **NQ-004** Outsourced-operation modeling (internal vs external, costing, QC-on-return).
- **NQ-005/SKU** Exact SKU/parameter-derivation formulas.
- **NQ-007** Print-mounting calculation rules.
- **NQ-008** Multi-level packaging & marking model.
- **NQ-009** CRM domain phasing.
- **NQ-010** Finance domain phasing (reinforces C-006).

### G. Decision-register impact

Added DR-000, DR-040, DR-041, DR-042, DR-043, DR-044; flagged DR-001/002/011 as CONFLICT (build-vs-buy); added evidence to DR-006, DR-036, DR-007. See `decision-register.md`.

### H. Traceability preserved

All original FR/NFR/DR/A/Q/C IDs are retained; this changelog only **adds** IDs (NQ-###, DR-04x, FR-NEW-*) and **annotates** statuses. No historical ID was renumbered or deleted. `traceability.md` remains valid; new reconciliation IDs (R-01..R-47) map document evidence to requirements in `slz-system-vs-task001.md`.

**Net effect on readiness:** platform foundation (Task 003) remains validated. **Domain implementation (Task 004+) is now gated on NQ-001 and NQ-002** in addition to previously open business decisions. **No application code was written in Task 004A.**

---

## 2026-08-21 — Business decision: NQ-001 (Build vs Buy) RESOLVED → custom build

**Trigger:** SLZ business confirmed the direction while authorising Task 004.

**Decision:** SLZ will **build a custom ERP/MES from scratch**. The MS Dynamics 365 F&O recommendation was **considered and rejected** for this project. Rationale: the system is specialised around SLZ's actual made-to-order flexible-packaging operations; the goal is to fit the system to SLZ, not SLZ to a generic ERP.

**Changes:**
- **NQ-001 → REJECTED/RESOLVED**; **DR-000 → CONFIRMED (Custom build)**.
- DR-001/002/011 build-vs-buy conflict flags **cleared** (Django/DRF, PostgreSQL, React/TS unblocked; still technical proposals).
- Domain implementation is **no longer gated on NQ-001**. Task 004 (Master Data) authorised to proceed.
- `SLZ-SOURCE-OF-TRUTH.md` and `decision-register.md` updated accordingly.
- Architecture is **not** changed on account of the former D365 recommendation.

**Still open:** NQ-002 (exact company/site list beyond SLZ + Helena) and all parametric business rules.

---

## 2026-08-21 — Task 004: Master Data Foundation (implementation)

Full detail: `docs/architecture/master-data.md` and the Task 004 final report.

**Built (identity + classification only):**
- `organization.SiteCapability` (site-scoped production capability, SR-15; audited).
- `partners` app — `Partner` (company-scoped, ≥1 role enforced by DB `CheckConstraint` + serializer, sanction flag), optional `Customer`/`Supplier` role extensions, `Contact`, `Address`.
- `catalog` app — `UnitOfMeasure` + `UomConversion` (same-dimension, distinct, positive-factor validation), taxonomy `ProductType → ProductClass → ProductFamily`, `ProductGroup` (sales-line axis), **thin** `Product` (identity + taxonomy + base UoM only), `Material` (subtype discriminator; optional planning fields).
- `hr` app — minimal `Employee` (company-scoped; optional site/department/user links).

**How:** all new writes go through `apps/core/service.py` + `AuditedModelViewSet` so they emit domain events and are audited automatically (the pre-existing `organization` Company/Site/Department CRUD remains unaudited — noted as a follow-up). RBAC codes seeded in `seed_rbac.py`. Frontend adds a permission-aware Master-data section (browse screens + Partner create), bilingual fa/en with RTL/LTR.

**Backend tests added:** partners (create+audit, role rule, unique code, soft-delete, permissions), catalog (UoM, conversion validation, taxonomy, thin product, material subtype), hr (create, uniqueness, permissions), organization SiteCapability (create+audit, uniqueness, permissions). Frontend: `masterData` API query-builder unit tests.

**Deferred to Task 005+ (unchanged):** product spec/revisions, formulations, drawings/marking, SKU derivation, print mounting, tooling/clichés, BOM/routing, warehouse store logic/kardex, CRM, full Finance/HR/Maintenance/foreign-trade. Open parametric values (e.g. DR-028 delivery tolerance) modelled nullable with no invented default.

**Not verified at runtime:** migrations / Django test suite / frontend build could not run in the sandbox (package install unavailable); Python checked via `py_compile`, TypeScript reviewed by hand. Repo commits no migration files → run `makemigrations && migrate` first (see architecture doc).
