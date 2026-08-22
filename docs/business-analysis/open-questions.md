# Open Questions + Final Consolidated Output

This document has two parts:

- **Part A — Open Questions & Assumptions register** (everything requiring SLZ human validation).
- **Part B — Final consolidated output** (domain model, entities, relationships, workflows, state machines, architecture, DB structure, risks, recommended next task) as required by the task brief.

---

# PART A — Assumptions & Open Questions Register

## A.1 Assumptions (industry defaults — validate before building)

| ID | Assumption | Doc |
|----|-----------|-----|
| A-001 | New-product (ETO) vs repeat-order (MTO) are distinct process paths. | business-processes |
| A-002 | A sampling / first-article approval loop exists before bulk production. | business-processes |
| A-003 | Printing tooling (plates/cylinders) is a distinct procured/created object with its own lifecycle. | business-processes |
| A-004 | Commodity resins are stocked/replenished; specialty materials bought to order. | business-processes/inventory |
| A-005 | QC is inline at every stage, not only final. | business/quality |
| A-006 | Reverse flows exist (change orders, cancellations, RMA, rework, over/under delivery). | business |
| A-007 | Process chain sequence (extrusion→print→laminate→slit→convert→pack). | manufacturing |
| A-008 | Adhesive curing/aging stage exists. | manufacturing |
| A-009 | Slitting creates 1→N roll genealogy. | manufacturing |
| A-010 | Final inspection & packing stage. | manufacturing |
| A-011 | Each stage has expected yield & scrap %. | manufacturing/bom |
| A-012 | BOM consumption is per-area/weight/length, not only per-piece. | bom |
| A-013 | Setup waste (fixed/run) vs running waste (%) tracked separately. | bom |
| A-014 | BOM lines may allow alternate materials. | bom |
| A-015 | Scrap carries accumulated cost to the stage scrapped. | costing |
| A-016 | Tooling cost is either customer-paid or amortized. | costing |
| A-017 | Over/under production affects unit cost & invoicing. | costing |
| A-018 | Defined inspection points per stage. | quality |
| A-019 | Reservations = soft allocation; shortfalls raise purchase requests. | inventory |
| A-020 | RM lots (and some FG) have shelf-life/expiry. | inventory |
| A-021 | Multiple UoMs with conversions (kg↔m↔m²). | inventory |
| A-022 | Proposed role catalogue. | roles |

## A.2 Open questions (no safe default — need SLZ answer)

**Terminology & scope**
- **Q-001** Confirm Persian shop-floor terminology for all domain terms.
- **Q-002** Repeat vs new-product order ratio.
- **Q-003** Is physical sample sign-off required per new job / per repeat?
- **Q-006 / Q-037** Over/under-delivery tolerance (±%) commercial rule?

**Products & specs**
- **Q-014 / Q-020** Enumerate bag/pouch/format types produced.
- **Q-019** Internal product code vs customer code; numbering scheme.
- **Q-021** List of special effects offered.
- **Q-022** Standard tolerance defaults per attribute/product group.
- **Q-023** Required certifications/compliance (food contact, ISO, halal…).
- **Q-024** What triggers a new spec revision vs minor correction; approver.
- **Q-025** Do artwork changes force a new product-spec revision?

**Manufacturing**
- **Q-010** Which finishing effects are inline vs separate passes/machines?
- **Q-011 / Q-015** Full machine list + capability data per stage.
- **Q-012** Extrusion layer count / coextrusion / corona inline?
- **Q-013** Max print colors; ink chemistry (solvent/water/UV).
- **Q-016 / Q-042** Standard scrap % and reason codes per stage.
- **Q-017** OEE tracking now or later? Existing PM scheduling?
- **Q-018** Current planning method; bottleneck stage(s).

**BOM / routing**
- **Q-026** Which intermediates are stocked/inventoried vs flow-through.
- **Q-027** Consumption bases & standard waste/overage per material.
- **Q-028** Material substitution allowed on floor? QC approval?
- **Q-029** Standard routings per product group; stage skips.
- **Q-030** BOM/routing release approval authority.

