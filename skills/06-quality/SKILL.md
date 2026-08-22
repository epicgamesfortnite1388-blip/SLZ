# Skill 06 — Quality

## Purpose
Ensure agents build quality as an inline part of the manufacturing workflow, integrated with traceability, and configurable per product/stage.

> **Quality is part of the manufacturing workflow, not only a final inspection step.**

> **RECONCILED (Task 004A).** The official SLZ doc confirms and sharpens: **inline QC can automatically stop a work order and spawn a rework work order** (SR-06) — QC is an active control that gates production, not a passive record; model the WO auto-stop + linked rework-WO creation as a QC-driven transition (do not build the automation while gated, but design for it). **Goods receipt is two-stage: temporary → QC → definitive**, so incoming QC is the **gate** that promotes a temporary receipt to definitive stock, keyed on a **QC pass threshold** (SR-09) — coordinate with `05-inventory-traceability`. **Rework produces sellable output and scrap recycles into regrind lots** (closed-loop, Tehran only — SR-07): rework and scrap dispositions have downstream inventory/costing effects, not just a status. QC is **site-scoped** (multi-company, DR-040). All gated on BUILD-vs-BUY (NQ-001).

## When to Read This Skill
Any work on quality plans, checks, characteristics, tolerances, inspection (incoming/inline/final), NCR/alerts, quarantine, release, scrap, rework, corrective action, COA, or recall.

## Source of Truth
- `docs/business-analysis/quality-model.md` — quality entities, checkpoints, NCR lifecycle.
- `docs/business-analysis/manufacturing-processes.md` §2 — where checks happen.
- Requirements: FR-070..FR-076.

## Core Rules
1. **Checks occur at multiple stages**, not only final: incoming (RM), after extrusion, after printing, after lamination, after slitting, final/converting, pre-ship *(A-005/A-018; exact points OPEN Q-039)*.
2. **Quality plans are configurable and versioned.** Do **not** assume every product uses the same checklist. A Quality Plan defines characteristics + methods + spec limits per operation/material *(FR-070)*.
3. **Spec limits come from the product specification revision's tolerances** — quality is bound to the produced spec.
4. **Quality results are immutable** once recorded; corrections create a new record (audit) *(FR-071)*.
5. **A failed check raises an NCR/Quality Alert and can place the batch/roll on QC_HOLD**, blocking consumption/shipment until disposition *(FR-073/074)*.
6. **Quality links to genealogy** so a failed characteristic traces forward (affected deliveries) and backward (RM lot/machine/operator/shift) — enabling recall/mock-recall.

## Domain Concepts
**Entities:** Quality Check (single measurement event tied to incoming lot / work order / batch / roll) · Quality Plan / Inspection Plan (versioned) · Quality Characteristic (thickness, ΔE, bond/seal strength, COF, dimensions… + method + spec limits) · Quality Alert / NCR · Scrap record · Rework record · COA (bilingual certificate).

**Check result model:** ref + characteristic (with spec limits from spec revision) + method/instrument + measured value(s) + result `PASS | FAIL | CONDITIONAL` + inspector + timestamp (UTC + Jalali/Gregorian); on FAIL → raises NCR.

**NCR lifecycle:** `OPEN → UNDER_REVIEW → DISPOSITION → CLOSED`; disposition ∈ `{ ACCEPT_AS_IS (concession), REWORK, SCRAP, RETURN_TO_SUPPLIER, DOWNGRADE }`.

**Scrap:** reason-coded per stage; removes qty via a scrap-issue stock movement; carries accumulated cost. **Rework:** traced re-pass through an operation, genealogy preserved, adds cost.

## Required Behaviors
- Attach checks to the correct object (incoming lot / work order / batch / roll) and to the spec revision's limits.
- Make inspection plans, characteristics, methods and sampling rules **data-driven and per-product/stage**.
- Raise NCR and set QC_HOLD on failure; block downstream consumption/shipment until disposition.
- Preserve genealogy links from every check for traceability.
- Render COA bilingually where required.

## Forbidden Behaviors
- Do **not** model a single terminal QC gate (contradiction C-001 — inline QC per stage + final).
- Do **not** hard-code inspection plans, characteristics, tolerances, sampling rules (AQL vs 100%), scrap reason codes, or rework-vs-scrap rules — these are `[OPEN]` (Q-039..Q-043, do-not-build-yet #11, #12).
- Do **not** assume one shared checklist for all products.
- Do **not** allow consumption/shipment of QC_HOLD material.
- Do **not** build formal recall/CAPA/8D workflow yet — design to allow it *(Q-041, Q-044; do-not-build-yet #31)*.

## Implementation Guidance
Model Quality Plan/Characteristic as versioned configurable data (`VersionedRoot`/`Revision`); pull spec limits from the product spec revision. Quality checks are append-only, authored records. QC_HOLD is a state on the batch/roll that inventory/manufacturing services must honor before issue/ship. Keep NCR disposition as data-driven states, not hard-coded branches.

## Examples
- *Color check after printing.* Characteristic ΔE with limit from the spec revision; FAIL → NCR + QC_HOLD on the printed roll → disposition (rework/scrap/concession). Lamination cannot consume the roll while held.
- *Two products, different checks.* Each has its own quality plan; do not apply product A's checklist to product B.

## Common Mistakes
- Putting a single QC step at the end of production.
- Hard-coding tolerance values instead of reading spec-revision limits.
- Letting held material flow downstream.
- Treating rework as untracked (must preserve genealogy + cost).

## Validation Checklist
- [ ] Are checks attachable at multiple stages, not only final?
- [ ] Are quality plans versioned and per-product configurable?
- [ ] Do spec limits come from the spec revision, not constants?
- [ ] Does QC_HOLD block consumption/shipment?
- [ ] Do checks link to genealogy for recall?
- [ ] Did I avoid hard-coding OPEN inspection/sampling/scrap rules?

## Related Documentation
`docs/reference/NEPTA_ERP_Feasibility_Study.md` · `docs/reconciliation/slz-specific-rules.md` (SR-06/07/09) · `docs/business-analysis/quality-model.md` · `docs/business-analysis/manufacturing-processes.md` · `docs/requirements/contradictions.md` (C-001)

## Skill Dependencies
Quality depends on: `01-slz-domain`, `02-erp-architecture`, `03-manufacturing-mes`, `05-inventory-traceability`, `07-coding-standards`, `08-agent-workflow`. Draws tolerances from `04-packaging-engineering`.
