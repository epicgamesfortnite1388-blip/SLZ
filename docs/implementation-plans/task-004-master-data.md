# Task 004 — Master Data Foundation — Implementation Plan (GATED, PLAN-ONLY)

**Status:** DRAFT — plan only. **No code is to be written under this plan yet.**
**Date:** 2026-08-21
**Owner sources:** `docs/reconciliation/master-data-impact.md` (R-MD-01..13) · `docs/reconciliation/slz-specific-rules.md` (SR-01..16) · `docs/SLZ-SOURCE-OF-TRUTH.md` · `skills/` (01, 02, 04, 05, 07, 08)

> **CRITICAL GATE — DO NOT IMPLEMENT.** This plan is blocked on two open business decisions:
> - **NQ-001 — BUILD vs BUY (DR-000, CRITICAL):** the official study recommends buying **Microsoft Dynamics 365 F&O**. The custom Django/DRF/React stack (DR-001/002/011) is `PROPOSED — CONFLICT FLAGGED`. If the business chooses BUY, this entire plan is void.
> - **NQ-002 — exact company/site list** beyond the confirmed SLZ (Tehran) + Helena (Saveh).
>
> This document exists so that *if* build-over-buy is reaffirmed, Task 004 implementation starts correct and reshaped. Until then it is reference only.

---

## 1. Purpose & Scope

Task 004 establishes the **master-data foundation** on top of the Task 003 platform: the durable, low-churn reference entities (companies, sites, partners, materials, product identity, UoM, taxonomy) that every later domain module (engineering, inventory, manufacturing, quality, sales) depends on.

It deliberately **excludes** engineering logic, transactional records, and process behavior. Per `master-data-impact.md`, Task 004 keeps Product as a **thin, classified master**; the rich versioned spec, formulations, SKU-derivation service, and cliché move to **Product Engineering (Task 005)**.

This plan follows the reconciled reality: **multi-company/multi-site is real** (DR-040), **taxonomy is multi-level** (SR-02/DR-044), **Material is subtyped** (SR-04/DR-042), and all master data is **company/site-scoped**.

## 2. Architectural Ground Rules (from skills 02 & 07)

- Add master data as **Django apps under `backend/apps/`** depending only on foundation apps; never put business logic in foundation apps.
- **Extend the existing `organization` app** (Company → Site → Department already exist as `SoftDeleteModel` with bilingual `name_fa`/`name_en`, `PROTECT` FKs). Do **not** rebuild it.
- Use base classes from `apps/core`: `UUIDModel`/`TimeStampedModel`/`AuthoredModel`/`BaseModel`/`SoftDeleteModel`. Pick the **minimum** needed — do not apply soft delete blindly.
- Business logic in `services.py` (via `atomic_with_events`); thin views; serializer-level input validation; `module.resource.action` permissions enforced by `HasPermission`.
- UUID PKs + **separate business-number/code fields**; bilingual fields at model level; no presentation formatting (Persian digits/Jalali strings) persisted — format at the edge via `localization`.
- FKs to master data use `PROTECT`/`SET_NULL`, never `CASCADE` (preserve history).
- Money/quantities as `Decimal` with explicit precision; datetimes UTC-aware.

## 3. Entity Scope (from R-MD-01..13)

### 3.1 In scope for Task 004 (safe, confirmed, foundational)

