# SLZ Domain Model — Entities Extracted from the NEPTA/SLZ System Documentation

**Source:** `docs/reference/NEPTA_ERP_Feasibility_Study.md` (NEPTA.ERP.SLC.FZS V1.5)
**Date:** 2026-08-21
**Purpose:** Catalogue the **real business entities** the SLZ document describes, independent of any prior Task 001/002 modeling. Each entity is described by: what it represents, who uses it, key fields, lifecycle, whether it is **master** or **transactional**, whether it is **versioned**, whether it needs an **audit trail**, and whether it is **customer-** or **production-specific**.

> This is a **domain extraction**, not a database schema. It records the business reality the document establishes. Where the document is silent on a field or rule, it is marked *(not specified — open question)* rather than invented.

## Legend

- **Kind:** Master (M) = relatively stable reference data · Transactional (T) = event/document with a lifecycle.
- **Versioned:** Yes = the business keeps immutable historical revisions.
- **Audit:** Yes = who/when/what-changed must be traceable.
- **Scope:** company / site / customer / product where the entity is inherently scoped.

---

## A. Organization & foundation

### Company (شرکت)
- **Represents:** A legal company within the NEPTA holding group (SLZ/لفاف زرین, Helena/هلنا, + 4 others).
- **Users:** Group admin, finance, planning.
- **Key fields:** name (fa/en), legal identifiers, group membership, base currency, active flag.
- **Kind:** M · **Versioned:** No · **Audit:** Yes · **Scope:** group.
- **Lifecycle:** created once; rarely changes. Phase-1 = SLZ + Helena; full = 6 companies.

### Site / Plant (سایت/کارخانه)
- **Represents:** A physical production location (Tehran for SLZ; Saveh for Helena).
- **Key fields:** company (FK), name (fa/en), location, **capabilities** (which production stages exist here).
- **Kind:** M · **Versioned:** No · **Audit:** Yes · **Scope:** company.
- **Production-specific:** capability differs by site — Tehran = blown film, cast film, printing, lamination, recycling/grinding, cutting/sewing; Saveh (Helena) = blown film + cutting/sewing only.

### Department / Organizational unit (واحد سازمانی)
- **Represents:** Real units named in the doc: R&D (تحقیق و توسعه), Edit unit (ادیت, for printed-artwork editing), Planning, Production Control (کنترل تولید), Production, QC, Warehouse, Procurement, Finance, HR, Technical/Maintenance (فنی), and **sales lines by product group**.
- **Kind:** M · **Versioned:** No · **Audit:** Yes · **Scope:** company/site.

---

## B. Commercial / partner master

### Partner (person/organization) — Customer / Supplier
- **Represents:** External party. The doc treats customers and suppliers as roles on parties.
- **Users:** Sales lines, procurement, finance.
- **Key fields:** name (fa/en), type (customer/supplier/both), tax/legal IDs, addresses, contacts, **sales line / product group** (customers), evaluation data (suppliers), **sanctioned-party flag**, settlement terms (راس تسویه — finance phase).
- **Kind:** M · **Versioned:** No (but change-audited) · **Audit:** Yes · **Scope:** company.
- **Customer-specific:** customer approves drawings/proof; customer specifies marking per packaging level.

### Contact (مخاطب) & Address
- **Represents:** People and locations attached to a partner; CRM adds leads/contacts/call-center.
- **Kind:** M · **Audit:** Yes.

### Lead / Opportunity / Campaign / Complaint (CRM)
- **Represents:** Full CRM pipeline: lead → contact → opportunity/pipeline → forecast; campaigns; customer feedback & complaint management.
- **Kind:** T · **Versioned:** No · **Audit:** Yes · **Phase:** later (whole CRM domain, NQ-009).

---

## C. Product engineering & master data

### Product (محصول) — layered/calculated customer product
- **Represents:** A customer's finished flexible-packaging product. "Precise product definition is one of NEPTA's biggest challenges."
- **Users:** R&D, Edit, Sales, Planning, Production, QC.
- **Key fields:** classification **type → class → family (نوع/طبقه/خانواده)** + product group; dimensional parameters; **product drawing / technical production drawing**; BOM types; OPC; **material formulation (main + alternative)**; **ink/color formulation** (if printed); **MSDS / storage info**; **design & cliché profile**; **targets (تارگت)**; **marking (مارکینگ)** per packaging level; **pallet spec**; QC checklist; derived **SKU**.
- **Kind:** M · **Versioned:** **Yes** (spec revisions) · **Audit:** Yes · **Scope:** customer + product.
- **Customer/production-specific:** dependent parameters (roll diameter & count, pallet count) are **derived by the system** from the customer's main parameters → SKU.

