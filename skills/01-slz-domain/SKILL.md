# Skill 01 — SLZ Domain

## Purpose
Give every coding agent the business reality of **صنایع لفاف زرین (Sanaye Lafaf Zarrin — "SLZ")** before they touch code, so no one models this system as a generic trading/catalogue ERP.

> **SLZ is not a generic trading ERP. The system is primarily a made-to-order flexible-packaging manufacturing system (MES) with ERP capabilities built around it.**

> **RECONCILED (Task 004A, 2026-08-21).** The official SLZ study `docs/reference/NEPTA_ERP_Feasibility_Study.md` is now the top source of truth. It establishes: (1) SLZ is one company in the **NEPTA 6-company holding** — phase-1 ERP covers **SLZ (Tehran) + Helena (Saveh)**, so the system is **multi-company/multi-site** (DR-040 CONFIRMED); (2) **16 SLZ-specific rules SR-01..SR-16** (`docs/reconciliation/slz-specific-rules.md`) that generic ERP would get wrong — read them before building domain behavior; (3) the study *recommended buying Microsoft Dynamics 365 F&O*, but the SLZ business **considered and rejected** that option: **BUILD vs BUY is RESOLVED → custom build** (DR-000 CONFIRMED, NQ-001 REJECTED, 2026-08-21). The custom Django/DRF/React stack is the confirmed direction; domain implementation (Task 004+) is **no longer gated on NQ-001**. Only NQ-002 (exact company/site list) and parametric business decisions remain open.

## When to Read This Skill
Read this **first**, on every task. It is a mandatory skill (see `skills/README.md`). Any work on products, orders, production, inventory, quality, or costing assumes the model described here.

## Source of Truth
Primary business documents (read the ones relevant to your task):
- `docs/reference/NEPTA_ERP_Feasibility_Study.md` — **the official SLZ document; highest authority.**
- `docs/reconciliation/slz-specific-rules.md` — the 16 SLZ-specific rules (SR-01..SR-16). Read before domain work.
- `docs/reconciliation/slz-domain-model.md` — the real entities extracted from the official doc.
- `docs/SLZ-SOURCE-OF-TRUTH.md` — top-level pointer, information hierarchy, confirmed facts, and gating decisions.
- `docs/business-analysis/README.md` — company baseline, tag legend, glossary (Task 001; valid where not overridden).
- `docs/business-analysis/business-processes.md` — order-to-cash & manufacturing lifecycle (Task 001).
- `docs/business-analysis/product-model.md` — the versioned product spec model (Task 001).
- `docs/business-analysis/manufacturing-processes.md` — the physical process chain (Task 001).
- `docs/business-review/business-review-fa-en.md` — the 15 highest-impact open decisions (Task 002).

Follow the source-of-truth hierarchy in `skills/README.md` and `skills/08-agent-workflow/SKILL.md`.