| # | Entity | App (proposed) | Action | Key notes |
|---|---|---|---|---|
| R-MD-01 | Company (multi-company) | `organization` (extend) | RESTRUCTURE | Genuinely multi-company; SLZ + Helena safe now. Most master data company-scoped. GATE on NQ-002 for full list. |
| R-MD-02 | Site / Plant | `organization` (extend) | EXPAND | Add **capability set** (which production stages exist); Tehran ≠ Saveh (SR-15). Capacity tables (later) are site-scoped. Modeling approach DR-041 OPEN → keep configurable. |
| R-MD-03 | Department / sales-line | `organization` (extend) | EXPAND | Accommodate real units (R&D, Edit, Planning, Production Control, Production, QC, Warehouse, Procurement, Finance, HR, Technical); **sales line** = department-like grouping keyed to product group; feeds RBAC scoping. |
| R-MD-04 | Partner + Customer/Supplier roles | `partners` (new) | EXPAND | Party + roles; add **sanctioned-party flag** (NFR-022), customer **sales-line/product-group** link, supplier **evaluation stub**. |
| R-MD-05 | Contacts & Addresses | `partners` (new) | KEEP | Attached to Partner. CRM extends later. |
| R-MD-06 | Minimal Employee | `identity`/`hr_min` (decide) | partial KEEP | Identity + department + site only, for operator identity & warehouse access. Full HR DEFER. |
| R-MD-07 | UoM + conversions | `catalog`/`uom` (new) | KEEP | Multiple UoM per item + conversion factors + substitutes (A-021). Early core. |
| R-MD-08 | Product taxonomy | `catalog` (new) | RESTRUCTURE | **type → class → family (نوع/طبقه/خانواده) + product group** (SR-02). Multi-level, not a flat category. Product groups also structure sales lines/CRM. |
| R-MD-09 | Product (master identity only) | `catalog` (new) | careful EXPAND | Classified, UoM, category; **no** spec/BOM/SKU-logic. SKU *field* may exist; SKU-**derivation service** is Task 005. |
| R-MD-10 | Material / Item | `catalog` (new) | RESTRUCTURE | **Subtype discriminator** — resin/masterbatch, ink, solvent, consumable, packaging, semi-finished, finished, **regrind** (SR-04). Plus multi-UoM, substitutes, min/max/reorder, safety stock, EOQ, lead time, **shelf-life/expiry**, MSDS. |
| R-MD-11 | Business codes / numbering | `core`/`catalog` | KEEP + EXPAND | Keep UUID + business-number separation. SKU generator is a Task 005 service; code fields live on masters now. |

### 3.2 Explicitly deferred (later tasks — record, do not build)

- **Product Engineering (Task 005):** spec revisions, formulations (main/alt ink & solvent), drawings/artwork, per-level marking, **SKU-derivation service**, print-mounting calc, **Tooling/Cliché** (R-MD-13, SR-03).
- **Manufacturing tasks:** BOM / Routing / OPC, capacity / machine-settings / allowed-scrap / allowed-downtime tables (SR-05).
- **Inventory task:** warehouse store logic, kardex (qty+rial), consumption permit, two-stage GRN movements, lot/roll genealogy (SR-07/09/10).
- **Later domains:** CRM (leads/opportunities/complaints, NQ-009), full Finance, full HR, Maintenance, Foreign-trade.

### 3.3 Gated / confirm-scope

- **R-MD-12 Warehouse master:** store-type enum (scrap/quarantine/cliché/line-side/consignment/stagnant) + site scoping + per-user access. The Task 004 brief did not clearly include Warehouse → **GATE: confirm whether warehouse *master* is in Task 004 or belongs to the inventory task.**
- **R-MD-13 Tooling/Cliché:** DEFER to Task 005 (tied to artwork/engineering); record now so it is not forgotten.

## 4. Proposed App Layout

Extend one existing app, add two new business apps (final split confirmed at implementation time):

- **`organization` (extend, Task 003):** Company (multi-company), Site (+ capability set), Department (+ sales-line). No new app needed.
- **`partners` (new):** Partner + Customer/Supplier roles, Contacts, Addresses, sanction flag, supplier-evaluation stub. Depends on `organization` (company/site scoping), `core`, `identity`.
- **`catalog` (new):** UoM + conversions, product taxonomy (type/class/family + group), Product master identity, Material master with subtype. Depends on `organization`, `core`.
- **Minimal Employee:** decide between a slim model in `identity` vs a stub `hr` app; keep to identity + department + site only.

