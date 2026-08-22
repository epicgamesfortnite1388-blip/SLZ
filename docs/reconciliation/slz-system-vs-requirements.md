# Reconciliation — NEPTA/SLZ System Documentation vs. Task 002 Requirements

**Reconciliation date:** 2026-08-21
**Source:** `docs/reference/NEPTA_ERP_Feasibility_Study.md` (NEPTA.ERP.SLC.FZS V1.5)
**Compared against:** `docs/requirements/` — `requirements-baseline.md` (FR/NFR), `decision-register.md` (DR), `contradictions.md` (C), `do-not-build-yet.md`, and `docs/business-review/business-review-fa-en.md`.

This document classifies the impact of the source document on the Task 002 baseline. Requirement text is **not** rewritten here; changes are logged in `docs/requirements/requirements-changelog.md` and statuses updated in `docs/requirements/decision-register.md`.

## 1. Requirements now CONFIRMED (evidence in the document)

| Requirement | Evidence in document |
|-------------|----------------------|
| FR-001/013 layered, calculated, classified customer product; SKU generation | System calculates dependent parameters and creates SKU; classify by type/class/family |
| FR-002/003/031/035 versioned, immutable specs/BOM/routing; ECN | Engineering change mgmt, version control, ECN (اعلامیه تغییر مهندسی) |
| FR-009/010/012 artwork + printing tooling lifecycle | Cliché management (شناسنامه کلیشه/برگ/دست), usage recording, cliché warehouse, design/cliché profile |
| FR-020/021/022 inquiry → versioned quotation/proforma → order | Sales Inquiry, proforma from pricing algorithm + approval workflow |
| FR-024 new-product vs repeat paths | Inquiry with imprecise params for new; reuse SKU history for repeats |
| FR-034 alternate/substitute materials | Material formulation main + alternative; substitute items in warehouse |
| FR-040/041/042/048 work centers, machine capability, per-WO capture, changeover | Machine settings per production order; capacity by product-machine; optimal-settings identification |
| FR-043/045 scrap & downtime with reason codes | Waste types & reasons; downtime issuance; allowed-scrap & allowed-downtime tables by machine-product |
| FR-044 rework as traced pass | Rework management (دوباره‌کاری): non-conforming → scrap or rework → sellable |
| FR-050/053/055 lot tracking, stock movements, genealogy/traceability | Raw-material ID card; traceability (ردیابی); kardex; inter-warehouse transfers |
| FR-057 multiple UoM + conversions | چند واحد شمارش per item |
| FR-059 shelf-life/expiry (+ FEFO capability) | تاریخ انقضاء و Shelf life in material planning |
| FR-070/071/072/073/074 versioned quality plans, inline+final QC, NCR, QC-hold | QC standards/criteria/parameters; per-operation QC sheets; auto stop/rework on out-of-range; defect tree; quarantine |
| FR-076 bilingual COA | صدور گواهی تحلیل (COA) |
| FR-080/081/082 suppliers, PR→PO→GRN, incoming QC | Supplier definition & evaluation; PR/inquiry/PO; temporary vs definitive receipt on QC threshold |
| FR-100 maintenance orders | Equipment ID card, PM planning, MRO work orders, service checklists |
| FR-110/114 audit, attachments/object storage | Document approval flows; MSDS, drawings, proofs, cliché profiles |
| FR-113 / NFR-010/011 bilingual fa/en + Jalali/Gregorian | Persian-language business document authored in Jalali dates; group is Iranian |
| NFR-022 sanction-aware / self-hostable | تحریم و مشکلات تامین و انتقال ارز; sanctioned-party control; infra limits |

## 2. Requirements needing MODIFICATION

| Requirement | Change required | Reason |
|-------------|-----------------|--------|
| **Company/site model (org foundation; underpins most FRs)** | Make **multi-company (NEPTA group)** and **multi-site (Tehran/Saveh)** first-class, with **site-scoped production capability & capacity**. | SLZ is one of six NEPTA companies; phase-1 = SLZ + Helena; Helena runs only blown film + cutting. |
| FR-036/041 operation/work-order model | Allow an operation to be **outsourced** (internal sister company or external vendor). | Production outsourcing (برون‌سپاری) of stages. |
| FR-030/031 BOM levels + FR-050 materials | **Material must be subtyped** (resin/masterbatch, **ink مرکب**, **solvent حلال**, consumable ملزومات, packaging); MRP treats them distinctly. | MRP explicitly spans RM, consumables, ink, solvent. |
| FR-006/007 spec parameters | Add **explicit fields**: MSDS/storage, ink/color formulation, targets (تارگت), per-packaging-level **marking (مارکینگ)**, pallet spec. | Product-master content in §مهندسی/تکوین محصول. |
| FR-052 warehouse model | Add **special store types**: scrap, quarantine, **cliché**, line-side (پای کار), consignment (امانی), stagnant (راکد); per-user warehouse access; **consumption permit**. | §انبار. |
| FR-090..097 costing | Reconcile with the fact that the business expects a **full finance domain** (product cost, treasury, AR/AP, settlement date, assets, payroll), not just shop-floor costing. | §مالی. |
| NFR-002/RBAC | Permission/role model must support **company- and site-scoped** access and **sales lines by product group**. | Multi-company + sales-line structure. |

