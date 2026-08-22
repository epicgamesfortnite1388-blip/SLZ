# Current SLZ System → Future ERP Mapping

**Source:** `docs/reference/NEPTA_ERP_Feasibility_Study.md` (NEPTA.ERP.SLC.FZS V1.5)
**Date:** 2026-08-21
**Purpose:** For each real SLZ process the document describes, map: **Current process → Business rule → New ERP domain model → New ERP workflow**. This is the bridge from "how SLZ works today" to "what we build," and the reference future implementation agents should consult before coding domain behavior.

> Rows preserve **business reality** and separate it from any legacy implementation detail. Cross-references: business rules `SR-##` in `slz-specific-rules.md`; entities in `slz-domain-model.md`; workflow steps in `slz-actual-workflow.md`.

## Legend
- **New ERP domain model** = the app/entity that will own this (names align with Task 003 foundation apps and planned domain tasks).
- **Phase**: 4 = Master Data (Task 004), 5 = Product Engineering (Task 005), M = Manufacturing, I = Inventory, Q = Quality, P = Procurement, later = CRM/Finance/HR/Maintenance/Trade.

| # | Current SLZ process | Business rule | New ERP domain model | New ERP workflow | Phase |
|---|---------------------|---------------|----------------------|------------------|-------|
| 1 | SLZ operates within NEPTA 6-company group; phase-1 SLZ + Helena | SR-16 multi-company; company-scoped data | `organization`: Company, Site | Group/company/site setup; scope every record | 4 (GATE NQ-002) |
| 2 | Production capability differs Tehran vs Saveh | SR-15 site-specific capability | Site.capabilities set | Feasibility & routing respect site capability | 4/M (DR-041) |
| 3 | Sales organized by product-group lines | R-18 sales lines | Department/sales-line + product group | RBAC-scoped sales-line access | 4 |
| 4 | Order starts as Sales Inquiry; new vs repeat | A-001 new-vs-repeat; repeats reuse SKU | Sales: Inquiry; Product master | New→engineering path; repeat→reuse SKU history | later (sales)/5 |
| 5 | Dependent params & SKU derived from customer main params | SR-01 derived SKU | Product Engineering: SKU-derivation service | Enter main params → system derives params + SKU | 5 |
| 6 | New/printed products → R&D + Edit unit; customer approves drawing/proof | R-16 drawing/proof approval (physical sample open Q-003) | `documents` + `workflow`: drawing/proof approval | Route drawing → customer approval gate | 5 (later sales) |
| 7 | Product precisely classified & richly specified | SR-02 type→class→family + rich spec | Product master (thin) + Product Engineering spec (versioned) | Classify product; version spec via ECN | 4 (taxonomy) / 5 (spec) |
| 8 | Cliché/sheet/set tooling with usage-life & own store | SR-03 tooling asset | Tooling/Cliché entity + cliché store type | Create cliché profile; record usage; store in cliché WH | 5 / I |
| 9 | Multiple production BOMs; print mounting calc | R-23 multi-BOM + mounting | BOM/Routing (versioned) + mounting calc | Version BOM/routing via ECN; compute mounting | 5/M |
| 10 | Engineering changes controlled | R-21/23 ECN + version control | `workflow` + VersionedRoot/Revision | ECN → new immutable spec/BOM/routing version | 5/M |
| 11 | Proforma from pricing algorithm + approval | R-14 versioned proforma | Sales: Quotation/Proforma (versioned) + pricing | Price algorithm → proforma → approval → order | later (sales) |
| 12 | Delivery date estimated from capacity/orders/stock/lead time | SR-12 ATP | Planning: ATP/delivery-estimate | Compute promised date from planning data | M/later |
| 13 | Production feasibility from forecast + capacity | R-30 feasibility | Planning: capacity table (product×machine×site) + feasibility | Feasibility check before commit | M |
| 14 | MRP spans RM, consumables, ink, solvent | SR-04 material subtypes | Material master subtypes + MRP | MRP → reservations, safety stock, EOQ → PR | 4 (subtypes) / P (MRP) |
| 15 | Work orders; priority by margin; outsourcing | SR-13 margin priority; SR-14 outsourcing | Manufacturing: Production/Work Order; routing locus | Generate WO; prioritize by margin; mark outsourced ops | M |
| 16 | PR→inquiry→PO; import; sanctions; FX | R-44 foreign-trade + SR + NFR-022 | Procurement + Trade: PR/PO/GRN, import, sanction screen | PR→PO→receipt; import docs; screen sanctioned parties | P / later (trade) |
| 17 | Temporary → QC → definitive receipt | SR-09 two-stage receipt | Inventory: temp/definitive GRN + QC gate | Temp receipt → incoming QC → definitive on threshold | I/Q |
| 18 | Machine settings per order (optimal from history) | SR-05 machine-settings library | Manufacturing: machine-settings (machine×product) | Load settings for WO; learn optimal from history | M |
| 19 | Roll/lot identity & genealogy across stages | SR-08 traceability | Inventory: Lot/Roll + genealogy | Create roll identity; link parent→child across ops | I (granularity Q-046) |
| 20 | Inline QC per operation on rolls; auto stop + rework WO | SR-06 QC drives WO state | Quality: per-op QC sheet + auto-action | Out-of-range → stop WO + spawn rework WO | Q/M |
| 21 | Scrap/downtime with reasons vs allowed tables | SR-05 allowed-scrap/downtime | Manufacturing: scrap/downtime records + threshold tables | Record with reason; compare to machine×product limits | M |
| 22 | Rework → sellable; scrap → recycle → regrind | SR-07 closed-loop | Manufacturing/Inventory: rework pass + recycling→regrind lot | Rework to sellable; grind scrap → new regrind lot (Tehran) | M/I |
| 23 | Final QC, defect tree, quarantine, COA | R-37 + FR-076 | Quality: NCR, quarantine store, COA | Final QC → COA on release; quarantine holds | Q |
| 24 | Unlimited WHs; special stores; per-user access; consumption permit; rial kardex | SR-10 | Inventory: Warehouse (store types) + kardex + permit | Manage stores; permit non-order issues; value kardex | 4 (WH master) / I |
| 25 | Marking per packaging level; pallet spec | SR-11 | Product/Order: multi-level packaging + marking | Capture marking per level; pallet spec per order | 5 / later (sales) |
| 26 | Product costing, treasury, settlement date, assets, payroll | R-45 finance domain | Finance domain | Cost roll-up; AR/AP; راس تسویه; assets; payroll | later (NQ-010) |
| 27 | Equipment ID cards, PM, MRO work orders | R-46 maintenance | Maintenance domain | PM planning; MRO WOs; service checklists | later |
| 28 | Org decrees, payroll, attendance, evaluation | R-47 HR | HR domain (+ early Employee master) | Employee lifecycle; attendance; decrees | later (Employee early) |
| 29 | CRM: leads, opportunities, campaigns, complaints | R-18 CRM | CRM domain | Lead→opportunity→forecast; complaint mgmt | later (NQ-009) |

## How to use this map

- **Before implementing any domain behavior**, find the row and read the linked business rule (`SR-##`) — it states where SLZ differs from generic ERP.
- **Phase column** shows dependency order: Master Data (4) → Product Engineering (5) → Manufacturing/Inventory/Quality/Procurement → later domains.
- **Do not collapse** derived-SKU, site-capability, material-subtype, or QC-auto-stop into generic defaults — those are the four most common places a generic ERP implementation would silently diverge from SLZ reality.

All of the above remains **design only**. Implementation is gated on **NQ-001 (build vs buy)** and the master-data decisions in `master-data-impact.md`.