Each app follows the standard internal layers (`models`/`managers`/`services`/`serializers`/`permissions`/`views`/`urls`/`subscribers`), mounted at `/api/v1/`, with `module.resource.action` permission codes and standardized response/error envelopes.

## 5. Cross-Cutting Requirements

- **Company/site scoping** is inherent: every master entity carries (or resolves) its owning company/site; managers scope queries; RBAC and later warehouses/capacity/work-orders inherit this. Never assume single-company.
- **Bilingual** `name_fa`/`name_en` on every named master entity; Persian is primary (RTL). Dual-calendar handled at the edge via `localization`.
- **Versioning:** master identity entities here are mostly **not** versioned (they are stable identity). Versioning (`VersionedRoot`/`Revision`) belongs to the **specifications** in Task 005, not the Task 004 product/material master. Do not over-apply it.
- **OPEN items stay configurable:** site-capability modeling (DR-041), product/material coding schemes (Q-019), UoM conversion factors (Q-052), taxonomy value lists — leave as data/config, never hard-code.
- **Audit/events:** all writes through services publish standard domain events post-commit; audit coverage is automatic.

## 6. Phasing (only after NQ-001 = BUILD is reaffirmed)

1. **Phase 0 — Gate clearance:** confirm NQ-001 (build) and NQ-002 (company/site list); decide warehouse-master scope (R-MD-12) and Employee placement (R-MD-06). No code before this.
2. **Phase 1 — Organization:** extend Site with capability set; extend Department with sales-line concept; seed SLZ (Tehran) + Helena (Saveh).
3. **Phase 2 — UoM + taxonomy:** UoM + conversions; multi-level product taxonomy (type/class/family + group).
4. **Phase 3 — Material master:** subtype discriminator + subtype-specific fields (shelf-life, MSDS, reorder points, substitutes).
5. **Phase 4 — Product master identity:** classified, UoM, category, code field (no spec/SKU logic).
6. **Phase 5 — Partners:** Partner + roles, contacts/addresses, sanction flag, sales-line link, supplier-eval stub.
7. **Phase 6 — Minimal Employee + wiring:** operator identity + department/site; connect to RBAC scoping.

Each phase = models + migration + service layer + serializers + permission map + API + tests, verified (build + tests green) before the next.

## 7. Explicit Non-Goals (do-not-build-yet)

No SKU-derivation logic, spec revisions, formulations, cliché, BOM/routing, capacity/scrap tables, warehouse movements/kardex/genealogy, consumption permits, CRM, finance, or full HR. These are named here only to keep the master-data shapes forward-compatible with them.

## 8. Validation Checklist (for when work is authorized)

- [ ] NQ-001 (build) and NQ-002 (company/site list) confirmed before any code.
- [ ] `organization` extended, not rebuilt; multi-company/site real.
- [ ] Taxonomy is multi-level (type/class/family + group), not a flat category.
- [ ] Material master has a subtype discriminator + subtype fields.
- [ ] Product master is a thin classified identity — no spec/BOM/SKU-derivation logic.
- [ ] All master entities company/site-scoped; FKs `PROTECT`/`SET_NULL`.
- [ ] OPEN items (capability modeling, coding schemes, conversion factors) left configurable.
- [ ] Writes go through services with `atomic_with_events`; permissions declared as `module.resource.action`.
- [ ] Deferred entities (engineering/inventory/manufacturing/CRM) not built.

## 9. Related Documentation

`docs/SLZ-SOURCE-OF-TRUTH.md` · `docs/reconciliation/master-data-impact.md` (R-MD-01..13) · `docs/reconciliation/slz-specific-rules.md` (SR-01/02/04/15/16) · `docs/requirements/decision-register.md` (DR-000/040..044) · `docs/requirements/do-not-build-yet.md` · `skills/01-slz-domain` · `skills/02-erp-architecture` · `skills/04-packaging-engineering` · `skills/05-inventory-traceability`
