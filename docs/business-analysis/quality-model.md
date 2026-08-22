# Quality Model

> Tags: **[CONFIRMED]** · **[ASSUMPTION]** · **[OPEN]** · **[PROPOSAL]**.
> Quality is **inline at every stage** plus final (see `manufacturing-processes.md` §2). Quality data must integrate with traceability and costing.

---

## 1. Core quality entities [PROPOSAL, concepts from brief]

| Entity | Purpose |
|--------|---------|
| **Quality Check (QC)** | A single inspection/measurement event against a defined characteristic, tied to a work order / production batch / roll / incoming lot. |
| **Quality Plan / Inspection Plan** | The set of characteristics + methods + tolerances to check at a given operation or on a given material. Versioned. |
| **Quality Characteristic** | What is measured (thickness, ΔE, bond strength, seal strength, COF, dimensions…), with method + spec limits (from product spec tolerances). |
| **Quality Alert / Non-Conformance (NCR)** | Raised when a check fails or an issue is detected; drives hold/rework/scrap and CAPA. |
| **Scrap record** | Rejected material quantity + reason code + stage + cost linkage. |
| **Rework record** | Material sent back through an operation to correct a defect. |
| **COA (Certificate of Analysis)** | Bilingual quality certificate issued with delivery, referencing batch results. |

---

## 2. Where checks happen [ASSUMPTION A-005 / A-018]

| Point | Typical characteristics |
|-------|-------------------------|
| **Incoming (RM)** | Resin/film/ink/adhesive lot acceptance: spec conformity, moisture, dyne, viscosity. |
| **After extrusion** | Thickness/micron, width, layer integrity, corona/dyne level, gel/defects. |
| **After printing** | Color match (ΔE vs standard), registration, print defects, adhesion/rub. |
| **After lamination** | Bond/laminate strength, appearance (tunneling/bubbles), coat weight, cure. |
| **After slitting** | Width accuracy, roll quality, telescoping, core/winding. |
| **Final / converting** | Seal strength, leak/burst, dimensions, bag defects, count. |
| **Pre-ship** | COA data, packing, labeling. |

**[OPEN Q-039]** Provide SLZ's actual inspection plans, test methods (standards), and equipment per stage. **[OPEN Q-040]** Sampling rules (100% vs AQL sampling plan; sample size)?

---

## 3. Quality check result model [PROPOSAL]
```
Quality Check
 ├ ref: {incoming_lot | work_order | production_batch | roll}
 ├ characteristic: FK (with spec limits from product spec revision)
 ├ method / instrument
 ├ measured_value(s)  (numeric | attribute pass-fail | text)
 ├ result: PASS | FAIL | CONDITIONAL
 ├ inspector, timestamp (UTC + Jalali/Gregorian)
 └ → on FAIL: raises Quality Alert / NCR
```
- Results are **immutable** once recorded; corrections create a new record (audit).

---

## 4. Non-conformance / alert lifecycle [PROPOSAL]
```
OPEN → UNDER_REVIEW → DISPOSITION → CLOSED
                          │
   disposition ∈ { ACCEPT_AS_IS (concession),
                   REWORK,
                   SCRAP,
                   RETURN_TO_SUPPLIER (incoming),
                   DOWNGRADE }
```
- A failed check can put the affected batch/roll on **QC_HOLD** (blocks consumption/shipment) until disposition.
- **CAPA** (corrective/preventive action) optionally linked. **[OPEN Q-041]** Does SLZ run formal CAPA/8D, or lightweight disposition only?

---

## 5. Scrap & rework [CONFIRMED concepts]

### 5.1 Scrap
- Reason-coded (setup waste, print defect, lamination defect, contamination, color reject, dimension out-of-tol…).
- Removes quantity from WIP/inventory via a **stock movement** (scrap issue) and carries cost (see `costing-model.md` §4).
- **[OPEN Q-016/042]** Standard scrap reason-code list per stage.

### 5.2 Rework
- Sends a batch/roll back through an operation (or a special rework operation). Adds cost (extra labor/machine/material) and is fully traced (genealogy preserved).
- **[OPEN Q-043]** Which defects are reworkable vs. always scrap? Any customer approval needed to ship reworked material?

---

## 6. Quality ↔ traceability integration [CONFIRMED principle]
- Every check links to a lot/batch/roll, so a failed characteristic can be traced **forward** (which finished lots/deliveries are affected → recall) and **backward** (which RM lot/machine/operator/shift caused it).
- Supports **recall / mock-recall** exercises. **[OPEN Q-044]** Does SLZ need formal recall capability (food-contact products often do)?

---

## 7. Quality documents (bilingual) [CONFIRMED bilingual requirement]
- **COA** issued per delivery/batch, in fa/en, referencing measured results vs spec.
- **[OPEN Q-045]** Which customers/products require a COA? What fields must it contain?

---

## 8. Assumptions & questions
A-005 inline QC · A-018 check points. Questions Q-039…Q-045 (+Q-016). Consolidated in [`open-questions.md`](./open-questions.md).
