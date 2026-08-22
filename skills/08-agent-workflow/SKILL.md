# Skill 08 — Agent Workflow

## Purpose
Define how every agent works on the SLZ ERP: what to read, in what order, how to resolve conflicting sources, and what never to assume. This skill governs process; the domain skills govern content.

## When to Read This Skill
Mandatory at the start of every task, before touching docs or code.

## Source of Truth
- This file (process rules) + `docs/architecture/agent-skills.md` (skill maintenance).
- `docs/SLZ-SOURCE-OF-TRUTH.md` — the top-level pointer; its hierarchy is authoritative and is mirrored below.
- The hierarchy below resolves *content* authority.

## Core Rules
1. Read the mandatory skills (01, 02, 07, 08) plus the task-mapped skills before touching code.
2. **Read `docs/reconciliation/slz-specific-rules.md` (SR-01..SR-16) before writing any domain behavior** — these are the SLZ mechanics generic ERP gets wrong.
3. Ground every business claim in a cited source from the hierarchy below — not memory, not Odoo.
4. Higher source wins on conflict, but **never silently resolve** one; document it.
5. Keep `[OPEN]`/`[PROPOSAL]`/`[ASSUMPTION]` items configurable; honor do-not-build-yet gates.
6. Never invent SLZ facts, terminology, or business rules.
7. **BUILD vs BUY is RESOLVED → custom build** (DR-000 CONFIRMED / NQ-001 REJECTED, 2026-08-21). Domain implementation (Task 004+) is **no longer gated on NQ-001**; only NQ-002 (exact company/site list) and parametric business decisions remain open — see the note below.

> **RESOLVED GATE — BUILD vs BUY (DR-000 / NQ-001).** The official SLZ study (`docs/reference/NEPTA_ERP_Feasibility_Study.md`) recommended buying Microsoft Dynamics 365 F&O; the SLZ business **considered and rejected** that in favor of a custom system fitted to SLZ's actual operations. **Decision: custom build** (2026-08-21). The stack decisions (DR-001 Django, DR-002 PostgreSQL, DR-011 React) are **CONFIRMED**. Task 004 (Master Data) is authorized and implemented. Still open: NQ-002 (exact company/site list beyond SLZ + Helena) and parametric business rules — keep those configurable, do not hard-code.

## Domain Concepts

### The Source-of-Truth Hierarchy
Mirrors `docs/SLZ-SOURCE-OF-TRUTH.md`. When two sources disagree, higher wins — but **never silently resolve a conflict**; document it (see Conflict Handling).

1. **Official SLZ documentation** — `docs/reference/NEPTA_ERP_Feasibility_Study.md` (NEPTA.ERP.SLC.FZS V1.5). Organizational facts and domain requirements from the business itself.
2. **Reconciled requirements & decisions** — `docs/requirements/*` (baseline, decision-register incl. DR-000/DR-040..044, changelog, contradictions, traceability). DR marked **CONFIRMED** = SLZ-established fact.
3. **Reconciliation analysis** — `docs/reconciliation/*` (interprets the official doc against prior work; SR-01..SR-16, domain model, master-data impact).
4. **Task 001 business analysis** — `docs/business-analysis/*` (earlier discovery; valid where not overridden above; mostly `[ASSUMPTION]`/`[PROPOSAL]`).
5. **Task 002 business review** — `docs/business-review/*`.
6. `docs/architecture/*` — technical conventions (authoritative for platform *mechanisms*; build-vs-buy is resolved → custom build).
7. `erp/` code — the running implementation (authoritative for *how* it is built, not *what business rule* applies).
8. These skills — condensed guidance derived from 1–7.
9. **Generic ERP / industry knowledge & Odoo** — **reference only**, lowest authority; only fills gaps and never overrides a confirmed SLZ rule.

### The Task Sequence
`READ → UNDERSTAND → SEARCH → PLAN → CONFIRM-OPEN → IMPLEMENT → TEST → VALIDATE → DOCUMENT`
1. **READ** the mandatory skills (01, 02, 07, 08) + the skills mapped to the task + `slz-specific-rules.md`.
2. **UNDERSTAND** the SLZ reality behind the request; identify the real domain objects and any governing SR rule.
3. **SEARCH** the codebase for existing patterns/apps/base classes to reuse.
4. **PLAN** the change against existing conventions; mirror an existing app.
5. **CONFIRM-OPEN**: build-vs-buy (NQ-001) is resolved (custom build); still check NQ-002, then `decision-register`, `contradictions`, `do-not-build-yet`, `master-data-impact.md` — is any dependency `[OPEN]` or gated?
6. **IMPLEMENT** in the service layer, reusing foundation bases.
7. **TEST** (unit/integration/API/permission/domain).
8. **VALIDATE** against the relevant skills' checklists; run formatters/linters/tests.
9. **DOCUMENT** decisions, assumptions, and any new conflict discovered.