## Core Rules
1. **Made-to-order, not stock catalogue.** New products are *engineer-to-order* (new artwork/spec/tooling); repeats are *make-to-order* against an already-approved spec revision. These are two different order paths *(A-001, Q-002)*.
2. **A "product" is a customer-specific, versioned technical specification — never a flat SKU.** See `skills/04-packaging-engineering`.
3. **Production is a multi-stage physical transformation chain**, not a status change. See `skills/03-manufacturing-mes`.
4. **Preserve history.** Specs, BOMs, artwork, routings, quotations and prices are versioned; superseding never deletes *(constraint #4)*.
5. **Full forward + reverse traceability** from supplier lot to customer delivery and back *(constraint #9)*.
6. **Bilingual (fa-IR RTL primary / en-US LTR) and dual-calendar (Jalali + Gregorian).** Persian is the primary language *(constraints #6, #7)*. **Sanction/FX awareness** is a real constraint *(NFR-022)*.
7. **Multi-company / multi-site is real, not optional** *(SR-16/DR-040 CONFIRMED)*. SLZ+Helena; capability and capacity are **site-scoped** *(SR-15/DR-041)*. Scope master data by company/site.
8. **Follow SR-01..SR-16** — when a generic ERP convention conflicts with an SR rule, the SR rule wins.
9. **BUILD vs BUY is RESOLVED → custom build** *(DR-000 CONFIRMED / NQ-001 REJECTED, 2026-08-21)*. The official study recommended Microsoft Dynamics 365 F&O; the SLZ business considered and **rejected** it in favor of a custom system fitted to SLZ's actual operations. The custom Django/DRF/React stack (DR-001/002/011) is the confirmed direction — Task 004+ domain implementation is **not** gated on NQ-001. NQ-002 (exact company/site list) remains open.
10. **Most parametric business specifics are still OPEN.** The document gives requirements, not numbers; nearly every threshold/formula/tolerance remains `[OPEN]`. Do not treat proposals as confirmed. Check `skills/README.md` hierarchy and `docs/requirements/do-not-build-yet.md`.

## Domain Concepts

**Organization (CONFIRMED, Task 004A):** SLZ = **صنایع لفاف زرین (Zarrin Laff Industries)**, a founding member of the **NEPTA holding (6 companies)**. Phase-1 ERP = **SLZ (site: Tehran) + Helena (site: Saveh)** (DR-040). Company and Site are first-class; **most master data, RBAC, warehouses, capacity and work orders are company/site-scoped**. Sister-company **outsourcing** of operations is real intercompany activity (SR-14/SR-16).

**What SLZ does (confirmed capability baseline) — capability is SITE-SPECIFIC (SR-15/DR-041):**
- **Tehran (SLZ):** blown film, cast film, extrusion/lamination, prepress & color matching, flexo printing, lamination, cold seal, spot matte, converting, **recycling/grinding (→ regrind)**, cutting/sewing, warehousing/logistics.
- **Saveh (Helena):** blown film + cutting/sewing **only**.
- A site declares its **capability set**; feasibility and routing must respect it. Do not assume every site can run every stage.

**Product groups:** cellulose & hygiene · food packaging · non-food packaging · general packaging · shopping bags. Product groups also structure **sales lines** and CRM.

**Product identity (SR-01/SR-02, DR-044 CONFIRMED):** classification is multi-level **type → class → family (نوع/طبقه/خانواده) + product group** — not a flat category. The **SKU and dependent parameters (roll diameter/count, pallet count) are DERIVED by the system** from the customer's main parameters, not manually entered. Rich spec/formulation/SKU logic belongs to Product Engineering (Task 005), not Master Data (Task 004). See `skills/04-packaging-engineering`.

**Production chain (routing selects which stages apply; subject to site capability):**
`Film forming (blown/cast) → Prepress → Flexo printing → Lamination → (Curing) → Slitting/Rewinding → Converting/Bag-making → Inspection/Packing → Finished goods`.

**SLZ-specific rules (SR-01..SR-16)** — the mechanics generic ERP gets wrong. Highlights: SKU derived (SR-01); layered taxonomy (SR-02); cliché tooling is a first-class asset with usage-life + dedicated store (SR-03); material is subtyped incl. ink/solvent/regrind (SR-04/DR-042 CONFIRMED); capacity/machine-settings/allowed-scrap/allowed-downtime are data-driven tables keyed by machine×product×site (SR-05); inline QC can auto-stop a WO and spawn a rework WO (SR-06); rework produces sellable output and scrap recycles to regrind (SR-07, Tehran); roll/lot genealogy (SR-08); two-stage goods receipt temporary→QC→definitive (SR-09); unlimited warehouses with special store types + per-user access + consumption permit + rial+qty kardex (SR-10); per-packaging-level marking (SR-11); ATP-style delivery estimation (SR-12); margin-based order priority (SR-13); outsourceable operations (SR-14); site-specific capability (SR-15); multi-company holding (SR-16). Read `docs/reconciliation/slz-specific-rules.md`.

**Order lifecycle (proposed, under review):**
`Inquiry → Technical requirements → Product specification → Quotation → Customer approval → Sales order → Artwork/tooling → Sample/first-article → BOM → Routing → Planning/MRP → Purchasing/reservation → Multi-stage production → Inline + final QC → Finished goods → Delivery → Continuous costing → Profitability`. Repeat orders skip spec/artwork/tooling/BOM/routing authoring.

**Major departments (real units per the official doc; full RBAC still open — Q-053):** R&D, Edit (printed-artwork editing), Planning, Production Control, Production, QC, Warehouse, Procurement, Finance, HR, Technical/Maintenance, and **sales lines by product group**.

**Key terminology (bilingual glossary — analyst proposals, Q-001, confirm with staff):**
Customer product (محصول مشتری) · Product specification (مشخصات فنی محصول) · Artwork (آرت‌ورک) · Printing tooling / cylinder / plate (کلیشه/سیلندر) · Raw material (مواد اولیه) · Raw material lot (لات مواد اولیه) · Roll (رول) · Semi-finished product (نیمه‌ساخته) · Finished product (محصول نهایی) · BOM (فهرست مواد) · Routing (مسیر تولید) · Operation (عملیات) · Work center (مرکز کاری) · Machine (ماشین) · Production order (سفارش تولید) · Work order (دستور کار) · Production batch (بچ تولید) · Quality check (کنترل کیفیت) · Scrap/Rework (ضایعات/دوباره‌کاری) · Warehouse/Location (انبار/موقعیت) · Stock movement (گردش موجودی) · Supplier (تأمین‌کننده) · Delivery (تحویل).

## Required Behaviors
- Frame every feature in terms of "which customer product / spec revision / production stage / lot does this touch?"
- Preserve the distinction between **new-product** and **repeat-order** paths.
- Keep costing continuous (captured during production), not a single end step.
- Treat quality as inline across stages, not only a final gate.
- Use the exact tag (`[CONFIRMED] / [ASSUMPTION] / [OPEN] / [PROPOSAL]`) from the docs when reasoning about whether a rule is safe to build.

## Forbidden Behaviors
- Do **not** model products as `SKU + quantity`.
- Do **not** invent SLZ business facts, terminology, machine lists, tolerances, scrap %, or rates. If it is not in the docs, it is `[OPEN]`.
- Do **not** collapse the multi-stage chain into a single "production" step.
- Do **not** implement any rule listed in `docs/requirements/do-not-build-yet.md` while its gate is OPEN.
- Do **not** assume "Odoo does X, so SLZ does X." Ask: does SLZ actually need this? (see `skills/README.md`).

## Implementation Guidance
This skill is orientation, not schema. When you build, combine it with the domain-specific skill (packaging, manufacturing, inventory, quality) plus `02-erp-architecture`, `07-coding-standards`, `08-agent-workflow`. Encode confirmed principles as structure; leave OPEN specifics configurable, never hard-coded.

## Examples
- *"Add a product catalogue with name, price, stock level."* → **Wrong framing.** SLZ products are customer-specific versioned specs; there is no flat price/stock on the product. Redirect to `04-packaging-engineering`.
- *"Mark the order 'produced'."* → Production is stage-level production orders with material consumption, output batches, QC and genealogy — not a status flip. See `03-manufacturing-mes`.
- *"What's the default scrap %?"* → It is `[OPEN]` (Q-016/042). Build the field configurable; do not hard-code a number.

## Common Mistakes
- Treating the proposed order flow as confirmed (it is explicitly "proposed, not correct").
- Hard-coding Persian labels or assuming LTR layout.
- Assuming one QC step, one costing step, one BOM level.
- Confusing customer product code with an internal product code (coding scheme is OPEN — Q-019).

## Validation Checklist
- [ ] Does my design keep product = customer-specific versioned spec?
- [ ] Have I preserved new-vs-repeat order paths?
- [ ] Is every non-confirmed business number/rule configurable rather than hard-coded?
- [ ] Did I check the term against the glossary instead of inventing one?
- [ ] Did I confirm no `do-not-build-yet` gate blocks this work?

## Related Documentation
`docs/reference/NEPTA_ERP_Feasibility_Study.md` · `docs/SLZ-SOURCE-OF-TRUTH.md` · `docs/reconciliation/*` (esp. `slz-specific-rules.md`, `slz-domain-model.md`, `master-data-impact.md`) · `docs/business-analysis/*` · `docs/business-review/business-review-fa-en.md` · `docs/requirements/*`

## Skill Dependencies
This is the foundational domain skill. Every other skill depends on it. Read alongside `02-erp-architecture`, `07-coding-standards`, `08-agent-workflow` on every task.
