# Multi-Tenancy Preparation — Q-055/Q-053 Dependency Map

Status: **PREPARATION DOCUMENT — no behavior implemented.** The data-scoping
policy itself is OPEN (`decision-register.md` DR-033; questions Q-053 role
catalogue / Q-055 scoping rules). This document maps every place that will need
changes when SLZ confirms that policy, so implementation becomes systematic
rather than a repository-wide rediscovery exercise.

> **Security context.** Until Q-055 resolves, the system is
> **single-tenant-open**: there is no user↔company binding, so any authenticated
> user holding a module permission can access any company's records of that
> module by ID. Do not host two unrelated companies before this gate closes.
> Serializer-level cross-company *consistency* (DR-040) is already enforced;
> what is missing is *visibility* scoping.

## 1. Current state

* ``identity.User`` has **no** company/site FK and no membership table.
* Every domain viewset serves an unfiltered default queryset (``objects.all()``).
* The only existing user↔resource grants: notifications/workflow-inbox are
  recipient/approver-scoped by design, and ``inventory.WarehouseAccess`` is a
  per-user warehouse grant — **the closest in-repo precursor pattern** for a
  future user↔company/site access model.

## 2. Model inventory

### 2a. Direct ``company`` FK (write paths assign it; reads unscoped today)

| App | Model | Also site-FK | Versioned root |
|---|---|---|---|
| catalog | Product | – | – |
| catalog | Material | – | – |
| partners | Partner | – | – |
| engineering | CustomerProduct | – | ✔ root |
| engineering | ToolingAsset | – | – |
| hr | Employee | ✔ | – |
| inventory | Warehouse | ✔ | – |
| manufacturing | WorkCenter | ✔ | – |
| manufacturing | Machine | ✔ | – |
| procurement | PurchaseRequisition | ✔ | – |
| procurement | PurchaseOrder | ✔ | – |
| production | ProductionOrder | ✔ | – |
| quality | QualityCharacteristic | – | – |
| sales | SalesOrder | ✔ | – |

### 2b. Indirectly scoped via parent chain

| Model | Path to company |
|---|---|
| sales.SalesOrderLine | order → company |
| procurement.PurchaseRequisitionLine / PurchaseOrderLine | header → company (DR-040 invariants already block cross-company lines) |
| partners.Customer / Supplier | 1:1 partner → company |
| partners.Contact / Address | partner → company |
| engineering.SpecificationRevision | root (CustomerProduct) → company |
| engineering.SpecLayer / SpecColor / SpecParameter | revision → root → company |
| manufacturing.BillOfMaterials / BomRevision / BomLine | spec_revision → CustomerProduct → company |
| manufacturing.Routing / RoutingRevision / RoutingOperation | spec_revision → CustomerProduct → company |
| quality.QualityPlan / QualityPlanRevision / QualityPlanItem | spec_revision → CustomerProduct → company |

### 2c. Site-scoped only (company reached through site)

organization.Site → company · Department → site · SiteCapability → site

### 2d. Generic entity-reference surfaces (hardest cases)

These carry ``entity_type``/``entity_id`` strings with **no company FK**:

* ``documents.Attachment`` — list/filter/upload/download against arbitrary targets.
* ``workflow.WorkflowInstance`` / ``ApprovalStep`` — generic entity register.
* ``audit.AuditLog`` — platform-global append-only trail.

Q-055 implementation must decide how these resolve visibility through their
target entity at query time (join-to-target or denormalized ``company`` column
backfilled per record). **Decision required — do not guess.**

### 2e. Global by design (never company-scoped)

Units of measure + conversions, product taxonomy (Group/Type/Class/Family),
MaterialSubtype, Spec-format/process/surface choice lists, localization,
identity (users/roles/permissions), notifications, audit trail, workflow engine
definitions.

## 3. Change-point map when Q-055 lands

1. **Read choke point (single layer).** All direct-scoped viewsets inherit
   ``AuditedModelViewSet`` and use default querysets. Proposed extension point
   *(PROPOSAL — not implemented)*: a company-scoping hook on the shared base
   viewset (e.g. queryset manager ``for_user(user)`` driven by a policy module),
   so scoping lands once, not in 14+ places. Indirect children scope via their
   parent FK join.
2. **Write-path assignment.** Create payloads currently take ``company`` from
   the client. Policy decision required: derive from the user's active/membership
   company vs. validate client value against memberships. DR-040-style
   serializer validation is the established precedent for cross-company writes.
3. **Generic-entity surfaces (§2d).** Require target-resolution checks on read
   *and* write, or a denormalized company column with backfill migration.
4. **Permissions.** No change expected — RBAC codes stay as-is; scoping narrows
   *which rows* they apply to.
5. **Audit trail.** Unaffected (global append-only trail is correct for the
   platform); the viewer may later want company filtering.
6. **Frontend.** Create forms currently render free company selectors; after
   Q-055 they must offer only permitted companies from a server-derived source
   (e.g. ``/auth/me/`` extension). List pages need no route changes — scoping is
   server-side. Detail pages need no change — deep links to other companies'
   records become 404s by queryset exclusion.
7. **Tests.** Each directly-scoped viewset gains one cross-company regression:
   Company-A user requests a known Company-B id ⇒ enveloped 404 (list excludes
   it; detail hides it). The fuzz suite (`test_input_fuzz.py`) already pins the
   envelope shape these tests will assert.

## 4. Explicitly out of scope until decided

Membership storage shape, multi-company users, default-company selection,
company switching UI, cross-company reporting, attachment retroactive
re-scoping — all downstream consequences of Q-055 answers.
