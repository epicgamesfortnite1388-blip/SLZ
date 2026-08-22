# SLZ ERP — Agent Skills

## Purpose
This directory holds the permanent, project-specific skills for the SLZ ERP (صنایع لفاف زرین / Sanaye Lafaf Zarrin), a made-to-order flexible-packaging manufacturer. Every coding agent working on this system reads the relevant skills **before** implementing, so the codebase reflects SLZ's real business — a versioned technical-spec product model, multi-stage physical manufacturing, lot/roll traceability, and inline quality — and never drifts into generic-ERP or Odoo-copied assumptions.

Each skill is a Markdown file under its own subdirectory and follows a fixed section template (Purpose, When to Read This Skill, Source of Truth, Core Rules, Domain Concepts, Required Behaviors, Forbidden Behaviors, Implementation Guidance, Examples, Common Mistakes, Validation Checklist, Related Documentation, Skill Dependencies).

## The Skills
- `01-slz-domain` — who SLZ is; the business reality agents must not reduce to a generic trading ERP.
- `02-erp-architecture` — modular monolith, foundation apps, layers, transactions, events, errors, permissions.
- `03-manufacturing-mes` — production as physical transformations, data-driven machines, genealogy.
- `04-packaging-engineering` — the versioned, multi-attribute product specification (not a flat SKU).
- `05-inventory-traceability` — lot/roll-tracked stock, append-only movements, forward/reverse genealogy.
- `06-quality` — inline QC per stage, versioned quality plans, NCR/QC_HOLD, recall linkage.
- `07-coding-standards` — the permanent engineering standard matching the `erp/` foundation.
- `08-agent-workflow` — how to work: read order, source-of-truth hierarchy, conflict handling, Odoo rule.

## Mandatory Skills
Read on **every** task, regardless of area:
- `01-slz-domain`
- `02-erp-architecture`
- `07-coding-standards`
- `08-agent-workflow`

## Task → Required Skills

| Task area | Read (in addition to the 4 mandatory) |
|---|---|
| Customer / product / specification / artwork / tooling | 04 |
| BOM & routing authoring | 04, 03 |
| Production orders, work orders, machines, shop-floor | 03, 04, 05 |
| Inventory, warehouses, lots, rolls, stock movements | 05 |
| Traceability / genealogy / recall design | 05, 03, 06 |
| Quality plans, checks, NCR, scrap, rework, COA | 06, 05, 03 |
| Costing (structure only; formulas are OPEN) | 03, 05, 06 |
| Foundation / platform apps (core, identity, audit, etc.) | (mandatory only) |
| API endpoints, serializers, permissions, migrations | (mandatory only) |
| Frontend UI, forms, i18n/RTL | (mandatory only) |

If a task spans areas, read the union.

## Source-of-Truth Hierarchy
Defined in `08-agent-workflow` and `docs/SLZ-SOURCE-OF-TRUTH.md`. Highest authority first:
1. `docs/reference/NEPTA_ERP_Feasibility_Study.md` — the official SLZ document.
2. `docs/requirements/*` — decision-register (DR-*), requirements baseline, contradictions, do-not-build-yet.
3. `docs/reconciliation/*` — SR-01..16 rules, domain model, master-data-impact (R-MD-*).
4. `docs/business-analysis/*` — Task 001 process/product/manufacturing models.
5. `docs/business-review/*` — Task 002 open-decision review.
6. `erp/` foundation code → these skills → generic ERP/Odoo knowledge (reference only, lowest).

Higher wins; **never silently resolve a conflict** — document it. Where a skill predates a CONFIRMED reconciliation decision, the decision wins and the skill must be updated.

> **RESOLVED — BUILD vs BUY (DR-000 / NQ-001).** The official study recommended Microsoft Dynamics 365 F&O; the SLZ business **considered and rejected** it → **custom build** (2026-08-21). The Django/DRF/React stack (DR-001/002/011) is **CONFIRMED** and Task 004+ domain implementation is **no longer gated on NQ-001** (NQ-002 remains open). Master Data (Task 004) holds only a **thin, classified product master**; rich spec/formulation/SKU-derivation/cliché belong to **Product Engineering (Task 005)** — see `docs/reconciliation/master-data-impact.md`.

## Ground Rules (from `08-agent-workflow`)
- Do not invent SLZ facts, terminology, or business rules.
- Keep `[OPEN]`/`[PROPOSAL]`/`[ASSUMPTION]` items configurable; honor the do-not-build-yet gates.
- Odoo is a conceptual/UX/feature reference only, never the source of an SLZ business rule.

## Maintenance
Skills are living documents. Update rules, ownership, decision propagation, contradiction handling, and staleness marking are defined in `docs/architecture/agent-skills.md`. A skill must never silently override a newer confirmed business decision.
