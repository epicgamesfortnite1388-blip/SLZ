# Master-Data Impact — Re-evaluation of the Task 004 Model Against the SLZ Documentation

**Source of truth:** `docs/reference/NEPTA_ERP_Feasibility_Study.md` + `slz-domain-model.md` + `slz-specific-rules.md`
**Date:** 2026-08-21
**Purpose:** Re-evaluate the **Task 004 (Master Data Foundation)** entity set in light of the confirmed SLZ reality. For each master-data entity: what the Task 004 brief assumed, what the document requires, and the resulting **impact**. This does **not** implement anything — it re-scopes Task 004 so implementation (when authorized) is correct.

> Reminder: the Task 004A brief says **do not blindly follow the earlier Task 004 prompt**. Where the document corrects it, the document wins.

## Impact legend
`KEEP` — model as planned · `EXPAND` — add fields/relations · `RESTRUCTURE` — change the shape · `ADD` — new entity not in Task 004 · `DEFER` — real but later phase · `GATE` — blocked on an open business decision.

---

## R-MD-01 — Company (multi-company)  → **RESTRUCTURE / GATE**
- **Task 004 assumed:** Company exists but effectively single-company.
- **Document requires:** NEPTA **6-company holding**; phase-1 = **SLZ (Tehran) + Helena (Saveh)**. Intercompany outsourcing is real.
- **Impact:** Company must be genuinely multi-company; nearly all master data is **company-scoped**. **GATE on NQ-002** (exact company/site list) — but SLZ+Helena is safe to model now. (DR-040 CONFIRMED.)

## R-MD-02 — Site / Plant  → **EXPAND**
- **Document requires:** Site carries **capabilities** (which production stages exist). Capability differs Tehran vs Saveh (SR-15).
- **Impact:** Add Site under Company with a **capability set**; capacity tables are site-scoped. Foundation `organization` app (Task 003) already has org entities — extend, don't rebuild. (DR-041 OPEN — modeling approach.)

## R-MD-03 — Department / Org unit  → **EXPAND**
- **Document requires:** Real units — R&D, Edit, Planning, Production Control, Production, QC, Warehouse, Procurement, Finance, HR, Technical/Maintenance, and **sales lines by product group**.
- **Impact:** Department taxonomy should accommodate these; **sales line** is a department-like grouping keyed to product group (feeds RBAC scoping).

## R-MD-04 — Partner / Customer / Supplier  → **EXPAND**
- **Task 004 assumed:** Partner with customer/supplier roles, contacts, addresses.
- **Document requires:** customer **sales line / product group**; supplier **evaluation**; **sanctioned-party flag** (SR + NFR-022); settlement terms (finance phase); customer drawing/proof approval & per-level marking authority.
- **Impact:** Keep the party+roles shape; **EXPAND** with sanction flag, sales-line link (customers), evaluation block (suppliers). CRM (leads/opportunities/complaints) is **DEFER** (NQ-009).

## R-MD-05 — Contacts & Addresses  → **KEEP**
- Model as planned (attached to Partner). CRM extends later.

## R-MD-06 — Employee  → **DEFER (partial KEEP)**
- **Document requires:** Full HR later; but **Employee master needed sooner** for production skills/operator identity and warehouse/user access.
- **Impact:** A **minimal Employee** (identity, department, site) is justified early; full HR (decrees, payroll, attendance) is **DEFER**.

## R-MD-07 — UoM + conversions  → **KEEP (confirmed core)**
- **Document confirms (A-021):** multiple UoM per item + conversions + substitutes. This is **early, core** master data. Model UoM and conversion factors now.

## R-MD-08 — Product Category / Taxonomy  → **RESTRUCTURE**
- **Task 004 assumed:** Product categories (flat/simple).
- **Document requires:** **type → class → family (نوع/طبقه/خانواده)** + **product group**; product groups also structure **sales lines** and CRM.
- **Impact:** Multi-level classification, not a single category field (SR-02).

