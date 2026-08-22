# Reconciliation — NEPTA/SLZ System Documentation vs. Task 001 Business Analysis

**Reconciliation date:** 2026-08-21
**Source document:** `docs/reference/NEPTA_ERP_Feasibility_Study.md` (code **NEPTA.ERP.SLC.FZS**, V1.5, 1402/09/26 ≈ 2023-12, authors: مهدی شوریده یزدی, رویا خسروی)
**Compared against:** `docs/business-analysis/` (Task 001, 10 documents)

> **Nature of the source document.** It is a **feasibility / ERP-selection study** written in the APQC process framework, not an as-is spec of a legacy software system. It therefore carries three kinds of content: (a) **organizational facts** about the NEPTA group and SLZ, (b) **domain requirements** area-by-area, and (c) a **build-vs-buy selection** recommending a COTS product. Per the Task 004A information hierarchy, this official SLZ document outranks our earlier technical proposals and generic ERP conventions. Contradictions below are surfaced, **not** silently resolved.

## Classification legend

`CONFIRMED` — doc confirms a Task 001 claim/assumption · `ASSUMPTION CONFIRMED` / `ASSUMPTION INVALIDATED` — status of a Task 001 A-### · `NEW INFORMATION` — in doc, absent from Task 001 · `CONTRADICTION` — doc conflicts with Task 001 · `OPEN QUESTION` — doc raises/leaves a question · `TECHNICAL PROPOSAL` — a Task 001 design choice the doc does not establish.

## A. Organizational & strategic reconciliation (highest impact)

| ID | Existing SLZ Documentation (NEPTA doc) | Task 001 | Result | Action |
|----|----------------------------------------|----------|--------|--------|
| R-01 | SLZ (لفاف زرین, est. 1382/2003) is the **founding member of the NEPTA holding group of six companies** (§شناخت سازمان). | Task 001 models SLZ as a **single standalone company**; NEPTA/holding never mentioned. | **NEW INFORMATION / ASSUMPTION INVALIDATED** (implicit single-company assumption) | Master data must be genuinely **multi-company**. See `master-data-impact.md` R-MD-01. |
| R-02 | **Phase-1 ERP scope = two companies: لفاف زرین (Tehran) + هلنا/Helena (Saveh)** (§تعریف پروژه). Full scope = all 6 group companies later. | No Helena, no Saveh, no multi-site-as-fact. | **NEW INFORMATION** | Company + Site (Tehran/Saveh) are real, phase-1 entities — validates the Task 003 `organization` app; confirm exact company/site list (NQ-002). |
| R-03 | Production is **split across companies with different capabilities**: SLZ-Tehran = blown film, cast film, printing, lamination, **recycling/grinding (بازیافت/آسیاب)**, cutting/sewing; Helena-Saveh = blown film + cutting/sewing only (§تولید و کنترل تولید). | Task 001 describes **one plant** with an 8-stage chain; no site-specific capability; no recycling stage. | **NEW INFORMATION / CONTRADICTION (single-site model)** | Capability & capacity must be **site-scoped**; add recycling/grinding stage. See `slz-specific-rules.md`. |
| R-04 | The study **evaluates COTS ERPs and recommends buying Microsoft Dynamics 365 F&O** (SAP S/4HANA runner-up) (§مقایسه راهکارهای برتر). | Task 001 (open-questions Part B) proposes a **custom modular monolith** (Django/DRF or NestJS). | **CONTRADICTION (critical, build-vs-buy)** | **Do not resolve silently.** Escalate as top decision NQ-001; the whole custom-build program depends on the business reaffirming custom over the documented buy recommendation. |

## B. Sales & commercial