### SKU / Product code
- **Represents:** Generated identifier encoding derived parameters. Repeats reuse prior SKU history.
- **Kind:** M · **Versioned:** with product · **Audit:** Yes.

### Material / Item (کالا/ماده)
- **Represents:** Any stocked item. **Subtyped**: resin/masterbatch (RM), **ink (مرکب)**, **solvent (حلال)**, production consumables (ملزومات), packaging, semi-finished, finished, **regrind** (from recycling).
- **Key fields:** code, name (fa/en), subtype, **multiple UoM + conversions**, substitutes, min/max/reorder, safety stock, EOQ, lead time, **shelf-life/expiry**, MSDS.
- **Kind:** M · **Versioned:** No · **Audit:** Yes.
- **MRP-relevant:** MRP explicitly spans RM, consumables, ink, and solvent.

### BOM (فرمولاسیون / نوع BOM) & Routing / OPC
- **Represents:** Product structure(s) — **multiple production BOMs per product** — plus operation sequence (OPC). Includes **print mounting calculation (مونتاژ چاپ)**.
- **Kind:** M · **Versioned:** **Yes** (immutable revisions, ECN-driven) · **Audit:** Yes · **Scope:** product.

### Engineering Change Notice (ECN — اعلامیه تغییر مهندسی)
- **Represents:** Controlled change to spec/BOM/routing.
- **Kind:** T · **Versioned:** produces new versions · **Audit:** Yes.

### Cliché / Printing tooling (کلیشه/برگ/دست)
- **Represents:** Flexo printing tooling as a **first-class asset**: ID cards for cliché / sheet (برگ) / set (دست); **usage-life recording**; stored in a **dedicated cliché warehouse**.
- **Kind:** M (asset) · **Versioned:** No (but revised with artwork) · **Audit:** Yes · **Scope:** customer/product.

---

## D. Planning & manufacturing

### Capacity table (ظرفیت)
- **Represents:** Capacity **by product × machine (× site)**, maintained annually by Production, supervised by Production Control; input to production feasibility.
- **Kind:** M (data-driven) · **Versioned:** annual snapshots · **Audit:** Yes · **Scope:** site.

### Production feasibility (امکان‌سنجی تولید)
- **Represents:** Planning check from sales forecast + capacity before commitment; feeds delivery-date/ATP estimation.
- **Kind:** T · **Audit:** Yes.

### Production order / Work order (سفارش تولید)
- **Represents:** Order to produce; **by customer order (MTO)**. Operations may be **outsourced** (internal sister company or external vendor).
- **Key fields:** product/SKU, quantity, routing operations, assigned machines, **machine settings per order**, priority (**by margin**), scrap/downtime capture.
- **Kind:** T · **Versioned:** No · **Audit:** Yes · **Scope:** site.

### Machine-settings library
- **Represents:** Optimal settings keyed by **machine × product**, learned from production/waste history.
- **Kind:** M (data-driven) · **Audit:** Yes.

### Allowed-scrap table & Allowed-downtime-limit table
- **Represents:** Thresholds **by machine × product**; drive scrap/downtime evaluation.
- **Kind:** M (data-driven) · **Audit:** Yes.

### Scrap / Waste record & Downtime record & Shift-event log
- **Represents:** Captured with **reason codes**; shift event log per machine.
- **Kind:** T · **Audit:** Yes · **Scope:** site.

### Recycling / Grinding (بازیافت/آسیاب)
- **Represents:** Converts scrap into reusable **regrind** material lots (Tehran only).
- **Kind:** T (produces material lots) · **Audit:** Yes · **Scope:** site.

### Rework (دوباره‌کاری)
- **Represents:** Non-conforming output → some scrap, some reworked → sellable; also sales-return QC.
- **Kind:** T · **Audit:** Yes.