**Costing**
- **Q-004 / Q-036** Tooling in-house vs outsourced; customer-paid vs amortized.
- **Q-005 / Q-050** Which materials stocked vs bought-to-order; allocation policy.
- **Q-031** Current costing method & currency; inflation handling.
- **Q-032** Cost taxonomy completeness (tooling amort, freight, QC, duty, disposal?).
- **Q-033** Rates & allocation drivers (labor/machine/energy/maint/overhead).
- **Q-034** Material valuation method (FIFO / weighted-avg / lot-actual).
- **Q-035** Scrap regrind/resale value & absorption.
- **Q-038** Priority profitability dimensions.

**Quality**
- **Q-039** Inspection plans, methods/standards, equipment per stage.
- **Q-040** Sampling rules (100% vs AQL).
- **Q-041** Formal CAPA/8D vs lightweight disposition.
- **Q-043** Reworkable vs always-scrap defects; customer approval to ship rework.
- **Q-044** Formal recall capability required?
- **Q-045** Which products need COA; required fields.

**Inventory**
- **Q-046** Serialize rolls vs lot+count tracking.
- **Q-047** Number of warehouses; bin-level tracking needed?
- **Q-048** Backflush vs explicit lot issue.
- **Q-049** Traceability granularity (roll/pallet/carton).
- **Q-051** Shelf-life/expiry enforcement (FEFO)?
- **Q-052** Required UoMs & conversions.

**Roles / audit**
- **Q-053** Validate role list vs real org.
- **Q-054** Approval thresholds & multi-step approvals matrix.
- **Q-055** Data-scoping needs.
- **Q-056** Maker≠checker documents.
- **Q-057** Record retention & regulatory audit requirements.
- **Q-058** SSO/AD; shop-floor kiosk/badge login.

**Platform / non-functional (new here)**
- **Q-059** Expected users (concurrent), sites, transaction volume/day → sizing.
- **Q-060** Deployment: on-prem (common for Iranian factories / connectivity/sanction constraints) vs cloud? Data-residency rules?
- **Q-061** Existing systems to integrate/migrate (accounting, current spreadsheets, label printers, scales, lab instruments, barcode scanners)?
- **Q-062** Do machines expose data (PLC/SCADA/OPC-UA) for automatic confirmations, or is all shop-floor input manual?
- **Q-063** Primary language of the shop-floor UI (fa first?) and reporting language for customers/management.
- **Q-064** Sanction-aware tech constraints: any restrictions on cloud providers, licensed software, or specific libraries?

---
# PART B — Final Consolidated Output

## B.1 Domain model (overview)