## 3. Requirements to ADD (new, introduced by the document)

| New req (proposed id) | Description | Phase note |
|-----------------------|-------------|------------|
| FR-NEW-CRM (domain) | Lead, Contact, Call-center/VOIP, Opportunity/pipeline, Sales forecasting (top-down quota + bottom-up), Campaign, Customer feedback, Complaint management. | Later phase; not in current manufacturing scope. |
| FR-NEW-FIN (domain) | GL/persons/floating/centers/projects, sales & purchase accounting, treasury, product costing, customer settlement date (راس تسویه), budgets, assets, payroll. | Later phase; supersedes "accounting deferred" eventually. |
| FR-NEW-HR (domain) | Org decrees, salary calculator, recruit/hire/terminate/transfer, evaluation, contracts, attendance. | Later phase. |
| FR-NEW-TRADE | Import/foreign-trade: proforma, insurance, arrival notice; sanctioned-party screening; FX conversion (تسعیر); documentary trade. | Extends procurement. |
| FR-NEW-OUTSRC | Outsourced production operations (internal/external), with costing & QC on return. | Extends manufacturing/costing. |
| FR-NEW-RECYCLE | Recycling/grinding (بازیافت/آسیاب) of scrap into reusable regrind material lots. | Extends manufacturing/inventory. |
| FR-NEW-SKU | SKU/product-code generation: derive dependent parameters (roll diameter/count, pallet count) from customer main parameters. | Belongs to master data / product engineering. |
| FR-NEW-MOUNT | Print mounting calculation & suggestion (مونتاژ چاپ). | Product engineering. |
| FR-NEW-DELEST | Delivery-date/ATP estimation from capacity, open orders, stock, lead times. | Sales ↔ planning. |
| FR-NEW-CAP | Capacity model as **table by product×machine×site**, annually maintained; production-feasibility check. | Planning. |
| FR-NEW-MSET | Machine-settings library keyed by machine×product (optimal settings from production/waste history). | Manufacturing. |

## 4. Requirements to potentially REMOVE / rescope

None are outright removed. The manufacturing-centric baseline stands. The only rescoping is **strategic**: if the business reaffirms the document's **buy Microsoft Dynamics 365 F&O** recommendation (NQ-001), then the entire custom **build** requirement set changes character (configuration vs. construction). This is escalated, not resolved.

## 5. Assumptions now DISPROVED or CONFIRMED

- **Disproved:** the implicit **single-company** assumption underlying the whole baseline (SLZ is one of six NEPTA companies; phase-1 spans SLZ + Helena).
- **Confirmed:** A-001, A-003, A-005, A-006, A-011, A-013, A-014, A-018, A-019, A-020, A-021 (see `slz-system-vs-task001.md` §F). A-002 partially confirmed.

## 6. Decision-register impact (see `decision-register.md` for applied changes)

| Decision | New status | Rationale |
|----------|-----------|-----------|
| **DR-000 (new) Build vs Buy** | **OPEN — CRITICAL** | Document recommends buying D365 F&O; custom build must be reaffirmed by business. |
| **DR-040 (new) Company scope / multi-company** | **CONFIRMED (business fact)** | NEPTA group; phase-1 SLZ + Helena, per official doc. |
| **DR-041 (new) Site-specific capability & capacity** | **OPEN** | Capability differs by site; modeling approach unconfirmed. |
| DR-001/002/011 (custom stack) | **PROPOSED — CONFLICT FLAGGED** | Outranked by document's buy recommendation until NQ-001 resolved. |
| DR-036 shelf-life/FEFO | **OPEN (evidence added)** | Expiry tracked; enforcement policy still open (Q-051). |
| NFR-022 sanctions | **CONFIRMED relevant** | Explicit sanction/FX constraints; answers Q-064. |
| Others (DR-020..035, cost/valuation/thresholds) | **OPEN (unchanged)** | Document gives requirements, not the parametric business rules. |

## 7. Contradictions impact

- Reinforces **C-006** (costing needs finance data vs. "accounting deferred") — the business plainly expects finance.
- Adds **new contradictions** tracked in `slz-system-vs-task001.md` (R-01..R-04): build-vs-buy, single-company vs holding, single-site vs site-specific capability, manufacturing-only vs broad scope.
- C-001..C-005, C-007, C-008 remain **OPEN**; the document does not resolve the roll-serialization, BOM-level, or over/under-delivery specifics (still Q-046/026/006).

## 8. Net effect on Task 002 readiness

Task 002's verdict was "READY FOR PLATFORM FOUNDATION." That remains true for the **platform** (the document validates bilingual/Jalali, audit, RBAC, object storage, multi-company org — all already built in Task 003). However, **domain readiness is now gated on NQ-001 (build vs buy) and NQ-002 (company scope)** in addition to the previously open business decisions. See `master-data-impact.md` for what this means for Task 004.