| ID | Existing SLZ Documentation | Task 001 | Result | Action |
|----|----------------------------|----------|--------|--------|
| R-10 | Production is **by customer order**; sales differs greatly from standard products (§فروش). | MTO / ETO-for-new posture (README, business-processes). | **CONFIRMED** | Keep MTO core. |
| R-11 | Order starts as **Sales Inquiry**; for new products parameters may be imprecise/undefined initially. | A-001 (new vs repeat paths), FR-020/FR-024. | **ASSUMPTION CONFIRMED (A-001)** | Flip A-001 → confirmed; keep new-vs-repeat branch. |
| R-12 | **Reuse of previous order history for the same product/customer (SKU)** for repeats. | Repeat-order path, Q-002. | **CONFIRMED** | Informs Q-002 (repeat ratio still unquantified). |
| R-13 | **System calculates dependent parameters from customer's main parameters and generates the SKU** (e.g. roll diameter & count, pallet count). | Layered, calculated product identity (product-model, FR-001). | **CONFIRMED + EXPANDED** | Product master needs a parameter-derivation/SKU service. See `slz-specific-rules.md` SR-01. |
| R-14 | **Proforma (پیش‌فاکتور) from a pricing algorithm + approval workflow**; price from product characteristics, packaging, volume, RM price, margin. | Versioned quotation state machine (FR-021), pricing. | **CONFIRMED** | Keep quotation/proforma versioning + approval. |
| R-15 | **Delivery-time estimation** from capacity, current orders, RM stock, supply lead time. | Implied by planning; not a distinct Task 001 feature. | **NEW INFORMATION** | Add ATP/lead-time estimate as a planning-linked sales feature (later). |
| R-16 | **Customer approves drawings: product drawing / technical drawing / Proof**; feasibility to **R&D** and **Edit unit** (ادیت) for printed products. | A-002 (sample/first-article), artwork approval (FR-009/012). | **ASSUMPTION CONFIRMED (partial, A-002)** | Confirms document-approval loop; **physical** sample sign-off still open (Q-003). Adds R&D + Edit units. |
| R-17 | **Marking (مارکینگ) specified by customer per packaging level**; pallet packaging spec per order. | Not modeled. | **NEW INFORMATION** | Add per-packaging-level marking to product/order spec (NQ-008). |
| R-18 | Full **CRM domain**: leads, contacts, call-center/VOIP, opportunities/pipeline, forecasting (top-down + bottom-up), campaigns, feedback, complaints; **sales lines by product group**. | Task 001 focuses on manufacturing; **no CRM requirements**. | **NEW INFORMATION (whole domain)** | CRM is a real future domain, not out-of-scope; phase TBD (NQ-009). |

## C. Product engineering & master data

| ID | Existing SLZ Documentation | Task 001 | Result | Action |
|----|----------------------------|----------|--------|--------|
| R-20 | "Product classification and precise definition is one of NEPTA's **biggest challenges**"; classify by **type / class / family (نوع/طبقه/خانواده)**. | Layered product identity; category/group defaults (product-model). | **CONFIRMED + EXPANDED** | Product master needs a **type→class→family** taxonomy plus product groups. |
| R-21 | Product master carries: dimensional parameters, product drawing, **BOM types**, **OPC**, technical production drawing, **material formulation (main + alternative)**, **ink/color formulation** (if printed), **MSDS/storage info**, **design & cliché profile**, **targets**, **QC checklist**. | Spec-revision attribute groups (product-model), BOM/routing, quality plan. | **CONFIRMED + EXPANDED** | Confirms rich versioned spec; adds MSDS, ink formulation, targets as explicit fields. |
| R-22 | **Cliché management (مدیریت کلیشه)**: ID cards for **کلیشه/برگ/دست** (cliché/sheet/set), **usage recording**, dedicated **cliché warehouse**. | A-003 (printing tooling is a distinct object), FR-010. | **ASSUMPTION CONFIRMED (A-003)** | Elevate **Tooling/Cliché** to a first-class master/asset entity with usage-life + its own store. See `master-data-impact.md` R-MD-05. |
| R-23 | Engineering change mgmt, **version control, ECN (اعلامیه تغییر مهندسی)**; multiple production BOMs per product; **print mounting calc (مونتاژ چاپ)**. | Versioned immutable spec/BOM (FR-031/035), Q-024. | **CONFIRMED + EXPANDED** | Confirms versioning/ECN; print-mounting is a new SLZ-specific calc (NQ-007). |

