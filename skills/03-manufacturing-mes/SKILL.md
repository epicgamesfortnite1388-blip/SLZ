# Skill 03 — Manufacturing / MES

## Purpose
Teach agents to model SLZ production as a chain of physical transformations, not a status flag.

> **Manufacturing is not simply changing an order status. Production is a sequence of physical transformations with material consumption, output, waste, machine time, labor, quality checks and traceability.**

> **RECONCILED (Task 004A).** The official SLZ doc confirms and sharpens several rules — build to these: **capacity, machine-settings, allowed-scrap, allowed-downtime are data-driven tables keyed by machine × product × site** (SR-05), never hard-coded. **Production capability is site-specific** (SR-15/DR-041): Tehran runs all stages incl. recycling; Saveh (Helena) runs blown film + cutting/sewing only — feasibility/routing must respect the site capability set. **Inline QC can auto-stop a work order and spawn a rework WO** (SR-06). **Rework produces sellable output; scrap can be recycled into regrind lots** (SR-07, Tehran only). **Operations may be outsourced** to a sister company or external vendor, with costing + QC-on-return (SR-14/DR-043/NQ-004) — a routing operation carries an execution locus. Order **priority is by margin** (SR-13) and delivery dates are **ATP-estimated** from capacity+orders+stock+lead time (SR-12) — both later-phase. Manufacturing implementation is gated on the BUILD-vs-BUY decision (NQ-001).

## When to Read This Skill
Any work touching production orders, work orders, operations, work centers, machines, batches, scrap, rework, downtime, or shop-floor reporting.

## Source of Truth
- `docs/business-analysis/manufacturing-processes.md` — process chain, production-model concepts, machine capability profiles.
- `docs/business-analysis/bom-and-routing.md` — routing/operation model.
- `docs/business-analysis/business-processes.md` §5.5 — production-order state machine.
- Requirements: FR-040..FR-049, FR-100 in `docs/requirements/requirements-baseline.md`.

