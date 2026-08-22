# SLZ ERP — Contradictions & Tensions / تناقض‌ها و تعارض‌ها

Contradictions found across Task 001 documents (including tensions between the **client-supplied proposed flow** and the **analyst's process analysis**). **None are silently resolved** — each carries a proposed resolution and the business decision required.

Severity: **High** = affects DB/model foundations · **Medium** = affects a workflow/policy · **Low** = wording/scope.

---

### C-001 — QC as a single terminal step vs. inline QC at every stage *(High)*
- **Documents:** `business-processes.md` §1 (proposed flow: "…Production → Quality control → Finished goods…") vs `manufacturing-processes.md` §2, `quality-model.md` §2, assumption **A-005**.
- **Contradiction:** The client-proposed lifecycle models Quality Control as one node after production; the analysis asserts QC occurs inline after extrusion, printing, lamination, slitting and final.
- **Why it matters:** Determines where QC gates, holds and cost-of-quality attach; a single terminal gate cannot block a bad intermediate before more value is added.
- **Proposed resolution:** Adopt **inline QC per stage + final QC**; treat the terminal "Quality control" as the final gate only.
- **Business decision required:** Quality to confirm real inspection points *(Q-039, Q-040)*.

### C-002 — "Actual costing" as a final step vs. continuous cost capture *(Medium)*
- **Documents:** `business-processes.md` §1 (flow ends "…Delivery → Actual costing → Profitability") vs `costing-model.md` §1/§7.
- **Contradiction:** The flow implies costing happens once at the end; the costing model captures cost continuously during production and only *settles* at close.
- **Why it matters:** Affects when cost data exists, WIP valuation, and whether mid-order margin is visible.
- **Proposed resolution:** **Continuous cost capture + settlement at order close**; "actual costing" in the flow = settlement.
- **Business decision required:** Finance to confirm costing method & timing *(Q-031, DR-027)*.

### C-003 — Full roll-level traceability vs. optional lot+count tracking / backflush *(High)*
- **Documents:** Traceability principle + `inventory-model.md` §4, FR-055 vs open questions **Q-046** (serialize vs lot+count) and **Q-048** / FR-058 (backflush option).
- **Contradiction:** Full forward/reverse **roll** genealogy (esp. 1→N at slitting) requires serialized rolls and explicit lot/roll issue, but the documents also present lot+count tracking and backflush as acceptable options — which would break roll-level genealogy.
- **Why it matters:** This is the single most foundational data-model decision; retrofitting serialization later is very costly *(risk R-2)*.
- **Proposed resolution:** **Serialize rolls** and use **explicit lot/roll issue** for traceable materials; reserve backflush for bulk consumables only.
- **Business decision required:** Production + Warehouse to decide *(Q-046, Q-048, Q-049; DR-020, DR-031)*.

### C-004 — Multi-level inventoried BOM vs. flow-through intermediates *(High)*
- **Documents:** `bom-and-routing.md` §1 (multi-level BOM with inventoried semi-finished rolls) vs **Q-026** (some intermediates may be flow-through, not stocked).
- **Contradiction:** The BOM model assumes each stage output is an inventoried item; if SLZ does not stock/track certain intermediates, those BOM levels and stock movements should not exist.
- **Why it matters:** Determines the real number of BOM levels, WIP records and stock-movement volume.
- **Proposed resolution:** Make intermediate inventorying **configurable per stage**; model only stages SLZ physically stores/QC's as inventoried items.
- **Business decision required:** Planning + Production *(Q-026; DR-021)*.

### C-005 — Artwork revises independently vs. "every produced configuration is a spec revision" *(Medium)*
- **Documents:** `product-model.md` §5 + FR-012 / **Q-025** (artwork may revise while spec stays ACTIVE) vs the versioning/traceability principle that the exact produced configuration must be reconstructable from the spec revision.
- **Contradiction:** If artwork changes without bumping the spec revision, two batches "made to the same ACTIVE spec revision" may differ in print — weakening exact reproducibility.
- **Why it matters:** Affects reverse traceability precision and re-order fidelity.
- **Proposed resolution:** Keep artwork revisions independent **but** record the **exact artwork revision** on each production batch (not only the spec revision), so the produced configuration is fully captured.
- **Business decision required:** Engineering *(Q-024, Q-025; DR-024)*.

### C-006 — Costing/profitability needs finance data vs. "accounting deferred" *(Medium)*
- **Documents:** `costing-model.md` §3/§8 (needs labor/machine/energy/overhead rates, prices, profitability) vs constraint **#10** (model manufacturing before accounting) and `costing-model.md` §9 (no GL/AR/AP).
- **Contradiction:** Profitability requires cost **rates** and **selling prices** that traditionally live in the deferred accounting/finance domain.
- **Why it matters:** Risk of either stalling costing or prematurely building accounting.
- **Proposed resolution:** Keep **rates and prices as configurable master data inside the ERP** (a thin costing master), independent of a full GL; integrate accounting later *(NFR-023, DR-007)*.
- **Business decision required:** Finance to supply rates and define the ERP/accounting boundary *(Q-033, Q-061)*.

### C-007 — Over/under-delivery vs. exact-quantity order fulfilment & invoicing *(Medium)*
- **Documents:** `costing-model.md` §6 + FR-026 (**Q-006/037** ± tolerance) vs the sales-order fulfilment/costing assumption of ordered quantity.
- **Contradiction:** Unit cost is computed over *delivered* good units while orders/invoices may reference *ordered* quantity; without a tolerance rule these disagree.
- **Why it matters:** Affects order closure ("Fulfilled"), invoicing basis and unit-cost reporting.
- **Proposed resolution:** Define an explicit **± % tolerance** and state whether invoicing is on delivered or ordered quantity.
- **Business decision required:** Management + Sales *(Q-006/037; DR-028)*.

### C-008 — Terminology: analyst English/Persian terms vs. SLZ shop-floor vocabulary *(Low)*
- **Documents:** `README.md` §5 glossary (analyst-proposed Persian terms) vs **Q-001**.
- **Contradiction:** Proposed Persian terms may not match how SLZ staff actually speak.
- **Why it matters:** UI adoption and training.
- **Proposed resolution:** Validate glossary with staff before UI copy is written.
- **Business decision required:** All departments *(Q-001)*.

---

**Count:** 8 contradictions/tensions (High: 3, Medium: 4, Low: 1). All remain **OPEN** pending the business workshop.