## D. Planning, manufacturing & quality

| ID | Existing SLZ Documentation | Task 001 | Result | Action |
|----|----------------------------|----------|--------|--------|
| R-30 | **Production feasibility (امکان‌سنجی تولید)** by Planning from sales forecasts + capacity; **capacity table by product-machine**, annual, updated by Production, supervised by **Production Control**. | Capacity/work-center concepts (manufacturing), A-011. | **CONFIRMED + EXPANDED** | Adds explicit feasibility step + capacity governance. |
| R-31 | **MRP** covers raw materials, production consumables, **ink (مرکب)** and **solvent (حلال)**. | MRP / material planning; material categories generic. | **CONFIRMED + EXPANDED** | Material master must subtype ink & solvent distinctly. |
| R-32 | **Production outsourcing (برون‌سپاری)**: some stages outsourced to inside/outside the group. | Not modeled. | **NEW INFORMATION** | Routing operations may be external / at a sister company (NQ-004). |
| R-33 | **Order priority by margin (اولویت‌بندی بر مبنای مارجین)**. | Not stated. | **NEW INFORMATION** | Planning prioritization rule (later). |
| R-34 | **Machine settings recorded per production order**; identify **optimal settings** from production/waste. | Data-driven machine model, constraint #8. | **CONFIRMED + EXPANDED** | Add a machine-settings library keyed by machine×product. |
| R-35 | **Allowed-scrap table** and **allowed-downtime-limit table**, both **by machine-product**; record scrap/downtime with reasons; **shift-event log**. | A-011/A-013 (yield/scrap %), scrap & downtime reason codes (FR-043/045). | **ASSUMPTION CONFIRMED (A-011, A-013) + EXPANDED** | Thresholds are per machine×product, data-driven. |
| R-36 | **Rework (دوباره‌کاری)**: non-conforming → some scrap, some reworked → sellable; sales-return QC. | A-006, FR-044, Q-043. | **ASSUMPTION CONFIRMED (A-006)** | Keep rework-vs-scrap path. |
| R-37 | Inline & post QC, **per-operation QC sheets based on production rolls**; **auto action on out-of-range: message + stop production WO + issue rework WO**; defect tree, COA, quarantine. | A-005/A-018 (inline QC), FR-072/073/074. | **ASSUMPTION CONFIRMED (A-005, A-018) + EXPANDED** | Adds automated QC-triggered actions. |
| R-38 | Incoming QC with **temporary vs definitive receipt** gated on a QC pass threshold. | FR-082 (GRN + incoming QC). | **CONFIRMED** | Keep temp→definitive receipt on QC. |

## E. Inventory, procurement, finance, maintenance, HR

