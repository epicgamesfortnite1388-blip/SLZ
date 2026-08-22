# Skill 04 — Packaging Product Engineering

## Purpose
Encode the SLZ-specific product model so agents never reduce a packaging product to `SKU + quantity`.

> A packaging product is a **customer-specific, multi-attribute, versioned technical specification** — not a flat catalogue item.

> **RECONCILED (Task 004A).** The official SLZ doc confirms and adds: product classification is **type → class → family (نوع/طبقه/خانواده) + product group** (SR-02 / DR-044 CONFIRMED) — a multi-level taxonomy, not a category field. The **SKU and dependent parameters (roll diameter/count, pallet count) are DERIVED by the system** from the customer's main parameters via a parameter-derivation/SKU-generation service (SR-01; formulas OPEN, NQ-005). **Cliché / printing tooling is a first-class asset** with per-use usage-life and a **dedicated cliché store** (SR-03). Spec fields explicitly include **MSDS/storage, ink/color formulation (main + alternative), targets (تارگت), per-packaging-level marking (مارکینگ), pallet spec**; revisions are **ECN-driven**. **Scope split:** in **Master Data (Task 004)** the Product is a *thin, classified master* (identity + taxonomy + UoM); the rich versioned spec, formulations, drawings, marking, SKU-derivation service, print-mounting calc, and cliché belong to **Product Engineering (Task 005)** — see `docs/reconciliation/master-data-impact.md` (R-MD-08/09/11/13). Do not bake engineering logic into the Task 004 product record. All gated on BUILD-vs-BUY (NQ-001).

## When to Read This Skill
Any work on customer products, specifications, revisions, artwork, tooling, BOM authoring inputs, sampling/first-article, or engineering changes.

## Source of Truth
- `docs/business-analysis/product-model.md` — the authoritative product model.
- `docs/business-analysis/bom-and-routing.md` — how spec drives BOM/routing.
- `docs/business-analysis/business-processes.md` §5.3/§5.4 — spec & artwork state machines.
- Requirements: FR-001..FR-013, FR-030..FR-039, FR-095.

## Core Rules
1. **Layered identity.** `Customer → Customer Product → Product Specification → Specification Revision`, then Revision → BOM revision + Routing + Artwork (revision) + Tooling. *These entity names are the analyst PROPOSAL in `product-model.md`; verify against docs before treating as final.*
2. **Every technical specification is versioned.** A revision is immutable once APPROVED/ACTIVE; the prior becomes SUPERSEDED (retained). State: `DRAFT → IN_REVIEW → APPROVED → ACTIVE → SUPERSEDED` (or `OBSOLETE`).
3. **Never overwrite a technical specification that has already been used in production. Create a new revision.** Older revisions are retained for traceability and re-order.
4. **Only ACTIVE revisions can be ordered against;** SUPERSEDED/OBSOLETE are kept for history and specific-revision re-orders.
5. **A production batch records the exact spec revision (and artwork revision) it was made to** — enabling reverse traceability and faithful re-orders (see contradiction C-005).
6. **Customer Product = durable identity** ("customer X's 1kg coffee pouch"), stable code across revisions; the specification carries the engineering definition.

## Domain Concepts
Why not `SKU + quantity`: a pouch hides dozens of engineering attributes that change independently — one layer or one Pantone differs and it is a different produced configuration. Costing, QC and traceability depend on the exact spec revision produced.

**Specification attribute groups (from `product-model.md`):**
- **Structure & material:** ordered **layers** (material + micron + function), e.g. `PET12 / ADH / AL7 / ADH / PE80`; substrate FKs to material master.
- **Dimensions & format:** width, length/roll length, gusset, bag type *(list OPEN Q-014/020)*, roll-stock vs finished bag.
- **Printing & color:** print process (flexo, surface/reverse), number of colors, ink (FK + coverage + system), color standard (Pantone + ΔE tolerance), artwork FK, print position/repeat.
- **Finishing & effects:** lamination (adhesive + coat weight g/m²), cold seal (pattern/coverage), matte/gloss, spot matte, special effects *(list OPEN Q-021)*.
- **Tolerances (cross-cutting):** attach to many attributes as `{value, unit, tol_low, tol_high / min / max}` — thickness ±, width ±, color ΔE, seal/bond strength min, registration ±, delivered qty ±%. Defaults are `[OPEN]` (Q-022).
- **Packaging & delivery spec:** primary/secondary pack, winding/core, labeling (bilingual, barcode/QR, lot marking), delivery unit.
- **Customer-specific specs:** typed custom attributes (key/value + datatype + unit + tolerance) so new requirements need no code change *(FR-007)*.

