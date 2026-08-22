# SLZ ERP / MES — Business & Domain Analysis

**Company:** صنایع لفاف زرین (Sanaye Lafaf Zarrin — "SLZ"), a made-to-order (MTO) flexible-packaging manufacturer.
**Document set purpose:** Capture and validate the business domain *before* any ERP/MES module is built. This is a **discovery deliverable**, not an implementation. It will be reviewed by the SLZ business team before development starts.

> **Scope guard:** No production application code is produced in this task. No SLZ business rules are invented. Every statement that is not directly given by the task brief or by universal flexible-packaging industry practice is explicitly flagged for validation.

---

## 1. How to read these documents

Each statement is tagged so reviewers can separate fact from proposal:

| Tag | Meaning |
|-----|---------|
| **[CONFIRMED]** | Given explicitly in the task brief or the SLZ public capability list. Safe to build on. |
| **[ASSUMPTION]** | A reasonable industry-standard default proposed by the analyst. **Must be validated by SLZ** before implementation. |
| **[OPEN]** | An unknown with no safe default. **Requires a human answer** from SLZ personnel. Tracked in `open-questions.md`. |
| **[PROPOSAL]** | A design/architecture recommendation offered for review; alternatives are noted. |

Every **[ASSUMPTION]** and **[OPEN]** item carries an ID (e.g. `A-012`, `Q-007`) and is consolidated in [`open-questions.md`](./open-questions.md).

---

## 2. Document index

| # | File | Purpose |
|---|------|---------|
| 0 | [`README.md`](./README.md) | This index, glossary, conventions, tag legend. |
| 1 | [`business-processes.md`](./business-processes.md) | End-to-end order lifecycle, validation of the proposed flow, cross-functional workflows, state machines. |
| 2 | [`manufacturing-processes.md`](./manufacturing-processes.md) | Physical processes (blown film → cast → lamination → prepress → flexo → converting) and the production model. |
| 3 | [`product-model.md`](./product-model.md) | Versioned technical product specification. Why packaging is not a flat SKU. |
| 4 | [`bom-and-routing.md`](./bom-and-routing.md) | Multi-level BOM, BOM revisions, routing, operations, work centers. |
| 5 | [`costing-model.md`](./costing-model.md) | Proposed actual-cost model and cost-capture points. Formulas unvalidated. |
| 6 | [`quality-model.md`](./quality-model.md) | Quality checks, alerts, scrap, rework, non-conformance, COA. |
| 7 | [`inventory-model.md`](./inventory-model.md) | Warehouses, locations, lots, rolls, stock movements, reservations, traceability. |
| 8 | [`roles-and-permissions.md`](./roles-and-permissions.md) | Roles, RBAC, approval authorities, audit. |
| 9 | [`open-questions.md`](./open-questions.md) | Consolidated assumptions & unknowns requiring SLZ answers + the final consolidated model, ERD, architecture, risks, and recommended next task. |

---

## 2b. Task 002 — Validation & Requirements Baseline

These build on the Task 001 analysis above (originals unchanged). They form the boundary between what SLZ has decided and what the software team has proposed:

- [`../business-review/business-review-fa-en.md`](../business-review/business-review-fa-en.md) — bilingual FA/EN **business review** for the validation workshop (critical decisions, grouped assumptions, department checklists, exit criteria).
- [`../requirements/requirements-baseline.md`](../requirements/requirements-baseline.md) — **requirements baseline** (78 FR + 24 NFR), each traced to Task 001; unvalidated items marked `[BUSINESS VALIDATION REQUIRED]`.
- [`../requirements/decision-register.md`](../requirements/decision-register.md) — **decision register** of open technical & business decisions (nothing marked CONFIRMED without SLZ sign-off).
- [`../requirements/traceability.md`](../requirements/traceability.md) — **traceability matrix**: Question → Requirement → Entity → Workflow → Module.
- [`../requirements/contradictions.md`](../requirements/contradictions.md) — **contradictions** across the documents (not silently resolved).
- [`../requirements/do-not-build-yet.md`](../requirements/do-not-build-yet.md) — **do-not-build-yet** list guarding against premature implementation.

