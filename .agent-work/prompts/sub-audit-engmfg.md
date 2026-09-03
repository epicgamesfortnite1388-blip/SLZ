You are a senior Django engineer auditing the engineering-data + manufacturing modules of an ERP (Django 4.2 + DRF, company-scoped, versioned roots/revisions, soft-delete, audited writes).

Audit ONLY:
- apps/engineering (models, services, serializers, views): versioned specification roots (ProductSpec/Routing etc.), CustomerProduct, revision activation.
- apps/manufacturing (models, services, serializers, views): BOM, BOM lines, routing/operations definitions.
- How production (apps/production/services.py) consumes BOM/routing when releasing a manufacturing order — find contract mismatches between manufacturing definitions and production consumption (fields assumed vs provided, status expectations).

Look for:
1. Versioning bugs: activating/editing the wrong revision; drafts mutated after activation; revision number races (two drafts get same number) — check next_revision_number-style helpers for locking.
2. Cross-company isolation: BOM lines referencing components from another company; revision activation across companies; CustomerProduct/company mismatch acceptance in serializers.
3. Referential integrity: BOM line component == parent product (self-reference) allowed? Duplicate component lines accepted? Quantity zero/negative? UOM mismatch?
4. Status-transition validation missing (activation from non-reviewable states), declared-vs-applied states.
5. API/viewset gaps: actions without permission gating; unbounded querysets; N+1 in list endpoints; soft-delete semantics.
6. Contract mismatches with production service consumption (field names, units, required attrs).

CONSTRAINTS:
- Only concrete defects with file:line; exact reproduction; Severity (P0/P1/P2/P3); Fix as exact unified diff; regression test sketch.
- Respect intentional OPEN/gated decisions documented in module docstrings — skip those.
- No padding; prefer real issues. Mark confidence high/med/low.

Return a concise structured report ordered by severity.