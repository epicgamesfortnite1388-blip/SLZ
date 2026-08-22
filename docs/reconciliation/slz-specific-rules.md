# SLZ-Specific Business Rules vs. Generic ERP Assumptions

**Source:** `docs/reference/NEPTA_ERP_Feasibility_Study.md` (NEPTA.ERP.SLC.FZS V1.5)
**Date:** 2026-08-21
**Purpose:** Isolate the mechanics that are **specific to SLZ / flexible-packaging manufacturing** and would be **wrong if implemented from generic ERP conventions**. Each rule states the SLZ reality, the generic-ERP default it contradicts, and the implementation implication. These are **business rules**, deliberately separated from legacy implementation detail.

> **Directive:** When a generic ERP convention conflicts with a rule below, the SLZ rule wins (per the information hierarchy in `SLZ-SOURCE-OF-TRUTH.md`).

---

## SR-01 — SKU / dependent parameters are DERIVED, not entered
- **SLZ reality:** The system computes dependent parameters (roll diameter & count, pallet count, …) **from the customer's main parameters**, and **generates the SKU** from them. Repeats reuse prior SKU history.
- **Generic ERP default:** SKU is a manually assigned code; product attributes are free-entered.
- **Implication:** Product master needs a **parameter-derivation/SKU-generation service**, not just a code field. Derivation rules are data-driven (open: exact formulas — NQ-005/SKU).

## SR-02 — Product identity is layered & classified (type → class → family)
- **SLZ reality:** "Precise product definition is one of the biggest challenges." Classify by **نوع/طبقه/خانواده** plus product group; spec carries drawings, formulations, MSDS, targets, marking, pallet spec.
- **Generic ERP default:** Flat item master with a category field.
- **Implication:** Multi-level taxonomy + rich versioned spec; not a single category dropdown.

## SR-03 — Cliché (printing tooling) is a first-class asset with usage-life & its own store
- **SLZ reality:** ID cards for **cliché / sheet (برگ) / set (دست)**, **usage recording**, dedicated **cliché warehouse**; tied to customer artwork.
- **Generic ERP default:** Tooling is a fixed asset or a consumable, no per-use life tracking, no dedicated store type.
- **Implication:** Model Tooling/Cliché as a master/asset entity with usage-life counters and a **cliché store type**.

## SR-04 — Material is subtyped; MRP treats ink & solvent distinctly
- **SLZ reality:** MRP explicitly spans **RM, consumables, ink (مرکب), solvent (حلال)**; formulations have **main + alternative** materials; **regrind** is a produced material.
- **Generic ERP default:** One "raw material" class; MRP treats all inputs uniformly.
- **Implication:** Material subtype is load-bearing for MRP, formulation, and QC (e.g., ink/solvent shelf-life, MSDS).