The domain divides into six bounded areas of a **modular monolith**. Manufacturing is the core; accounting is deliberately excluded (constraint #10).

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              SLZ ERP / MES                                 │
│                                                                            │
│  [Commercial]            [Engineering]            [Manufacturing]          │
│  Customer                Product Spec (v)          Production Order         │
│  Inquiry                 Artwork (v)               Work Order               │
│  Quotation (v)           Printing Tooling          Work Center / Machine    │
│  Sales Order             BOM (v) / Routing (v)     Production Batch / Roll   │
│                          Color/Ink recipe          Scrap / Rework / Downtime │
│                                                                            │
│  [Inventory & Trace]     [Quality]                 [Procurement]           │
│  Warehouse / Location    Quality Plan / Check       Supplier                │
│  RM / Lot / Roll         Quality Alert (NCR)        Purchase Request         │
│  Stock Movement          COA                        Purchase Order / GRN     │
│  Genealogy / Reservation Disposition                                        │
│                                                                            │
│  [Costing] Cost Record / Rates / Settlement / Profitability                 │
│  [Maintenance] Maintenance Order / Downtime                                 │
│  [Platform] Users/Roles/RBAC · Audit log · i18n (fa/en) · Jalali/Gregorian  │
└──────────────────────────────────────────────────────────────────────────┘
```

## B.2 Main entities (catalogue)

**Commercial:** Customer, ContactPerson, CustomerProduct, Inquiry, Quotation, QuotationRevision, QuotationLine, SalesOrder, SalesOrderLine.
**Engineering:** ProductSpecification, ProductSpecificationRevision, SpecLayer, SpecParameter (typed, toleranced), Artwork, ArtworkRevision, ColorRecipe, PrintingTooling, ToolingSet.
**BOM/Routing:** Bom, BomRevision, BomLine, Routing, RoutingRevision, Operation, WorkCenter, Machine, MachineCapabilityProfile, ChangeoverMatrix.
**Manufacturing:** ProductionOrder, WorkOrder, WorkOrderConfirmation, ProductionBatch, Roll, ScrapRecord, ReworkRecord, DowntimeEvent.
**Inventory:** Warehouse, Location, Item (RM/SFG/FG/packaging), RawMaterialLot, StockMovement, StockReservation, BatchGenealogy, UomConversion.
**Quality:** QualityPlan, QualityCharacteristic, QualityCheck, QualityAlert(NCR), Disposition, COA.
**Procurement:** Supplier, PurchaseRequest, PurchaseOrder, PurchaseOrderLine, GoodsReceipt(GRN).
**Costing:** CostRate, CostRecord (per event), OrderCostSettlement, ProfitabilityRecord.
**Maintenance:** MaintenanceOrder.
**Platform:** User, Role, Permission, ApprovalRule, AuditLogEntry.

## B.3 Key entity relationships (text ERD)

```
Customer 1───N CustomerProduct 1───N ProductSpecification 1───N ProductSpecificationRevision
ProductSpecificationRevision 1───N SpecLayer
ProductSpecificationRevision 1───N SpecParameter
ProductSpecificationRevision 1───N ArtworkRevision (ref)   Artwork 1───N ArtworkRevision
ArtworkRevision 1───N PrintingTooling
ProductSpecificationRevision 1───1 BomRevision (active)    Bom 1───N BomRevision 1───N BomLine
ProductSpecificationRevision 1───1 RoutingRevision(active) Routing 1───N RoutingRevision 1───N Operation
Operation N───1 WorkCenter 1───N Machine
BomLine N───1 Item ;  BomLine (produced-at) N───1 Operation

SalesOrder 1───N SalesOrderLine N───1 CustomerProduct (+ specific ProductSpecificationRevision)
SalesOrderLine 1───N ProductionOrder 1───N WorkOrder N───1 Operation / Machine
WorkOrder 1───N WorkOrderConfirmation
WorkOrder 1───N StockMovement (issue)   WorkOrder 1───N ProductionBatch 1───N Roll
ProductionBatch 1───N QualityCheck ;  QualityCheck 0───N QualityAlert 1───1 Disposition
ProductionBatch 1───N ScrapRecord / ReworkRecord ; WorkOrder 1───N DowntimeEvent

BatchGenealogy: (parent_object) N───N (child_object)   [rolls/lots/batches]
RawMaterialLot N───1 Supplier ; RawMaterialLot 1───N StockMovement
StockMovement N───1 Item / Location ; StockReservation N───1 SalesOrderLine

PurchaseRequest 1───N PurchaseOrder 1───N PurchaseOrderLine 1───N GoodsReceipt → RawMaterialLot
CostRecord N───1 (WorkOrder | ProductionOrder | StockMovement) ; OrderCostSettlement 1───1 SalesOrderLine
MaintenanceOrder N───1 Machine ; DowntimeEvent N───1 Machine
AuditLogEntry N───1 (any versioned/transactional entity)
```

## B.4 Main workflows
1. **Quote-to-order:** Inquiry → Requirements → Spec(v) → Quotation(v) → Approval → Sales Order.
2. **Engineering release (new product):** Spec → Artwork(v) → Tooling → Sample/first-article → BOM(v) + Routing(v) release.
3. **Plan-to-produce:** Production planning → MRP → reserve/purchase → stage Production Orders → Work Orders → confirmations (output/scrap/downtime) → batches/rolls.
4. **Quality:** inline checks per stage → pass→next / fail→hold→disposition (rework/scrap/concession) → final QC → COA.
5. **Inventory & trace:** receipts → issues (lot/roll) → production receipts → transfers → genealogy → FG.
6. **Deliver:** pick → pack → dispatch → deliver (± tolerance) → returns (RMA).
7. **Cost & profit:** continuous cost capture → order settlement → margin/profitability.
8. **Procure:** PR → PO(approve) → receipt → incoming QC → RM lot to stock.
9. **Maintain:** maintenance order → machine downtime → availability/cost.

## B.5 State machines (summary — full detail in business-processes.md §5)
- **Quotation:** Draft→UnderReview→Sent→(Accepted|Rejected|Expired), Revised loop.
- **Sales Order:** Draft→Confirmed→InPlanning→InProduction→(Partially)Fulfilled→Closed; Cancelled/OnHold.
- **Spec/Artwork/BOM/Routing revision:** Draft→InReview→Approved→Active→Superseded/Obsolete.
- **Production Order:** Planned→Released→InProgress→(Paused)→Completed→Closed; Cancelled; QC_Hold.
- **Purchase Order:** Draft→Approved→Sent→PartiallyReceived→Received→Closed; Cancelled.
- **NCR/Quality Alert:** Open→UnderReview→Disposition→Closed.
- **Delivery:** Planned→Picked→Packed→Dispatched→Delivered; Returned.

## B.6 Unknowns requiring human answers
See **Part A** — 22 assumptions (A-001…A-022) and 64 open questions (Q-001…Q-064). The highest-priority blockers for implementation are: **Q-011/Q-015** (machine capability data), **Q-026/Q-027/Q-029** (real BOM levels, consumption bases, routings), **Q-033/Q-034** (cost rates & valuation), **Q-046/Q-049** (roll serialization & trace granularity), **Q-060/Q-062** (deployment target & shop-floor data capture).

## B.7 Proposed architecture [PROPOSAL]

**Style:** **Modular monolith** — a single deployable, internally modularized by domain. No microservices unless a concrete need appears (e.g. one module needing independent scaling); none is demonstrated yet.

**Recommended stack** (of the two suggested backends, the analyst recommends one but flags it as a team choice):

| Layer | Recommendation | Rationale / alternative |
|-------|----------------|-------------------------|
| Backend | **Django + Django REST Framework (Python)** | Batteries-included admin, mature migrations, strong history/audit ecosystem (django-simple-history, django-guardian); excellent for record-heavy ERP. **Alternative: NestJS/TypeScript** if the team wants one language across the stack. **[Q-decision]** team preference. |
| DB | **PostgreSQL** | Transactional integrity (constraint #8), JSONB for flexible spec parameters, strong constraints. |
| Cache / broker | **Redis** | Caching, locks, task broker. |
| Background workers | **Celery** (Django) / **BullMQ** (NestJS) | MRP runs, cost roll-ups, COA/report generation, notifications. |
| Frontend | **React + TypeScript** | RTL/LTR, i18n (react-i18next), Jalali calendar (dayjs-jalali). |
| Object storage | **S3-compatible — MinIO on-prem** | Artwork, prepress, COAs, attachments; self-hostable if cloud is restricted (Q-060/64). |
| Deploy | **Docker / docker-compose** (→ k8s later) | Reproducible, on-prem friendly. |
| Reporting | Postgres + materialized views initially | Dedicated BI later. |

**Cross-cutting platform services (built once, used by all modules):** i18n/localization (fa/en, RTL/LTR); **dual-calendar** service (store UTC + Gregorian, render Jalali/Gregorian per user); audit/history (immutable log + versioned entities); RBAC/approval-rule engine (data-driven authorities); numbering/sequence service (document masks); attachment/document service; in-process **domain event bus** so modules stay decoupled (e.g. "BatchCompleted" → costing & inventory react).

**Module boundaries (each a Django app / Nest module):** `commercial`, `engineering` (spec/artwork/tooling), `bom_routing`, `manufacturing`, `inventory`, `quality`, `procurement`, `costing`, `maintenance`, `platform` (auth/audit/i18n).

## B.8 Proposed database structure [PROPOSAL — indicative, not final DDL]

Principles: surrogate PKs; **effective-dated versioned tables**; **append-only** transactional tables; JSONB for flexible/typed spec parameters; every table carries `created_at/by`, `updated_at/by` (UTC); soft-supersede, not hard-delete, for versioned data.

Indicative core tables (grouped by module):

```
commercial:  customer, contact_person, customer_product,
             inquiry, quotation, quotation_revision, quotation_line,
             sales_order, sales_order_line
engineering: product_specification, product_specification_revision,
             spec_layer, spec_parameter,        -- value/unit/tol_low/tol_high (JSONB-friendly)
             artwork, artwork_revision, color_recipe,
             printing_tooling, tooling_set
bom_routing: bom, bom_revision, bom_line,
             routing, routing_revision, operation,
             work_center, machine, machine_capability_profile, changeover_matrix
manufacturing: production_order, work_order, work_order_confirmation,
             production_batch, roll, scrap_record, rework_record, downtime_event
inventory:   item, warehouse, location, raw_material_lot,
             stock_movement (append-only), stock_reservation,
             batch_genealogy (parent_id, child_id, relation, qty), uom, uom_conversion
quality:     quality_plan, quality_characteristic, quality_check (append-only),
             quality_alert, disposition, coa
procurement: supplier, purchase_request, purchase_order, purchase_order_line, goods_receipt
costing:     cost_rate, cost_record (append-only), order_cost_settlement, profitability_record
maintenance: maintenance_order
platform:    app_user, role, permission, role_permission, user_role,
             approval_rule, audit_log_entry (append-only), doc_sequence
```

Key structural decisions:
- **Versioning:** `*_revision` tables hold immutable snapshots; the parent points to `active_revision_id`.
- **Traceability:** `batch_genealogy` is a graph edge table enabling forward+reverse walks; `stock_movement` + `roll`/`raw_material_lot` carry lot/roll references on every consume/produce.
- **Flexibility without code change:** `spec_parameter` and `machine_capability_profile` use typed key/value (+JSONB), so new attributes/machines need data, not schema/code churn (constraint #9).
- **Transactionality:** a work-order confirmation writes confirmation + stock issues + batch/roll + genealogy + cost_records in **one DB transaction** (constraint #8).
- **Dates:** timestamps stored UTC; a display layer renders Jalali/Gregorian — no business logic branches on locale.

## B.9 Risks

| # | Risk | Impact | Mitigation |
|---|------|--------|-----------|
| R-1 | **Domain misunderstanding** — many assumptions unvalidated. | Wrong model, rework. | This discovery doc + business sign-off on Part A before coding. |
| R-2 | **Traceability complexity** (roll splits/merges, genealogy). | Core requirement fails / slow. | Model genealogy explicitly early; prototype trace queries; decide serialization (Q-046). |
| R-3 | **Over-engineering / scope creep** — building all modules. | Delay, budget. | Phased delivery; start with the vertical slice in B.10. |
| R-4 | **Costing without validated rates/methods.** | Misleading margins. | Keep formulas configurable; validate Q-031/33/34 before costing go-live. |
| R-5 | **Bilingual + Jalali retrofitting** if deferred. | Expensive rework. | Build i18n + dual-calendar into the platform layer from day one. |
| R-6 | **Shop-floor data-capture friction** (manual vs machine). | Poor data quality, no trace. | Clarify Q-062; design operator UX for fast, mandatory lot/scrap capture. |
| R-7 | **On-prem / sanction constraints** on cloud & libraries. | Blocked deployment. | Confirm Q-060/64 early; prefer self-hostable OSS (Postgres, MinIO, Redis). |
| R-8 | **Master-data readiness** (machines, materials, tolerances). | Cannot configure system. | Parallel data-collection workstream driven by open questions. |
| R-9 | **Audit/immutability gaps** if added late. | Compliance failure. | Append-only + versioning as platform primitives from the start. |
| R-10 | **Performance** of genealogy/trace at volume. | Slow recalls/reports. | Proper indexing, edge/closure table, materialized views; validate with Q-059. |

## B.10 Recommended next implementation task [PROPOSAL]

**Do not** start building all modules. Recommended sequence:

**Task 002 — Validation & platform foundation (no business modules yet):**
1. **Business review workshop** to answer Part A (prioritize the B.6 blockers). Convert answers into a "Confirmed Requirements" document.
2. **Platform foundation** (thin, reusable, safe regardless of domain answers): project scaffold (Django or NestJS per team decision), PostgreSQL, Redis, Docker; **i18n (fa/en, RTL) + dual-calendar** service; **audit/versioning** primitives; **RBAC/approval-rule** engine; object storage; auth.

**Task 003 — First vertical slice (thinnest end-to-end thread), after Part A is answered:**
`Customer → CustomerProduct → ProductSpecificationRevision (versioned) → SalesOrder → single-stage ProductionOrder/WorkOrder → ProductionBatch/Roll → StockMovement + genealogy → QualityCheck → Delivery`, plus **continuous cost capture** on that slice. This proves the hardest cross-cutting requirements (versioning, traceability, transactional posting, bilingual/Jalali, audit) on a minimal path before scaling to all stages and modules.

**Explicitly deferred:** full APS scheduling, financial accounting/GL, advanced OEE, automated BOM/routing generation, and machine (PLC/SCADA) integration — revisit once the core manufacturing domain is proven.

---

*End of Task 001 discovery deliverable. Awaiting business-team review of Part A before implementation begins.*