---

## E. Quality

### Quality plan / standard / criteria / parameters
- **Represents:** QC standards, criteria, parameters; **per-operation QC sheets based on production rolls**; defect tree.
- **Kind:** M · **Versioned:** **Yes** · **Audit:** Yes · **Scope:** product.

### QC inspection / result
- **Represents:** Inline & post inspection. **Out-of-range auto-action: message + stop production WO + issue rework WO.** Incoming QC uses **temporary vs definitive receipt** gated on a QC pass threshold.
- **Kind:** T · **Audit:** Yes.

### Non-conformance / Quarantine
- **Represents:** Quarantine store; NCR lifecycle.
- **Kind:** T · **Audit:** Yes.

### COA (گواهی تحلیل)
- **Represents:** Bilingual certificate of analysis issued on release.
- **Kind:** T (document) · **Audit:** Yes.

---

## F. Inventory & procurement

### Warehouse / Store (انبار)
- **Represents:** **Unlimited warehouses**; **special store types**: scrap, quarantine, **cliché**, line-side (پای کار), consignment (امانی), stagnant (راکد). **Per-user warehouse access.**
- **Kind:** M · **Audit:** Yes · **Scope:** site.

### Stock movement / Kardex (کاردکس)
- **Represents:** Quantity **and rial** kardex; inter-warehouse transfers; stocktaking; year-end; Excel import.
- **Kind:** T · **Audit:** Yes.

### Consumption permit (مجوز مصرف)
- **Represents:** Authorizes consumption/issue (gift/sample/consumables).
- **Kind:** T · **Audit:** Yes.

### Lot / Roll (بچ/رول) — traceability
- **Represents:** Raw-material ID card + roll/lot genealogy for **traceability (ردیابی)** across stages.
- **Kind:** T (identity+genealogy) · **Audit:** Yes · **Production-specific:** roll-level serialization (granularity still open, Q-046).

### Purchase Requisition → Inquiry → Purchase Order → Receipt
- **Represents:** PR (MRP-driven) → supplier inquiry → PO (internal/external/procurement) → payment order → GRN. Includes **import process** (proforma, insurance, arrival notice), **sanctioned-party control**, **FX/تسعیر**, documentary trade.
- **Kind:** T · **Audit:** Yes.

### Supplier evaluation
- **Represents:** Definition + periodic evaluation of suppliers.
- **Kind:** M+T · **Audit:** Yes.

---

## G. Finance, maintenance, HR (later phases — real domains)

### Finance (مالی)
- Chart of accounts / persons / **floating (شناور)** / cost centers / projects; sales & purchase accounting; treasury; **product cost (بهای تمام‌شده)**; **customer settlement date (راس تسویه)**; budgets per section; **asset system**; payroll.
- **Kind:** mixed M/T · **Audit:** Yes · **Phase:** later (NQ-010; reinforces C-006).

### Maintenance / Technical (فنی)
- **Equipment ID card** + spare-parts structure; PM types & periodic planning; service checklists; machine-stop reasons; runtime; **MRO work orders**; inspection results.
- **Kind:** mixed · **Audit:** Yes · **Phase:** later.

### HR
- **Org decrees (احکام)**; salary calculator; recruit/hire/terminate/transfer; evaluation; contracts; **attendance**. Employee master needed sooner for production skills.
- **Kind:** mixed · **Audit:** Yes · **Phase:** later (Employee master earlier).

---

## H. Cross-cutting observations

- **Versioned entities:** Product/spec, BOM/routing, quality plan (immutable revisions, ECN-driven) — matches the platform `VersionedRoot`/`Revision` pattern from Task 003.
- **Data-driven (not hard-coded) tables:** capacity, machine-settings, allowed-scrap, allowed-downtime — all keyed by machine×product(×site). Reinforces the "no hard-coded machine logic" constraint.
- **Everything audited:** the document's pervasive approval/traceability expectations align with the generic audit trail already built.
- **Company/site scoping is inherent**, not an add-on: partners, warehouses, capacity, WOs, and RBAC are all naturally scoped by company/site.

See `master-data-impact.md` for how this maps onto the Task 004 master-data model, and `slz-specific-rules.md` for the SLZ-specific mechanics that generic ERP would get wrong.