| ID | Existing SLZ Documentation | Task 001 | Result | Action |
|----|----------------------------|----------|--------|--------|
| R-40 | **Unlimited warehouses**, per-user warehouse access; special stores: **scrap, quarantine, cliché, line-side (پای کار), consignment (امانی), stagnant (راکد)**; **multiple UoM per item, substitute items, min/max/reorder**; quantity + rial **kardex**; stocktaking; year-end; Excel import; **consumption permit** (gift/sample/consumables). | Warehouse→Zone→Location, movement types, A-021 (UoM), Q-047. | **CONFIRMED + EXPANDED; partially answers Q-047** | Multiple warehouses confirmed; adds special-store types + consumption permit + kardex. |
| R-41 | Multiple UoM per item with substitutes. | A-021, FR-057. | **ASSUMPTION CONFIRMED (A-021)** | UoM + conversion is core early master data. |
| R-42 | **Shelf-life / expiry** in material planning. | A-020, FR-059. | **ASSUMPTION CONFIRMED (A-020)** | Keep expiry/FEFO capability (enforcement still open, Q-051). |
| R-43 | **Reservations, safety stock, economic order qty, lead times, purchase requests** via MRP. | A-019, FR-056. | **ASSUMPTION CONFIRMED (A-019)** | Keep reservation + PR-on-shortfall. |
| R-44 | Procurement: PR → inquiry → PO (internal/external/procurement), payment order, **import process (proforma, insurance, arrival notice)**, supplier eval, **sanctioned-party control, FX/تسعیر, documentary trade**. | PR→PO→GRN (FR-081), supplier mgmt (FR-080), NFR-022 (sanctions). | **CONFIRMED + EXPANDED; confirms Q-064** | Adds foreign-trade/import + sanction screening as real requirements. |
| R-45 | Finance: chart of accounts/persons/**floating (شناور)**/centers/projects, sales & purchase accounting, treasury, **product cost (بهای تمام‌شده)**, **customer settlement date (راس تسویه)**, budgets per section, **asset system**, payroll. | Costing model proposed; **accounting explicitly deferred** (constraint #10). | **CONTRADICTION (scope/phasing) — reinforces C-006** | Finance is clearly expected; keep deferred for now but record the tension (NQ-010). |
| R-46 | Maintenance (فنی): **equipment ID card + spare-parts structure**, PM types, preventive activities, periodic PM planning, service checklists, machine stop reasons, runtime, **MRO work orders**, inspection results. | FR-100 (maintenance orders), Q-017. | **CONFIRMED + EXPANDED** | Confirms a real maintenance domain (later phase). |
| R-47 | HR: **org decrees (احکام)**, salary calculator, recruit/hire/terminate/transfer, evaluation, contracts, **attendance**. | Not in Task 001 scope. | **NEW INFORMATION (domain)** | HR is a real future domain; Employee master needed for production skills sooner (later phase). |

## F. Assumption status roll-up (Task 001 `open-questions.md`)

| Assumption | New status from this document |
|------------|-------------------------------|
| A-001 new-vs-repeat paths | **CONFIRMED** (R-11, R-12) |
| A-002 sample/first-article loop | **PARTIALLY CONFIRMED** — document approval confirmed; physical-sample rule still open (R-16, Q-003) |
| A-003 printing tooling distinct object | **CONFIRMED** (R-22) |
| A-005 inline QC every stage | **CONFIRMED** (R-37) |
| A-006 reverse flows (RMA/rework) | **CONFIRMED** (R-36) |
| A-011 yield/scrap % per stage | **CONFIRMED + EXPANDED** (R-35) |
| A-013 setup vs running waste | **CONFIRMED (per machine×product)** (R-35) |
| A-014 alternate materials | **CONFIRMED** (R-21, ink/material formulation) |
| A-018 defined inspection points | **CONFIRMED** (R-37) |
| A-019 reservations → purchase requests | **CONFIRMED** (R-43) |
| A-020 shelf-life/expiry | **CONFIRMED** (R-42) |
| A-021 multiple UoM conversions | **CONFIRMED** (R-41) |
| A-022 role catalogue | **PARTIALLY INFORMED** — doc lists real units/departments (R&D, Edit, Planning, Production Control, QC, Warehouse, Procurement, Finance, HR, Technical, sales lines); full RBAC still open (Q-053) |
| *(implicit)* single-company assumption | **INVALIDATED** — SLZ is one of six NEPTA companies (R-01, R-02) |
| A-004, A-007–A-010, A-012, A-015–A-017 | **UNCHANGED** — not addressed at the needed granularity by the document |

## G. Summary

The document **strongly validates** the manufacturing-centric domain Task 001 built (product versioning, cliché/tooling, inline QC, lot/roll traceability, multi-UoM, MRP, scrap/rework, maintenance) and **confirms 12 of 22 assumptions**. It **expands** scope into CRM, Finance, HR, and foreign-trade procurement, and adds SLZ-specific mechanics (SKU parameter derivation, print mounting, marking, machine-settings library, allowed-scrap/downtime tables, recycling, outsourcing). It introduces **two structural corrections** — SLZ is **multi-company** (NEPTA group; phase-1 SLZ + Helena) and production capability is **site-specific** — and **one critical contradiction**: the official study **recommends buying Microsoft Dynamics 365 F&O**, whereas the current program builds a custom system. That build-vs-buy question (NQ-001) must be resolved by the business before further implementation.
