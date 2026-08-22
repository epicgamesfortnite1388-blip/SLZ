# SLZ ERP — Requirements Baseline / خط‌مبنای الزامات

**Task 002 deliverable.** Derived strictly from Task 001 (`docs/business-analysis/`). No requirement is invented beyond that analysis. Requirements whose detail depends on an unvalidated assumption or open question are marked **[BUSINESS VALIDATION REQUIRED]** and carry their source ID (A-xxx / Q-xxx).

**Status of this baseline:** DRAFT — pending business workshop (see `../business-review/business-review-fa-en.md`).

Legend: **shall** = mandatory intent from Task 001 · **[BVR]** = `[BUSINESS VALIDATION REQUIRED]` · source in *(parentheses)*.

---

## Functional Requirements / الزامات کارکردی

### FR — Product Engineering (Specification, Artwork, Tooling)

- **FR-001** The system shall represent a product as a layered identity: **Customer → Customer Product → Product Specification → Specification Revision**, not a flat SKU. *(product-model §2)*
- **FR-002** The system shall support **versioned** customer-specific product specifications; every technical specification is versioned. *(README constraint; product-model §4)*
- **FR-003** The system shall preserve all historical specification revisions immutably; superseding shall never delete. *(constraint #4; product-model §4)*
- **FR-004** The system shall allow ordering only against an **ACTIVE** specification revision, while retaining SUPERSEDED/OBSOLETE revisions for traceability and re-order. *(product-model §4)*
- **FR-005** The system shall model material structure as an **ordered list of layers**, each with material, thickness (micron) and tolerance. *(product-model §3.1)*
- **FR-006** The system shall store technical attributes (dimensions, width, length, thickness, bag type, seal type, printing, colors, ink, lamination, adhesive, cold seal, matte/gloss, special effects, packaging) as typed, toleranced spec parameters. *(product-model §3)*
- **FR-007** The system shall support **customer-specific specifications** as typed custom attributes without requiring code changes. *(product-model §3.7)*
- **FR-008** The system shall attach **tolerances** to individual attributes (thickness ±, width ±, color ΔE, seal/bond strength min, registration ±, delivered-quantity ±%). Default values **[BVR]** *(Q-022)*.
- **FR-009** The system shall manage **Artwork** with its own revisions and approval lifecycle (internal → customer → approved). *(business-processes §5.4; product-model §5)*
- **FR-010** The system shall manage **Printing Tooling** (plates/cylinders/sleeves) as objects linked to an artwork revision, with their own lifecycle. **[BVR]** in-house vs outsourced, ownership *(Q-004/036)*.
- **FR-011** The system shall define, per product, the rule that triggers a **new spec revision vs. a minor correction**, and the approver. **[BVR]** *(Q-024)*.
- **FR-012** The system shall allow artwork to revise independently of the product specification, linked by reference. **[BVR]** *(Q-025)*.
- **FR-013** The system shall classify customer products by **product group** (cellulose/hygiene, food, non-food, general, shopping bags). *(product-model §6)*

### FR — Sales & Commercial

- **FR-020** The system shall capture **customer inquiries** and technical requirements. *(business-processes §4)*
- **FR-021** The system shall produce **versioned quotations** with a state machine (Draft→UnderReview→Sent→Accepted/Rejected/Expired; Revised). *(business-processes §5.1)*
- **FR-022** The system shall create a **Sales Order** upon quotation acceptance, retaining superseded quotation versions. *(business-processes §5.1)*
- **FR-023** The system shall support a **Sales Order lifecycle** (Draft→Confirmed→InPlanning→InProduction→(Partially)Fulfilled→Closed; Cancelled/OnHold). Hold/release conditions **[BVR]** *(Q-009)*.
- **FR-024** The system shall support distinct **new-product vs. repeat-order** paths. **[BVR]** ratio & automation depth *(A-001, Q-002)*.
- **FR-025** The system shall support customer **change orders, cancellations, and returns (RMA)**. **[BVR]** rules *(A-006)*.
- **FR-026** The system shall support an **over/under-delivery tolerance** on order fulfilment and its billing basis. **[BVR]** ± % *(Q-006/037)*.
- **FR-027** The system shall support a **sample / first-article approval** step before bulk production. **[BVR]** when mandatory *(A-002, Q-003)*.

### FR — BOM & Routing

- **FR-030** The system shall support **multi-level BOMs** mirroring the production stages (resin→base film→printed→laminate→slit→finished). Which levels are real **[BVR]** *(Q-026)*.
- **FR-031** The system shall version BOMs (BOM Revision) immutably and preserve history. *(bom-and-routing §2, §4)*
- **FR-032** The system shall express BOM-line consumption on a configurable **basis** (per unit / area / weight / length / fixed-per-run). Bases & waste factors **[BVR]** *(A-012, Q-027)*.
- **FR-033** The system shall separate **setup waste (fixed)** from **running waste (%)** in requirement calculations. **[BVR]** factors *(A-013, Q-016/042)*.
- **FR-034** The system shall support **alternate/substitute materials** on a BOM line with priority. **[BVR]** whether allowed & QC approval *(A-014, Q-028)*.
- **FR-035** The system shall version **Routings** (Routing Revision) bound to a spec revision, composed of ordered **Operations** on **Work Centers**. *(bom-and-routing §3)*
- **FR-036** Each operation shall define setup time, run-rate basis, required tooling, required skills, inline QC, standard scrap, input BOM lines consumed and expected output item. *(bom-and-routing §3.2, §3.3)*
- **FR-037** The system shall support **standard routings per product group** with permissible stage skips. **[BVR]** templates *(Q-029)*.
- **FR-038** A **Production Order** shall snapshot the BOM revision and Routing revision it was released with, so later changes never alter historical orders. *(bom-and-routing §4)*
- **FR-039** BOM/Routing release shall require an approval authority. **[BVR]** who *(Q-030)*.

### FR — Manufacturing Execution

- **FR-040** The system shall model **Work Centers** grouping interchangeable **Machines**, each machine carrying a data-driven **capability profile** (no hard-coded machine logic). *(manufacturing §3, §3.1; constraint #9)*
- **FR-041** The system shall generate **Production Orders per stage** and **Work Orders per operation**, choosing among **alternative qualified machines**. *(manufacturing §3.2)*
- **FR-042** The system shall capture, per work order: setup, run confirmations (good qty, scrap qty, time), **material issues with lot/roll**, inline QC, and output. *(manufacturing §3.2)*
- **FR-043** The system shall record **scrap** with reason codes per stage. **[BVR]** reason-code list & standard % *(A-011, Q-016/042)*.
- **FR-044** The system shall record **rework** as a traced pass through an operation, preserving genealogy. **[BVR]** reworkable-vs-scrap rules *(Q-043)*.
- **FR-045** The system shall record **downtime** events with reason codes against a machine. *(manufacturing §4)*
- **FR-046** The system shall support a **Production Order state machine** (Planned→Released→InProgress→(Paused)→Completed→Closed; Cancelled; QC_Hold). *(business-processes §5.5)*
- **FR-047** The system shall record output as **Production Batches** and **Rolls/units** posted to inventory with parent→child genealogy. *(manufacturing §3.4)*
- **FR-048** The system shall support machine **changeover** durations via a data-driven from→to matrix (not hard-coded). *(manufacturing §3)*
- **FR-049** Capacity/scheduling in the first release shall be **finite-capacity-aware but manual/assisted** (planner assigns work orders). Full automatic APS is out of scope. **[BVR]** planning method *(manufacturing §5, Q-018)*.

### FR — Inventory & Traceability

- **FR-050** The system shall track raw materials by **item and supplier lot** (Raw Material Lot). *(inventory §1)*
- **FR-051** The system shall track **Rolls** as physical objects with weight/length/width/core. Whether each roll is **serialized** vs. lot+count **[BVR]** *(Q-046)*.
- **FR-052** The system shall model **Warehouse → (Zone) → Location** with location types (RM, WIP, FG, QC-hold, quarantine, scrap, staging, returns). Bin-level need **[BVR]** *(Q-047)*.
- **FR-053** The system shall record every inventory change as an **immutable, append-only Stock Movement** (receipt, issue, production receipt, transfer, reservation, scrap, adjustment, shipment, return). *(inventory §3)*
- **FR-054** The system shall guarantee that a work-order confirmation's consumption + output + genealogy + cost capture commit as **one atomic transaction**. *(constraint #8; inventory §3)*
- **FR-055** The system shall provide **forward and reverse traceability** Supplier→RM lot→batch→semi-finished→finished→delivery, and back, via a genealogy edge model. *(inventory §4; constraint)*
- **FR-056** The system shall support **stock reservations** (soft allocation) and raise purchase requests for shortfalls. **[BVR]** allocation policy *(A-019, Q-005/050)*.
- **FR-057** The system shall support **multiple units of measure with conversions** (kg↔m↔m² via grammage/width). **[BVR]** UoMs & factors *(A-021, Q-052)*.
- **FR-058** The system shall support material issue via **explicit lot/roll selection and/or backflush**. **[BVR]** which method *(Q-048)*.
- **FR-059** The system shall support **shelf-life/expiry** attributes on lots (and FEFO handling if required). **[BVR]** *(A-020, Q-051)*.
- **FR-060** The system shall support a chosen **traceability granularity** (roll / pallet / carton) consistently across labeling and recall. **[BVR]** *(Q-049)*.

### FR — Quality

- **FR-070** The system shall support **Quality Plans** (versioned) defining characteristics, methods and spec limits per operation/material. *(quality §1)*
- **FR-071** The system shall record **Quality Checks** against incoming lot / work order / batch / roll, with measured values and PASS/FAIL/CONDITIONAL result; results are immutable. *(quality §3)*
- **FR-072** The system shall support **inline QC at each stage** plus final QC. **[BVR]** exact points/methods/sampling *(A-005/A-018, Q-039, Q-040)*.
- **FR-073** The system shall raise a **Quality Alert / NCR** on failure, with a disposition lifecycle (Open→UnderReview→Disposition→Closed; disposition ∈ accept/rework/scrap/return/downgrade). **[BVR]** CAPA depth *(quality §4, Q-041)*.
- **FR-074** The system shall place affected batches/rolls on **QC-Hold**, blocking consumption/shipment until disposition. *(quality §4)*
- **FR-075** The system shall link quality results to genealogy to enable **recall / mock-recall**. **[BVR]** whether formal recall required *(quality §6, Q-044)*.
- **FR-076** The system shall issue a bilingual **COA** per delivery/batch where required. **[BVR]** which products & fields *(quality §7, Q-045)*.

### FR — Procurement

- **FR-080** The system shall manage **Suppliers**. *(business-processes §4; entity list)*
- **FR-081** The system shall support **Purchase Requests → Purchase Orders → Goods Receipts (GRN)**, with a PO state machine (Draft→Approved→Sent→PartiallyReceived→Received→Closed; Cancelled). *(business-processes §5.6)*
- **FR-082** Goods receipt shall create/attach a **Raw Material Lot** and trigger incoming QC. *(inventory §3; quality §2)*
- **FR-083** The system shall distinguish **stocked (replenished)** vs **bought-to-order** materials. **[BVR]** which materials *(A-004, Q-005/050)*.
- **FR-084** PO approval shall respect approval thresholds. **[BVR]** thresholds *(Q-054)*.

### FR — Costing

- **FR-090** The system shall capture **actual costs** continuously during production at defined capture points (material/ink/adhesive issue, time confirmation, scrap, order close). *(costing §1, §7)*
- **FR-091** The system shall support the cost-element taxonomy: material, ink, adhesive, labor, machine time, setup, energy, maintenance allocation, packaging, scrap, overhead. Completeness **[BVR]** *(costing §2, Q-032)*.
- **FR-092** The system shall keep cost **formulas and rates configurable** (labor/machine/energy/maintenance/overhead) — not hard-coded. Values **[BVR]** *(costing §3, Q-033)*.
- **FR-093** The system shall support a chosen **material valuation method** (FIFO / weighted-average / lot-actual). **[BVR]** *(Q-034)*.
- **FR-094** The system shall attribute **scrap cost** as accumulated cost to the stage scrapped, less recovery value. **[BVR]** regrind/resale treatment *(A-015, Q-035)*.
- **FR-095** The system shall support **tooling cost** as customer-paid or amortized. **[BVR]** *(A-016, Q-004/036)*.
- **FR-096** The system shall compute **order cost settlement** and **profitability** (revenue − actual cost) by chosen dimensions. **[BVR]** priority dimensions *(costing §8, Q-038)*.
- **FR-097** The system shall optionally record an **estimated/standard cost at quotation** and report estimate-vs-actual variance. **[BVR]** whether adopted *(costing §1, Q-031)*.

### FR — Maintenance

- **FR-100** The system shall support **Maintenance Orders** (preventive & breakdown) linked to machines, feeding downtime and availability. **[BVR]** whether PM scheduling in scope now *(manufacturing §4, Q-017)*.

### FR — Cross-cutting / Platform (functional aspects)

- **FR-110** The system shall record an **immutable audit entry** (who/what/before→after/when/reason) for every create/update/state-transition. *(roles §4; constraint #5)*
- **FR-111** The system shall enforce **role-based access control** with permissions as (action, resource) pairs. Role list **[BVR]** *(roles §1–2, Q-053)*.
- **FR-112** The system shall model **approval authorities as data** (thresholds, multi-step, maker≠checker). **[BVR]** matrix *(roles §2–3, Q-054, Q-056)*.
- **FR-113** The system shall present all UI and key documents **bilingually (fa/en)** and render dates in **Jalali and Gregorian**. *(constraints #6, #7)*
- **FR-114** The system shall store artwork/prepress/COA/attachments in **object storage**. *(architecture; product-model)*

---

## Non-Functional Requirements / الزامات غیرکارکردی

Legend: **[TTD]** = `[TARGET TO BE DEFINED]` (no numeric target established in Task 001).

### Security & Access Control
- **NFR-001** The system shall authenticate all users; credential policy per SLZ. Auth method (local vs SSO/AD, shop-floor kiosk/badge) **[BVR]** *(roles §5, Q-058)*.
- **NFR-002** The system shall enforce RBAC on every action/resource and support segregation of duties. Data-scoping need **[BVR]** *(roles §2–3, Q-055)*.
- **NFR-003** The system shall protect secrets and sensitive data at rest and in transit. **[TTD]** specific standards.
- **NFR-004** The system shall support approval workflows as a security control for critical documents. *(roles §2)*

### Auditability & Data Integrity
- **NFR-005** All versioned entities (spec, artwork, BOM, routing, quotation, price) shall be immutable once active and never hard-deleted. *(constraint #4)*
- **NFR-006** All transactional records (stock movements, QC results, cost captures, confirmations) shall be **append-only**; corrections via reversing entries. *(roles §4)*
- **NFR-007** The audit log shall be read-only, non-editable even by administrators. *(roles §4)*
- **NFR-008** Manufacturing transactions shall be **ACID/atomic** (no partial posting). *(constraint #8)*
- **NFR-009** Record retention period **[TTD]** / regulatory audit requirements **[BVR]** *(Q-057)*.

### Localization
- **NFR-010** The system shall provide **Persian (fa-IR, RTL)** and **English (en-US, LTR)** interfaces. *(constraint #6)*
- **NFR-011** The system shall support **Jalali (Shamsi) and Gregorian** dates; timestamps stored UTC, rendered per user locale; no business logic branching on locale. *(constraint #7)*
- **NFR-012** Primary shop-floor UI language and customer/management reporting language **[BVR]** *(Q-063)*.

### Performance & Scalability
- **NFR-013** The system shall serve interactive operations responsively under expected load. Concurrency/volume targets **[TTD]** pending sizing *(Q-059)*.
- **NFR-014** Traceability/genealogy queries shall remain performant at production data volumes via indexing, edge/closure tables and materialized views. Volume targets **[TTD]** *(open-questions R-10, Q-059)*.
- **NFR-015** The architecture shall scale as a modular monolith; microservices only on demonstrated need. *(architecture §B.7)*

### Availability, Backup & Disaster Recovery
- **NFR-016** The system shall define availability targets (uptime, maintenance windows). **[TTD]**.
- **NFR-017** The system shall perform regular backups. Frequency/retention **[TTD]**.
- **NFR-018** The system shall define RPO/RTO for disaster recovery. **[TTD]**.

### Observability
- **NFR-019** The system shall provide application logging, error tracking and basic operational metrics. Toolset **[TTD]** *(architecture)*.

### File Storage & Deployment
- **NFR-020** The system shall store binary artifacts (artwork, prepress, COA) in S3-compatible object storage (self-hostable). *(architecture §B.7)*
- **NFR-021** The system shall be container-deployable (Docker). Deployment model (on-prem vs cloud, data residency) **[BVR]** *(Q-060)*.
- **NFR-022** Technology choices shall respect sanction/licensing constraints; prefer self-hostable OSS. **[BVR]** *(Q-064)*.

### Integration
- **NFR-023** The system shall define integration boundaries with existing systems (accounting, label printers, scales, lab instruments, scanners) and migration needs. **[BVR]** *(Q-061)*.
- **NFR-024** Shop-floor data capture shall support manual entry; machine/PLC integration only if confirmed feasible. **[BVR]** *(Q-062)*.

---

## Traceability of this baseline
Every FR/NFR cites its Task 001 origin. The full origin→requirement→entity→workflow→module chain is in [`traceability.md`](./traceability.md). Unresolved items are tracked in [`decision-register.md`](./decision-register.md) and [`../business-review/business-review-fa-en.md`](../business-review/business-review-fa-en.md).

**Counts:** 78 functional requirements (FR), 24 non-functional requirements (NFR). Items marked **[BVR]** must be validated before the corresponding feature is implemented.