## R-MD-09 — Product  → **EXPAND / careful scoping**
- **Task 004 brief itself warned:** do not prematurely build CustomerProduct/Specification/BOM/Routing/Artwork/Tooling/Production.
- **Document requires:** the *master* Product carries classification + identity; the **rich versioned spec, formulations, drawings, marking, SKU derivation** belong to **Product Engineering (planned Task 005)**, not Task 004.
- **Impact:** In Task 004 keep Product as an identified, classified master item with UoM and category. **SKU-derivation service, spec revisions, formulations, cliché** → **DEFER to Task 005** (SR-01/02). Avoid baking business logic into the Task 004 product record.

## R-MD-10 — Material / Item  → **RESTRUCTURE**
- **Document requires:** **subtypes** — resin/masterbatch, **ink**, **solvent**, consumables, packaging, semi-finished, finished, **regrind** — because MRP/formulation/QC treat them distinctly (SR-04); plus multi-UoM, substitutes, min/max/reorder, safety stock, EOQ, lead time, **shelf-life/expiry**, MSDS.
- **Impact:** Material master needs a **subtype** discriminator and subtype-specific fields from the start; this is a Task 004 concern (it is master data), even though MRP itself is later.

## R-MD-11 — Business codes / numbering  → **KEEP + EXPAND**
- **Foundation (Task 003):** UUID PKs; business numbers are separate fields.
- **Document adds:** SKU generation (product), and coding for materials/partners/warehouses. Keep UUID+business-number separation; **the SKU generator is a Task 005 service**, but the *field* can exist on Product master.

## R-MD-12 — Warehouse (master)  → **EXPAND**
- **Document requires:** unlimited warehouses; **store types** (scrap/quarantine/cliché/line-side/consignment/stagnant); per-user access. Warehouse *definition* is master data (Task 004-adjacent); movements/kardex are later.
- **Impact:** If warehouse master is in Task 004 scope, add a **store-type** enum and site scoping; otherwise flag for the inventory task. (Task 004 brief did not clearly include Warehouse — **GATE / confirm scope**.)

## R-MD-13 — Tooling / Cliché  → **DEFER (to Task 005)**
- First-class asset with usage-life + dedicated store (SR-03), but tied to artwork/product engineering. **Not** Task 004; belongs with Product Engineering. Record now so it is not forgotten.

---

## Revised Task 004 master-data scope (recommendation)

**In scope for Task 004 (safe, confirmed, foundational):**
- Company (multi-company: SLZ + Helena) — RESTRUCTURE
- Site (with capability set) — EXPAND
- Department / sales-line — EXPAND
- Partner + Customer/Supplier roles (+ sanction flag, sales-line, supplier-eval stub) — EXPAND
- Contacts + Addresses — KEEP
- Minimal Employee (identity/department/site) — partial
- UoM + conversions — KEEP
- Product classification taxonomy (type→class→family + group) — RESTRUCTURE
- Product **master identity** only (classified, UoM, category; **no** spec/BOM/SKU-logic) — careful EXPAND
- Material master with **subtype** discriminator — RESTRUCTURE

**Explicitly deferred (later tasks):**
- Product Engineering: spec revisions, formulations (main/alt, ink/solvent), drawings, marking, **SKU-derivation service**, **print mounting**, Tooling/Cliché → **Task 005**.
- BOM / Routing / OPC, capacity/machine-settings/allowed-scrap tables → Manufacturing tasks.
- Warehouse store logic, kardex, consumption permit, lot/roll genealogy → Inventory task.
- CRM, Finance, HR (full), Maintenance, Foreign-trade → later domains.

**Gated on business decisions before Task 004 implementation:**
- **NQ-001 build vs buy** (critical — the whole custom build is contingent).
- **NQ-002** exact company/site list beyond SLZ+Helena.
- Warehouse-master scope for Task 004 (in or out).

## Bottom line

The Task 004 entity list is **largely valid but must be reshaped**: multi-company/site becomes real, taxonomy becomes multi-level, Material gains subtypes, and Product stays a *thin classified master* with all engineering logic pushed to Task 005. None of this is implemented in Task 004A. Implementation of Task 004 remains **gated on NQ-001 and NQ-002**.