---

## 3. Company capability baseline [CONFIRMED]

From the task brief / public site, SLZ performs:

- **Film production:** Blown film, Cast film, Extrusion/Lamination
- **Prepress & color:** Color matching, Prepress
- **Printing:** Flexographic (flexo) printing
- **Finishing:** Lamination, Cold seal, Spot matte effects, Converting
- **Logistics:** Warehousing and delivery

**Product groups:** Cellulose & hygiene, Food packaging, Non-food packaging, General packaging, Shopping bags.

**Business character:** Made-to-order (engineer-to-order for new artwork/spec; make-to-order for repeat items). This is the single most important modeling driver: the "product" is a *customer-specific, versioned technical specification*, not a catalogue SKU.

---

## 4. Guiding design principles [CONFIRMED constraints from brief]

1. Do **not** build all ERP modules yet; model the manufacturing domain first.
2. Do **not** invent SLZ business rules; separate confirmed from assumed.
3. **Preserve history** — specifications, BOMs, artwork, prices are versioned and immutable once superseded.
4. **Auditability** — every state change is attributable (who/when/why) and append-only where it matters.
5. **Bilingual** — Persian (fa-IR, RTL) and English (en-US, LTR) throughout.
6. **Dual calendar** — Jalali (Shamsi) and Gregorian; store UTC + canonical date, render per user locale.
7. **Transactional integrity** — manufacturing stock/lot movements are atomic and fully traceable.
8. **No hard-coded machine logic** — machine behaviour is data-driven (parameters, capability profiles), not branched in code.
9. **Full + reverse traceability** — Supplier → RM lot → production batch → semi-finished → finished → delivery, and back.
10. **Manufacturing before accounting** — costing is modeled, but financial-ledger/accounting integration is deferred.

---

## 5. Bilingual glossary (key domain terms)

| English | فارسی (proposed) | Note |
|---------|------------------|------|
| Customer | مشتری | |
| Customer product | محصول مشتری | Customer-facing item identity |
| Product specification | مشخصات فنی محصول | Versioned |
| Artwork | طرح گرافیکی / آرت‌ورک | Versioned |
| Printing tooling (cylinder/plate/sleeve) | کلیشه / سیلندر چاپ | Flexo photopolymer plates / sleeves |
| Raw material | مواد اولیه | Resin, ink, adhesive, solvent, film |
| Raw material lot | بچ/لات مواد اولیه | Supplier lot for traceability |
| Roll | رول | Physical wound roll (WIP or FG) |
| Semi-finished product | محصول نیمه‌ساخته | Printed/laminated reel before converting |
| Finished product | محصول نهایی | |
| BOM | فهرست مواد (BOM) | Multi-level, versioned |
| Routing | مسیر تولید | Ordered operations |
| Operation | عملیات | A step on a work center |
| Work center | مرکز کاری | Logical grouping of machines |
| Machine | ماشین/دستگاه | |
| Production order | سفارش تولید | |
| Work order | دستور کار | Per-operation execution |
| Production batch | بچ تولید | Traceable output unit |
| Quality check | کنترل کیفیت | |
| Scrap / Rework | ضایعات / دوباره‌کاری | |
| Warehouse / Location | انبار / موقعیت | |
| Stock movement | گردش/حرکت موجودی | |
| Purchase request / order | درخواست خرید / سفارش خرید | |
| Supplier | تأمین‌کننده | |
| Delivery | تحویل / ارسال | |
| Maintenance order | دستور نگهداری و تعمیرات | |

> **[OPEN Q-001]** The Persian terms above are analyst proposals. SLZ must confirm the exact internal terminology (shop-floor vocabulary) so the UI matches how staff actually speak.

---

## 6. Status of this deliverable

This is **Task 001 — Discovery**. The recommended next implementation task is defined at the end of [`open-questions.md`](./open-questions.md). Nothing here should be treated as final until the business team signs off on the open questions.
