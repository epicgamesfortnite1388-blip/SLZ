# Skill 05 — Inventory & Traceability

## Purpose
Encode SLZ inventory as lot- and roll-tracked stock with full genealogy, and make every stock change an auditable transaction.

> **RECONCILED (Task 004A).** The official SLZ doc confirms and adds: **Material is subtyped** — resin/masterbatch, **ink (مرکب)**, **solvent (حلال)**, consumables, packaging, semi-finished, finished, **regrind** — because MRP/formulation/QC treat them distinctly (SR-04 / DR-042 CONFIRMED); the material master needs a **subtype discriminator** plus multi-UoM, substitutes, min/max/reorder, safety stock, EOQ, lead time, **shelf-life/expiry**, MSDS. **Goods receipt is two-stage: temporary → QC → definitive**, gated on a QC pass threshold (SR-09). **Warehouses are unlimited with special store types** — scrap, quarantine, **cliché**, line-side (پای کار), consignment (امانی), stagnant (راکد) — with **per-user warehouse access**, a **consumption-permit** transaction, and a **quantity + rial kardex** (SR-10). **Scrap recycles into regrind material lots** (closed-loop, Tehran only — SR-07), and warehouses/stock are **site-scoped** (multi-company, DR-040). Warehouse master shape is Task-004-adjacent; movements/kardex/genealogy are later inventory-task work. All gated on BUILD-vs-BUY (NQ-001).

## When to Read This Skill
Any work on warehouses, locations, materials, lots, rolls, reservations, stock movements, receipts, issues, transfers, production consumption/output, quarantine, or traceability/recall.

## Source of Truth
- `docs/business-analysis/inventory-model.md` — inventory hierarchy, movements, traceability.
- `docs/architecture/transactions.md` — atomic write strategy.
- Requirements: FR-050..FR-060, NFR-006, NFR-008.

## Core Rules
1. **Inventory is not simple quantity-on-hand.** It is lot- and roll-tracked with genealogy.
2. **Every inventory change is an immutable, append-only Stock Movement** (from→to location, or in/out of a virtual location). *(FR-053)*
3. **Never silently change stock quantities.** Corrections are reason-coded adjustment/reversing movements, never destructive edits *(NFR-006)*.
4. **Do not delete historical stock movements.** Append-only.
5. **Lot/roll identity must be preserved** across every transformation.
6. **Reservation ≠ consumption.** Reservation is a soft allocation (`available = on-hand − reserved`); consumption is a physical issue movement.
7. **Atomicity:** a work-order confirmation's consumption + output + genealogy + cost capture commit as **one transaction**; no partial posting *(constraint #8)*.

## Domain Concepts
**Object hierarchy:** Raw Material (item master) · Raw Material Lot (supplier batch #, GRN, COA) · Roll/Reel (unique ID, weight, length, width, core — base film/printed/laminate/slit) · Semi-finished product (rolls) · Finished product (production batch/lot + pack units) · Packaging materials (cartons, cores, pallets, labels).

**Warehouse model:** `Warehouse → (Zone) → Location`; location types: RM store, WIP/floor, FG store, QC-hold, quarantine, scrap, shipping-staging, returns.

**Movement types:** Receipt (GRN) · Issue to production · Production receipt · Transfer · Reservation/allocation (soft) · Scrap issue · Adjustment (reason-coded) · Shipment issue · Return receipt (RMA).

**Forward genealogy:**
`Supplier → Raw Material Lot → Production Batch → Semi-Finished Lot → Finished Product Lot → Customer Delivery`.

**Reverse genealogy:**
`Customer Delivery → Finished Product → Production Batch → Raw Material Lots → Supplier`.

**Genealogy mechanism:** a batch/roll genealogy table records `parent_object → child_object` for every transformation (1:N split at slitting, N:1 merge at lamination). Each batch stores input lots/rolls, machine, operator, shift, routing/BOM revision, spec revision, QC results, timestamps — enabling recall / mock-recall.

**UoM:** multiple units coexist (kg, m, m², µm, pieces, rolls, cartons, pallets) with conversions (kg↔m via grammage & width). Factors are `[OPEN]` (Q-052).

## Required Behaviors
- Record every stock change as a Stock Movement with actor, timestamp, reason where relevant.
- Preserve lot and (where serialized) roll identity through transformations.
- Maintain parent→child genealogy edges on every production transformation.
- Keep reservation and consumption as distinct concepts/records.
- Use `Decimal` quantities with explicit UoM; convert at the edge, store canonical.

## Forbidden Behaviors
- Do **not** mutate `quantity_on_hand` directly or delete/edit movements.
- Do **not** collapse reservation into consumption.
- Do **not** post output without genealogy links in the same transaction.
- Do **not** hard-code these OPEN decisions — leave configurable and do not build the dependent logic while gated:
  - Roll **serialization vs lot+count** (Q-046/DR-020) — *foundational; do-not-build-yet #18*.
  - Inventoried intermediates / real BOM levels (Q-026/DR-021) — #19.
  - Traceability granularity roll/pallet/carton (Q-049/DR-022) — #20.
  - Material issue method explicit vs backflush (Q-048/DR-031) — #21.
  - Shelf-life/FEFO enforcement (Q-051/DR-036) — #16.
- Do **not** build formal recall/mock-recall automation yet — design the genealogy to *allow* it *(do-not-build-yet #31)*.

## Implementation Guidance
Model Stock Movement as an append-only, authored, timestamped entity; never `SoftDeleteModel` semantics that hide history — retain everything. Wrap posting in a service using `atomic_with_events`. Represent genealogy as an edge/closure table for performant forward/reverse queries *(NFR-014)*. Reservation is a separate record feeding availability, not a movement of physical stock.

> **Design-tension note (C-003):** full roll-level genealogy (esp. 1→N at slitting) implies **serialized rolls + explicit lot/roll issue**; lot+count and backflush would weaken it. The recommendation is serialize + explicit issue for traceable materials, backflush for bulk consumables — but this is `OPEN` and must be decided before the traceability schema is migrated.

## Examples
- *Consume a roll into lamination.* Issue movement (roll → WIP/virtual), output movement (new laminate roll), genealogy edge parent→child — all one transaction.
- *Stock count correction.* Post a reason-coded adjustment movement; never overwrite the on-hand figure.

## Common Mistakes
- Editing quantities instead of posting movements.
- Losing the parent roll link after slitting (1→N).
- Treating a reservation as if stock were already consumed.
- Assuming every intermediate is stocked (some are flow-through — C-004).

## Validation Checklist
- [ ] Is every stock change an append-only movement?
- [ ] Are lot/roll identities and parent→child edges preserved?
- [ ] Are reservation and consumption distinct?
- [ ] Is posting atomic with output + genealogy + cost?
- [ ] Are serialization/granularity/backflush/FEFO left configurable and ungated work avoided?

## Related Documentation
`docs/reference/NEPTA_ERP_Feasibility_Study.md` · `docs/reconciliation/slz-specific-rules.md` (SR-04/07/09/10) · `docs/business-analysis/inventory-model.md` · `docs/requirements/contradictions.md` (C-003, C-004) · `docs/requirements/do-not-build-yet.md`

## Skill Dependencies
Inventory depends on: `01-slz-domain`, `02-erp-architecture`, `07-coding-standards`, `08-agent-workflow`. Tightly coupled with `03-manufacturing-mes` and `06-quality`.