## SR-05 — Capacity, machine-settings, allowed-scrap, allowed-downtime are DATA-DRIVEN tables keyed by machine × product (× site)
- **SLZ reality:** Capacity table by **product×machine**, annual, governed by Production Control; **machine-settings library** learned from history; **allowed-scrap** and **allowed-downtime** thresholds **per machine×product**.
- **Generic ERP default:** Global routing standards, single capacity per work center, fixed scrap %.
- **Implication:** These are **configurable data**, never hard-coded logic (aligns with the project's no-hard-coded-machine-logic constraint). Thresholds are looked up by (machine, product[, site]).

## SR-06 — Inline QC can automatically STOP a work order and spawn a rework WO
- **SLZ reality:** Per-operation QC sheets **based on production rolls**; **out-of-range → message + stop production WO + issue rework WO**; defect tree; quarantine.
- **Generic ERP default:** QC records a result; stopping/reworking is a manual downstream decision.
- **Implication:** QC result must be able to **drive WO state transitions** and generate a rework WO automatically.

## SR-07 — Rework produces sellable output; scrap can be recycled into regrind
- **SLZ reality:** Non-conforming → **partly scrap, partly reworked → sellable**; scrap → **recycling/grinding → regrind material lots** (Tehran only).
- **Generic ERP default:** Non-conforming is scrapped or reworked to the same spec; scrap leaves the system.
- **Implication:** Rework is a **traced pass** feeding back into sellable stock; recycling **creates new material lots** (closed-loop inventory). Recycling is **site-capability-gated**.

## SR-08 — Roll/lot genealogy for full traceability across stages
- **SLZ reality:** Raw-material ID card + roll/lot identity carried across every operation → **traceability (ردیابی)**.
- **Generic ERP default:** Lot tracking at receipt/issue only, not per-roll through operations.
- **Implication:** Genealogy links parent→child lots/rolls through the routing (granularity open — Q-046).

## SR-09 — Incoming goods: temporary receipt → QC → definitive receipt
- **SLZ reality:** **Temporary vs definitive receipt** gated on a **QC pass threshold**.
- **Generic ERP default:** Single GRN posts stock immediately (optionally to QC-hold).
- **Implication:** Two-stage receipt with a QC gate and threshold parameter.

## SR-10 — Warehouses are unlimited with special store types & per-user access & consumption permits
- **SLZ reality:** Many warehouses; special stores: **scrap, quarantine, cliché, line-side (پای کار), consignment (امانی), stagnant (راکد)**; per-user warehouse access; **consumption permit** for gift/sample/consumables; kardex in **quantity + rial**.
- **Generic ERP default:** Few warehouses, generic bins, movements without an explicit permit document.
- **Implication:** Store-type enum + per-user access control + a consumption-permit transaction; kardex carries value, linking to finance.

## SR-11 — Marking specified per packaging level; pallet spec per order
- **SLZ reality:** Customer specifies **marking (مارکینگ)** at each packaging level; pallet packaging spec per order.
- **Generic ERP default:** Single item-level label/barcode.
- **Implication:** Packaging is multi-level with per-level marking on the product/order spec (NQ-008).

## SR-12 — Delivery date is ESTIMATED from capacity + open orders + stock + lead time
- **SLZ reality:** Delivery-time estimation from capacity, current orders, RM stock, supply lead time (ATP-like).
- **Generic ERP default:** Manually promised date or simple lead-time offset.
- **Implication:** ATP/CTP-style estimate wired to planning data (later phase).

## SR-13 — Order priority by margin
- **SLZ reality:** Production orders **prioritized by margin (مارجین)**.
- **Generic ERP default:** FIFO or due-date priority.
- **Implication:** Planning prioritization uses a margin metric (needs costing — later phase).

## SR-14 — Operations may be outsourced (internal sister company or external vendor)
- **SLZ reality:** **Production outsourcing (برون‌سپاری)** of stages, inside or outside the group.
- **Generic ERP default:** All routing operations are in-house.
- **Implication:** A routing operation carries an execution locus (this site / sister site / external vendor) with costing & **QC on return** (NQ-004). Ties to multi-company.

## SR-15 — Production capability is SITE-SPECIFIC
- **SLZ reality:** Tehran = blown film, cast film, printing, lamination, recycling/grinding, cutting/sewing; Helena/Saveh = blown film + cutting/sewing only.
- **Generic ERP default:** One plant, uniform capability; or site is a stocking location only.
- **Implication:** A site declares its **capabilities**; feasibility & routing must respect them. Capacity tables are **site-scoped** (DR-041).

## SR-16 — Multi-company holding structure (NEPTA)
- **SLZ reality:** SLZ is the founding member of a **6-company holding**; phase-1 ERP = SLZ + Helena; sister-company outsourcing is real intercompany activity.
- **Generic ERP default (and our prior assumption):** Single company.
- **Implication:** Company is a first-class, multi-tenant-within-group entity; RBAC, partners, warehouses, WOs scoped by company (DR-040).

---

## Rules that are GENERIC (do NOT need SLZ-specific handling)

For clarity, these are areas where standard ERP conventions are fine and no SLZ-specific rule was found: basic PR→PO→GRN mechanics (beyond the two-stage receipt), standard supplier master fields, generic document approval routing, standard UoM conversion math, and generic audit/who-when. The platform foundation (Task 003) already covers audit, RBAC mechanics, versioning pattern, and bilingual/Jalali — SLZ adds *content*, not new *mechanisms*, there.

See `master-data-impact.md` for how SR-01..SR-16 reshape the Task 004 master-data model.