### Pre-Implementation Checklist
1. Read mandatory + mapped skills, plus `docs/reconciliation/slz-specific-rules.md`.
2. Located the authoritative source(s) for this feature (highest applicable hierarchy level).
3. Build-vs-buy (NQ-001) is resolved (custom build); confirmed NQ-002 does not block this work and no dependency is `[OPEN]` or on the do-not-build-yet list.
4. Checked whether an SR-01..SR-16 rule governs this behavior (SLZ reality over generic default).
5. Searched for and will reuse existing patterns/base classes.
6. Business logic planned for services, not views/serializers/components.
7. Company/site scoping considered (master data is company/site-scoped — DR-040).
8. Auditing/versioning/events accounted for.
9. Permissions (`module.resource.action`) identified.
10. Bilingual + Jalali + Decimal + UUID + UTC concerns handled.
11. OPEN business values kept configurable, not hard-coded; no conflict left silently resolved.

## Required Behaviors
- Ground every business claim in a cited source (hierarchy above), not memory or Odoo.
- Check SR-01..SR-16 before implementing domain mechanics; the SLZ rule beats the generic default.
- Keep `[OPEN]`/`[PROPOSAL]`/`[ASSUMPTION]` items configurable; honor do-not-build-yet gates and the NQ-002 gate (build-vs-buy/NQ-001 is resolved).
- Surface conflicts explicitly in your output and in `contradictions.md`.

## Forbidden Behaviors
- Do **not** invent SLZ facts, terminology, machines, tolerances, or business rules.
- Do **not** silently resolve conflicting sources or override a newer confirmed decision.
- Do **not** build gated/OPEN-dependent logic.
- Do **not** reason "Odoo does X, therefore SLZ does X." Odoo is a conceptual/UX/feature reference only — never the source of an SLZ business rule.
- Do **not** treat analyst `[ASSUMPTION]`/`[PROPOSAL]` content as confirmed.

## Implementation Guidance
Start from the mapped skills (see `skills/README.md`). If a needed decision is OPEN, implement the stable structure and leave the decision as configuration with a documented note, rather than picking a value. When code and a business doc disagree on a *rule*, the doc hierarchy wins and the code is suspect; when they disagree on *how it is built*, the code wins.

## Examples
- *Task references a scrap %.* It is `[OPEN]` (Q-042) and governed by SR-05 (allowed-scrap is a data-driven table keyed by machine×product×site) → model it as configurable data, do not hard-code, note the assumption.
- *Doc says inline QC, an older note implies terminal QC.* That is C-001 → follow the higher source (inline; SR-06 even lets QC auto-stop a WO), reference the contradiction, do not quietly choose.
- *Asked to build the Master Data module.* Build-vs-buy (NQ-001) is resolved → custom build; NQ-002 does not block master-data identity/classification. Task 004 is authorized — implement the smallest correct scope, keep OPEN parametric values configurable, and defer gated payload (specs, BOM, formulations) to later tasks.

## Common Mistakes
- Coding from generic ERP intuition or Odoo behavior instead of SLZ sources (ignoring SR-01..SR-16).
- Reopening the build-vs-buy question: it is **RESOLVED → custom build** (DR-000 CONFIRMED / NQ-001 REJECTED). Treat the Django/DRF/React stack as settled.
- Treating a `[PROPOSAL]` as CONFIRMED.
- Hard-coding an OPEN value to "make it work."
- Resolving a contradiction in code without recording it.

## Validation Checklist
- [ ] Did I read the mandatory + mapped skills and `slz-specific-rules.md`?
- [ ] Is every business rule traced to a source in the hierarchy?
- [ ] Did I respect the NQ-002 gate (build-vs-buy/NQ-001 is resolved → custom build)?
- [ ] Are OPEN/gated items left configurable/unbuilt?
- [ ] Did I avoid inventing facts and avoid Odoo-as-authority?
- [ ] Are any discovered conflicts documented, not silently resolved?

## Related Documentation
`docs/SLZ-SOURCE-OF-TRUTH.md` · `docs/reference/NEPTA_ERP_Feasibility_Study.md` · `docs/reconciliation/*` (esp. `slz-specific-rules.md`, `master-data-impact.md`) · `docs/requirements/decision-register.md` · `docs/requirements/contradictions.md` · `docs/requirements/do-not-build-yet.md` · `docs/architecture/agent-skills.md` · `skills/README.md`

## Skill Dependencies
Governs process for all skills. Mandatory (with `01`, `02`, `07`) on every task.