## Core Rules
1. **Multi-stage.** A product's routing selects which stages apply; not every product uses every stage. Chain: film forming → prepress → flexo printing → lamination → (curing) → slitting → converting → inspection/packing.
2. **Data-driven machine behavior — no hard-coded machine logic** *(constraint #9)*. Each machine carries a **capability profile** (web width, thickness range, speed range, color stations, supported materials/structures/bag types, setup baselines). Planning/validation reads these attributes generically. Adding a machine = adding data, not code.
3. **Changeover is a from→to matrix** (data), never branched in code.
4. **A Production Order snapshots the BOM revision + Routing revision** it was released with, so later edits never alter historical orders *(FR-038)*.
5. **Work-order confirmation is atomic:** material issues (with lot/roll) + good/scrap qty + time/downtime + inline QC + output batch + genealogy commit together *(constraint #8)*.
6. **Output is a Production Batch → Roll(s)/units** posted to inventory with parent→child genealogy *(FR-047)*.

## Domain Concepts
| Concept | Modeled as | Note |
|---|---|---|
| Production Order | per-stage order (product spec rev, qty) | snapshots BOM+Routing rev |
| Work Order | one operation on a chosen machine | setup + run confirmations |
| Operation | ordered step at a work center | run rate, setup, tooling, skills, QC, std scrap |
| Routing | ordered operations bound to a spec revision | versioned |
| Work Center | logical stage grouping interchangeable machines | e.g. Printing |
| Machine | physical resource | capability profile (data) |
| Production Batch | traceable output unit | genealogy anchor |
| Material Consumption | BOM lines issued at an operation | with RM lot / parent roll |
| Output | good units/rolls posted to inventory | |
| Scrap | reason-coded qty per stage | feeds cost & yield *(Q-016/042 OPEN)* |
| Rework | traced re-pass through an operation | genealogy preserved *(Q-043 OPEN)* |
| Downtime | reason-coded machine stoppage | feeds OEE/cost |
| Setup / Changeover | operation attr / from→to matrix | data-driven |

**Production Order state machine (proposed):** `PLANNED → RELEASED → IN_PROGRESS → (PAUSED) → COMPLETED → CLOSED`; `CANCELLED`; `QC_HOLD → (PASS→next | FAIL→rework/scrap)`.

**Alternative machines:** an operation runs on any *qualified* machine (by capability); planner or system chooses.

**Scheduling:** first release is **finite-capacity-aware but manual/assisted** — planner assigns work orders. Automatic APS is out of scope *(DR-012; do-not-build-yet #22)*.

**Genealogy:** extrusion batch → base film roll → printed roll → laminate roll → N slit rolls (1→N) → finished units. Every transformation records parent→child links.

## Required Behaviors
- Represent machine capability, setup, changeover, yield/scrap %, and run rates as **configurable data**.
- Bind work orders to specific machines from the qualified pool.
- Capture actual vs planned separately (setup/run time, good/scrap qty).
- Record spec revision, BOM/routing revision, machine, operator, shift, and QC result on each batch.

## Forbidden Behaviors
- Do **not** hard-code machine behavior, changeover times, scrap %, or yields — all are data (and mostly `[OPEN]`).
- Do **not** model "production" as a single step/status.
- Do **not** post output without recording consumption + genealogy in the same transaction.
- Do **not** build automatic scheduling/APS, advanced OEE, or PLC/IoT integration yet *(do-not-build-yet #22, #24, #25)*.
- Do **not** invent the machine list, stage sequence certainty, or standard routings — these are `[OPEN]` (Q-010..Q-018, Q-029).

## Implementation Guidance
Use `VersionedRoot`/`Revision` for routings. Model machine capability as attributes/JSON on the machine (validated generically), not code branches. Keep confirmation logic in a service using `atomic_with_events`. Which intermediates are inventoried is **configurable per stage** — do not assume all stages produce a stocked item (see C-004, `05-inventory-traceability`).

## Examples
- *Add a new printing machine.* Create a machine record + capability profile; no code change. If code needs an `if machine.name == …` branch, that is a design error.
- *Print then laminate.* Two operations, two output batches (printed roll, laminate roll), each with genealogy to inputs; lamination consumes the printed roll + second web + adhesive.

## Common Mistakes
- One "quantity produced" field instead of good/scrap/rework per stage.
- Referencing the routing root instead of the released revision on the production order.
- Assuming every product runs every stage.
- Hard-coding a scrap % that is actually OPEN.

## Validation Checklist
- [ ] Is machine behavior data-driven (capability profile), not branched in code?
- [ ] Does the production order snapshot BOM + routing revisions?
- [ ] Do confirmations commit consumption + output + genealogy + QC atomically?
- [ ] Are scrap/yield/changeover values configurable and not hard-coded?
- [ ] Did I avoid building deferred items (APS, OEE, PLC)?

## Related Documentation
`docs/reference/NEPTA_ERP_Feasibility_Study.md` · `docs/reconciliation/slz-specific-rules.md` (SR-05/06/07/13/14/15) · `docs/reconciliation/slz-domain-model.md` (§D) · `docs/business-analysis/manufacturing-processes.md` · `docs/business-analysis/bom-and-routing.md` · `docs/requirements/do-not-build-yet.md`

## Skill Dependencies
Manufacturing depends on: `01-slz-domain`, `02-erp-architecture`, `04-packaging-engineering`, `05-inventory-traceability`, `06-quality`, `07-coding-standards`, `08-agent-workflow`.

## Implementation Status (Task 006 — 2026-08-21)
The **engineering definition** of manufacturing is implemented in `apps/manufacturing` — resource masters `WorkCenter` and `Machine` (with data-driven `capability_profile` JSON; no hard-coded machine logic, constraint #9), plus two versioned structures bound to a `SpecificationRevision`: `BillOfMaterials` (root → `BomRevision` → `BomLine`) and `Routing` (root → `RoutingRevision` → `RoutingOperation`). Both revisions share one generic draft → activate → supersede lifecycle service (immutable once non-DRAFT); all writes are audited via domain events. See `docs/architecture/manufacturing-bom-routing.md`.

Still `[OPEN]` and intentionally **not** built: consumption bases / waste / standard scrap % (Q-027, #9 — `consumption_basis` free text, `scrap_pct` nullable, no default); standard routing templates & stage-skip rules (Q-029, #10); inventoried intermediates / real BOM levels (Q-026, #19 — `output_material` optional); alternates/substitutes, changeover matrix, machine-qualification pools, skills, QC-plan and tooling links; outsourcing execution locus (DR-043/NQ-004); and **all production EXECUTION** (production/work orders, confirmations, consumption, genealogy, OEE — the production-order snapshot of BOM+routing revisions described above belongs to that later task).
