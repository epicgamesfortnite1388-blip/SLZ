# SLZ — SOURCE OF TRUTH

**IMPORTANT: This project is a custom ERP for SLZ. Do not infer business rules from generic ERP systems. Read this document and the linked business-analysis/requirements documentation before implementing domain behavior. When generic ERP conventions conflict with confirmed SLZ requirements, SLZ requirements take precedence.**

---

## What this document is

This is the top-level pointer for any agent or developer about to implement domain behavior in the SLZ ERP. It defines the **information hierarchy**, links the authoritative sources, and lists the confirmed facts and the critical open decisions that gate implementation.

SLZ = **صنایع لفاف زرین** (Zarrin Laff Industries), a made-to-order flexible-packaging manufacturer and founding member of the **NEPTA** holding group.

## Information hierarchy (highest wins)

1. **Official SLZ documentation** — `docs/reference/NEPTA_ERP_Feasibility_Study.md` (NEPTA.ERP.SLC.FZS V1.5). Organizational facts and domain requirements from the business itself.
2. **Reconciled requirements & decisions** — `docs/requirements/` (baseline, decision-register, changelog, contradictions, traceability) as updated by reconciliation.
3. **Reconciliation analysis** — `docs/reconciliation/` (this task's output; interprets the official doc against prior work).
4. **Task 001 business analysis** — `docs/business-analysis/` (our earlier discovery; valid where not overridden above).
5. **Task 002 business review** — `docs/business-review/`.
6. **Generic ERP conventions** — lowest priority; only fill gaps the sources leave, and never override a confirmed SLZ rule.

When two sources conflict, the higher one wins, and the conflict is recorded (not silently resolved) in `docs/requirements/contradictions.md` or the reconciliation files.

## Read these before coding domain behavior

- `docs/PROJECT-STATUS.md` — **consolidated progress, milestones, module status matrix, and the prioritized list of what remains (with gates).** Read this to see current state at a glance.
- `docs/reconciliation/slz-specific-rules.md` — **the 16 SLZ-specific rules (SR-01..SR-16)** that generic ERP would get wrong. Read this first.
- `docs/reconciliation/slz-domain-model.md` — the real entities, their fields, lifecycle, versioning, and scope.
- `docs/reconciliation/slz-actual-workflow.md` — the real order-to-delivery flow.
- `docs/reconciliation/current-to-future-system.md` — current process → business rule → ERP model → workflow map, with phase ordering.
- `docs/reconciliation/master-data-impact.md` — how the master-data model must be reshaped (Task 004).
- `docs/reconciliation/slz-system-vs-task001.md` and `slz-system-vs-requirements.md` — the classified evidence tables.
- `docs/requirements/requirements-changelog.md` — what changed and why.

## Confirmed business facts (do not re-litigate)

- **Multi-company holding:** SLZ is one of six NEPTA companies; **phase-1 ERP = SLZ (Tehran) + Helena (Saveh)**. (DR-040)
- **Site-specific capability:** Tehran = blown/cast film, printing, lamination, recycling/grinding, cutting/sewing; Helena/Saveh = blown film + cutting/sewing only. (DR-041 modeling still open)
- **Made-to-order** production, driven by customer order; new products follow an ETO-like R&D/drawing/proof path, repeats reuse the SKU.
- **SKU & dependent parameters are derived by the system** from the customer's main parameters. (SR-01)
- **Product classification is multi-level:** type → class → family + product group. (DR-044, SR-02)
- **Material is subtyped** (resin, ink, solvent, consumable, packaging, regrind); MRP treats them distinctly. (DR-042, SR-04)
- **Cliché/printing tooling** is a first-class asset with usage-life and a dedicated store. (SR-03)
- **Capacity, machine-settings, allowed-scrap, allowed-downtime** are data-driven tables keyed by machine×product(×site) — never hard-coded. (SR-05)
- **Inline QC can auto-stop a WO and spawn a rework WO.** (SR-06)
- **Rework produces sellable output; scrap can be recycled into regrind lots** (Tehran). (SR-07)
- **Roll/lot genealogy** provides full traceability across operations. (SR-08)
- **Two-stage goods receipt** (temporary → QC → definitive). (SR-09)
- **Unlimited warehouses with special store types**, per-user access, consumption permits, rial+quantity kardex. (SR-10)
- **Bilingual fa/en + Jalali/Gregorian** throughout; **sanction/FX awareness** is a real constraint. (NFR-010/011/022)

## Critical decisions

- **NQ-001 / DR-000 — BUILD vs BUY: RESOLVED (2026-08-21).** The SLZ business **confirmed a custom ERP/MES build**. The NEPTA study's recommendation to buy Microsoft Dynamics 365 F&O was **considered and rejected** for this project. Domain implementation is **no longer gated on NQ-001**. Do **not** change the architecture merely because D365 was once recommended.
- **NQ-002 (still open):** exact company/site list beyond the confirmed phase-1 SLZ + Helena. Safe to model SLZ + Helena now.
- Master-data reshaping decisions in `master-data-impact.md` (multi-company, taxonomy, material subtypes, thin-product-vs-engineering split) apply.

## Current build status

- **Task 003 platform foundation is built** (`erp/`): identity/RBAC, audit, documents, localization (Jalali/Gregorian), notifications, workflow, standardized API surface, domain events, versioning pattern. The feasibility study validates these foundation choices (bilingual/Jalali, audit, RBAC, object storage, multi-company org).
- **Domain modules 004–011 have code committed** (`erp/backend/apps/`): `partners` + `catalog` + `hr` (Task 004 Master Data), `engineering` (Task 005 Product Engineering — versioned specification), `manufacturing` (Task 006 BOM & Routing), `inventory` (Task 007 foundation), `quality` (Task 008 plans), `procurement` (Task 009), `sales` (Task 010), `production` (Task 011 work orders). Each ships models, services, serializers, viewsets, URLs and tests, and follows the audited-write / RBAC / versioning conventions.
- **These modules are IMPLEMENTED-BUT-UNVERIFIED.** The repository commits **no migration files** (only empty `migrations/__init__.py` packages; the entrypoint is `makemigrations && migrate`), and the Django test suite has **not** been executed in the current authoring environment (offline sandbox — PyPI is proxy-blocked, so Django/DRF cannot be installed to run `makemigrations`/`migrate`/`pytest`). All Python has been checked with `py_compile` only. **No milestone can be certified COMPLETE until migrations and the full test suite run green in a normal dev environment.** See `docs/architecture/verification-audit.md`.

> Bottom line for future agents: the platform is real and domain apps 004–011 are coded to the SLZ conventions, but **treat them as unverified until migrations + tests are run**. Build-vs-buy is settled (custom build). Respect the SLZ-specific rules over generic ERP defaults, and check `docs/reconciliation/` before writing any domain code.
