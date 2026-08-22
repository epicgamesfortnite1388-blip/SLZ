# SLZ Actual End-to-End Workflow (as described by the NEPTA/SLZ documentation)

**Source:** `docs/reference/NEPTA_ERP_Feasibility_Study.md` (NEPTA.ERP.SLC.FZS V1.5)
**Date:** 2026-08-21
**Purpose:** Reconstruct the **real, order-to-delivery workflow** the document describes, so future implementation follows SLZ's actual process rather than a generic ERP flow. Steps are drawn from the document's domain sections (CRM/Sales, Product Engineering, Planning, Production/Control, Quality, Warehouse, Procurement). Where the document does not specify a rule, it is flagged as an open question rather than assumed.

## 0. Nature of the flow

Production is **made-to-order (MTO)** and driven **by customer order**; standard-product sales are minor. New products follow an **engineer-to-order (ETO)-like** path (imprecise parameters, R&D, drawings, proof approval); repeats reuse the existing SKU and history. Production capability is **site-specific** (Tehran full chain incl. printing/lamination/recycling; Helena/Saveh only blown film + cutting/sewing).

---

## 1. Lead → Inquiry (Sales)

1. (CRM, later phase) Lead/contact/opportunity captured; sales organized into **lines by product group**.
2. Order begins as a **Sales Inquiry (استعلام فروش)**. For **new products**, parameters may be **imprecise/undefined** initially; for **repeats**, the prior **SKU and order history** are reused.

## 2. Product definition & feasibility (R&D / Edit / Engineering)

3. System **calculates dependent parameters** (roll diameter & count, pallet count, …) from the customer's **main parameters** and **generates the SKU**.
4. For **new/printed** products: technical feasibility routed to **R&D**; artwork handled by the **Edit unit (ادیت)**.
5. **Customer approves drawings** — product drawing / technical drawing / **Proof** — before commitment. *(Physical first-article/sample sign-off rule still open — Q-003.)*
6. Product master is completed: classification (type→class→family), dimensional params, BOM type(s), OPC, **material formulation (main + alternative)**, **ink/color formulation** (if printed), **MSDS/storage**, **design & cliché profile**, **targets**, **marking per packaging level**, **pallet spec**, QC checklist. Spec is **versioned**; changes go through **ECN**.
7. If printed and new tooling is needed: **cliché/sheet/set (کلیشه/برگ/دست)** created and profiled; **print mounting (مونتاژ چاپ)** calculated.

## 3. Quotation → Proforma → Order (Sales)

8. **Proforma (پیش‌فاکتور)** produced by a **pricing algorithm** (price from product characteristics, packaging, volume, RM price, margin) + **approval workflow**. Quotation/proforma is **versioned**.
9. **Delivery-date / ATP** estimated from capacity, current open orders, RM stock, and supply lead time.
10. On customer acceptance → **Sales Order** confirmed.

## 4. Planning (Planning + Production Control)

11. **Production feasibility (امکان‌سنجی)** evaluated from sales forecast + **capacity table (by product×machine×site)**; capacity is maintained annually by Production, supervised by Production Control.
12. **MRP** run across **RM, consumables, ink, solvent**: reservations, safety stock, EOQ, lead times → **purchase requests** on shortfall.
13. **Production orders / work orders** generated; **priority by margin**; operations may be **outsourced** (internal sister company or external vendor).

## 5. Procurement (if MRP signals shortfall)

14. **PR → supplier inquiry → PO** (internal/external/procurement); payment order.
15. For imports: **proforma, insurance, arrival notice**, **sanctioned-party screening**, **FX/تسعیر**, documentary trade.
16. **Goods receipt**: **temporary receipt** → **incoming QC** → **definitive receipt** once QC pass threshold met. Rejected material quarantined.

## 6. Production (per site capability) — the manufacturing chain

For each routing operation (e.g., extrusion/**blown or cast film** → **printing (flexo)** → **lamination** → slitting → cutting/sewing/converting), at the responsible **machine × site**:

17. Operator loads **machine settings for the order** (defaults from the machine-settings library, keyed by machine×product).
18. **Roll/lot identity** created and carried forward for **traceability (genealogy)** across operations.
19. **Inline QC** per operation using **per-operation QC sheets based on production rolls**.
    - **Out-of-range → automatic action:** system message **+ stop the production WO + issue a rework WO**.
20. **Scrap/waste** and **downtime** recorded with **reason codes**; evaluated against **allowed-scrap** and **allowed-downtime** tables (by machine×product); **shift-event log** maintained.
21. **Rework (دوباره‌کاری):** non-conforming output → some scrapped, some reworked → sellable.
22. **Recycling/grinding** (Tehran): scrap converted into **regrind** material lots for reuse.
23. Outsourced operations: material issued out, returned, then **QC on return** and cost captured.

## 7. Final quality & release

24. **Final QC**; defect tree classification; **quarantine** for holds.
25. **COA (گواهی تحلیل)** issued (bilingual) on release.

## 8. Warehouse & dispatch

26. Finished goods received to a warehouse (of many; special stores for scrap/quarantine/cliché/line-side/consignment/stagnant). **Kardex** updated (quantity **and rial**).
27. **Consumption permits** authorize non-order issues (gift/sample/consumables).
28. Dispatch to customer per **marking/pallet spec**; **inter-warehouse transfers** as needed.
29. Reverse flows: **sales-return QC**, rework or scrap.

## 9. Finance (later phase, but expected)

30. Product **costing (بهای تمام‌شده)**, sales/purchase accounting, treasury, **customer settlement date (راس تسویه)**, budgets, assets, payroll. *(Deferred for now — reinforces C-006 / NQ-010.)*

---

## Workflow-level open questions (carried forward)

- **Q-003** physical first-article/sample sign-off (document confirms drawing/proof approval only).
- **Q-046** roll-level serialization granularity for genealogy.
- **Q-026** BOM level count; **Q-006** over/under-delivery tolerance on order fulfillment.
- **NQ-001** build vs buy; **NQ-002** exact company/site list; **NQ-004** outsourced-operation modeling; **NQ-007** print-mounting calc; **NQ-008** marking model; **NQ-009** CRM phase; **NQ-010** finance phase.

See `slz-specific-rules.md` for the mechanics in steps 3, 6, 11, 17–22 that differ from generic ERP, and `current-to-future-system.md` for the mapping of each step onto the new ERP domain model.