**Related lifecycles:** Artwork revision (`DRAFT → INTERNAL_REVIEW → CUSTOMER_REVIEW → APPROVED → ACTIVE → SUPERSEDED`) drives printing tooling (plates/cylinders/sleeves) + color recipe. Artwork may revise **independently** of the spec, linked by reference — but the exact artwork revision is recorded on each batch (C-005; recommendation, Q-025 OPEN). Tooling is its own object with its own procurement/approval lifecycle *(A-003; ownership OPEN Q-004/036)*.

**Sampling / first-article:** a sample/proof approval loop typically precedes bulk production for new products *(A-002; mandatory-when OPEN Q-003)*.

**Product groups** classify the customer product and drive defaults (e.g. food → migration/COA requirements).

## Required Behaviors
- Model identity, specification, and revision as separate layers.
- Represent structure as an ordered list of layers, not a single thickness field.
- Store attributes as typed, toleranced parameters; support custom attributes without code changes.
- Create a **new revision** for any change to a spec used in production; keep supersession history.
- Record spec revision **and** artwork revision on production batches.

## Forbidden Behaviors
- Do **not** model products as flat SKUs with price/stock fields.
- Do **not** mutate an ACTIVE/used specification in place.
- Do **not** hard-code tolerance defaults, bag-type lists, effect lists, or coding schemes — these are `[OPEN]`.
- Do **not** implement the spec-revision trigger rule, product coding scheme, sampling-mandatory rule, or tooling cost model while their gates are OPEN *(do-not-build-yet #13, #14, #15, #5)*.

## Implementation Guidance
Use `VersionedRoot` (Customer Product) + `Revision` (Specification Revision) from `apps/core/versioning.py`. Attributes → typed spec-parameter rows with unit + optional tolerance. Keep artwork and tooling as separate versioned/linked entities. Downstream (quotation, BOM, production) reference the **revision id**.

## Examples
- *Customer asks to darken a color.* New artwork revision; if structure/BOM unchanged, spec may stay ACTIVE but the batch records the new artwork revision. Confirm the trigger rule (Q-024/025) before automating.
- *Re-order of an old version.* Order against a specific SUPERSEDED spec revision — supported because history is retained.

## Common Mistakes
- One "thickness" field instead of per-layer structure.
- Editing an approved spec instead of revising it.
- Linking a batch only to the spec root, losing which revision/artwork was produced.
- Inventing a product numbering scheme (Q-019 OPEN).

## Validation Checklist
- [ ] Is the product a versioned spec, not a flat SKU?
- [ ] Is structure an ordered layer list with per-layer tolerance?
- [ ] Do changes create a new revision, never overwrite a used one?
- [ ] Do batches capture spec revision AND artwork revision?
- [ ] Are OPEN items (tolerances, coding, sampling, tooling cost) left configurable/unbuilt?

## Related Documentation
`docs/reference/NEPTA_ERP_Feasibility_Study.md` · `docs/reconciliation/slz-specific-rules.md` (SR-01/02/03) · `docs/reconciliation/master-data-impact.md` (R-MD-08/09/11/13) · `docs/business-analysis/product-model.md` · `docs/business-analysis/bom-and-routing.md` · `docs/architecture/versioning.md` · `docs/requirements/contradictions.md` (C-005)

## Skill Dependencies
Packaging Engineering depends on: `01-slz-domain`, `02-erp-architecture`, `07-coding-standards`, `08-agent-workflow`. Consumed by `03-manufacturing-mes` and `05-inventory-traceability`.

## Implementation Status (Task 005 — 2026-08-21)
The specification **spine** is implemented in `apps/engineering` — `CustomerProduct` (versioned root, manual code), `SpecificationRevision` (draft → activate → supersede, immutable once non-DRAFT), ordered `SpecLayer`, ink `SpecColor` (ink must be `INK`-subtype material), and typed `SpecParameter`. Lifecycle is in the service layer under `atomic_with_events`; all writes are audited. See `docs/architecture/product-engineering.md`.

Still `[OPEN]` and intentionally **not** built: spec-revision trigger/approver rule (Q-024/025, #13), SKU/product coding scheme (Q-019, #14), default tolerances (Q-022), canonical bag-type list (Q-014/020 — kept free-text), sampling-mandatory rule (#15), tooling/cliché cost model (#5), and Artwork/Tooling as separate linked lifecycles.
