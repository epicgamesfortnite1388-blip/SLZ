# Agent Skills — Maintenance Rules

## Purpose
Define how the project-specific agent skills in `skills/` are kept accurate over the life of the SLZ ERP, so they guide agents correctly without ever contradicting a newer confirmed business decision.

> **A skill must never silently override a newer confirmed business decision.**

## Scope
Applies to all files under `skills/` (`01-slz-domain` … `08-agent-workflow`, plus `skills/README.md`) and their relationship to the SLZ documentation and codebase.

## When Skills Must Be Updated
Update the affected skill(s) whenever any of the following happens:
- A decision-register entry (DR-xxx) moves to **CONFIRMED**, or a confirmed decision changes.
- The reconciled `docs/SLZ-SOURCE-OF-TRUTH.md` is created or amended.
- A business-review/workshop output changes a rule a skill encodes.
- A contradiction (C-xxx) is resolved, or a new one is discovered.
- A do-not-build-yet item is unblocked (its gate opens).
- The codebase foundation changes in a way a skill describes (base classes, transactions, events, error types, stack versions, conventions).
- A new domain area needs its own skill, or the Task → Required Skills mapping shifts.

## Who Updates
The agent (or engineer) making the underlying change owns the skill update in the **same change set**. Do not land a confirmed-decision, contradiction resolution, gate opening, or foundation change without updating the skills it affects. Reviewers check skill consistency as part of review.

## How Decisions Propagate
1. The decision lands in its authoritative source first (decision-register → CONFIRMED, or `SLZ-SOURCE-OF-TRUTH.md`).
2. The relevant skill's affected sections (Core Rules, Domain Concepts, Forbidden/Required Behaviors, Examples, Validation Checklist) are updated to match.
3. Cross-references are checked: `Related Documentation`, `Skill Dependencies`, the hierarchy in `08-agent-workflow`, and the mapping in `skills/README.md` stay consistent.
4. If the decision closes an `[OPEN]` item, remove the "keep configurable / do not build" guidance for it and replace it with the confirmed rule.

## Contradiction Handling
- Skills **describe** contradictions (referencing C-xxx); they do not resolve them.
- If a skill and a higher source disagree, the higher source wins per the `08-agent-workflow` hierarchy, and the skill is corrected.
- If two sources of equal-or-unclear authority disagree, record it in `docs/requirements/contradictions.md` and reference it from the skill — never resolve it silently inside a skill or in code.

## Staleness Marking
- When a skill statement depends on an item that is still `[OPEN]`/`[PROPOSAL]`/`[ASSUMPTION]`, the skill must say so and instruct agents to keep it configurable.
- When a source a skill cites changes but the skill has not yet been reconciled, mark the affected section with a visible `> [STALE: reason + source]` note until updated. Prefer updating immediately over marking.
- Periodically (and before major task waves) reconcile skills against the decision-register and `SLZ-SOURCE-OF-TRUTH.md`.

## Consistency Requirements
- The 9-level source-of-truth hierarchy is defined once in `08-agent-workflow` (mirroring `docs/SLZ-SOURCE-OF-TRUTH.md`) and referenced elsewhere; do not fork it.
- The mandatory-skills set (01, 02, 07, 08) and the Task → Required Skills mapping live in `skills/README.md`; keep them in sync with reality.
- Every skill keeps the fixed section template and an accurate `Skill Dependencies` section.
- No placeholder text (TODO/TBD/XXX/`<insert>`/`[your text]`), no invented SLZ facts, and correct doc references.

## Related Documentation
`skills/README.md` · `skills/08-agent-workflow/SKILL.md` · `docs/SLZ-SOURCE-OF-TRUTH.md` · `docs/reconciliation/slz-specific-rules.md` · `docs/reconciliation/master-data-impact.md` · `docs/requirements/decision-register.md` · `docs/requirements/contradictions.md` · `docs/requirements/do-not-build-yet.md`
