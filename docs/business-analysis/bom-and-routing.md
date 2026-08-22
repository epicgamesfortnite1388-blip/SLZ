# BOM & Routing

> Tags: **[CONFIRMED]** · **[ASSUMPTION]** · **[OPEN]** · **[PROPOSAL]**.
> Both BOM and Routing are **versioned** and linked to a specific **product specification revision**. Preserve history (constraint #4/#5).

---

## 1. Why a multi-level BOM [PROPOSAL / CONFIRMED by process chain]

Flexible packaging is transformed in stages, each producing an inventoried semi-finished item (roll/reel). A **single-level** BOM cannot express "printed roll consumes base film + inks" then "laminate consumes printed roll + adhesive + 2nd film." So the BOM is **multi-level**, mirroring the routing stages:

```
FINISHED PRODUCT (bags)
 └─ consumes: SLIT ROLL, packaging materials (cartons, cores, labels)
     └─ SLIT ROLL ⇐ from LAMINATE ROLL (slitting)
         └─ LAMINATE ROLL
             └─ consumes: PRINTED ROLL, 2nd film/web, ADHESIVE, (cold seal)
                 └─ PRINTED ROLL
                     └─ consumes: BASE FILM ROLL, INKS, (solvents)
                         └─ BASE FILM ROLL
                             └─ consumes: RESINS, MASTERBATCH, ADDITIVES
```

Each level = a **semi-finished item** with its own BOM revision and the routing operation that produces it.

**[OPEN Q-026]** Confirm which intermediates SLZ actually stocks/tracks as inventoried items vs. flow-through (some plants don't stock printed rolls separately). This decides how many BOM levels are real.

---

## 2. BOM model [PROPOSAL]

### 2.1 Entities
- **BOM** — header bound to a *product spec revision* + *item level* (which output it produces).
- **BOM Revision** — immutable version; `status ∈ {DRAFT, APPROVED, ACTIVE, SUPERSEDED}`; `valid_from/valid_to`, `approved_by`.
- **BOM Line** — a consumed material/semi-finished item with **quantity per unit of output**, unit of measure, and **scrap/overage factor**.

### 2.2 BOM line quantity semantics [ASSUMPTION A-012]
Packaging consumption is often **per area/weight**, not per piece:
- Film/laminate consumption ≈ area (m²) × grammage → kg, plus **edge trim & setup waste %**.
- Ink consumption ≈ coverage × area → kg/g per color.
- Adhesive ≈ coat weight (g/m²) × area.
- Cartons/cores/labels = per finished-unit counts.

So each BOM line needs a **consumption basis**: `per_unit | per_area | per_weight | per_length | per_run_setup(fixed)`.
**[OPEN Q-027]** Confirm consumption bases and standard waste/overage factors per material type.

### 2.3 Yield & scrap in BOM [ASSUMPTION A-011/A-013]
- Gross requirement = net × (1 + scrap%) accumulated up the levels.
- Setup waste (fixed qty per run) vs. running waste (%) modeled separately.

### 2.4 Alternates & substitutes [ASSUMPTION A-014]
- A BOM line may allow **alternate materials** (e.g. resin grade A or B) with priority. Data-driven, not hard-coded.
- **[OPEN Q-028]** Are material substitutions allowed on the floor, and do they need QC/approval?

---

## 3. Routing model [PROPOSAL]

### 3.1 Entities
- **Routing** — bound to product spec revision; **versioned** (Routing Revision).
- **Operation** — an ordered step (sequence no.) performed at a **Work Center**; defines setup time, run rate (per area/length/weight/piece), required tooling, required skills, QC checks, standard scrap.
- **Work Center** — logical stage (Extrusion, Printing, Lamination, Slitting, Converting, Packing) grouping interchangeable **machines**.
- **Machine** — physical resource with capability profile; an operation can run on any *qualified* machine (alternative machines).

### 3.2 Operation attributes [maps brief's production-model list]
| Attribute | On operation? |
|-----------|---------------|
| Work center | yes (FK) |
| Eligible machines / alternatives | yes (pool, by capability) |
| Setup time (standard) | yes |
| Run rate / runtime basis | yes (m/min, kg/h, pcs/h) |
| Changeover | via changeover matrix (from→to) |
| Required operators/skills | yes |
| Input materials (BOM lines consumed here) | linked |
| Expected output (item + yield) | yes |
| Standard scrap % + setup waste | yes |
| Inline quality checks | yes (FK to QC plan) |
| Required tooling (plates/cylinders) | yes (for printing) |

### 3.3 Routing ↔ BOM linkage [PROPOSAL]
Each **operation produces one output item** and **consumes specific BOM lines**. This binds "what is consumed" to "where it is consumed," enabling accurate WIP, backflush, and cost capture per stage.

```
Routing Rev
 ├ Op 10  Extrusion  → output: BASE FILM ROLL     consumes: resins, MB
 ├ Op 20  Printing   → output: PRINTED ROLL        consumes: base film roll, inks
 ├ Op 30  Lamination → output: LAMINATE ROLL       consumes: printed roll, 2nd web, adhesive
 ├ Op 40  Slitting   → output: SLIT ROLLS          consumes: laminate roll
 ├ Op 50  Converting → output: FINISHED BAGS       consumes: slit rolls
 └ Op 60  Packing    → output: FINISHED GOODS      consumes: cartons, labels, pallets
```

Only stages relevant to the product are included (e.g. an unprinted roll-stock product skips Printing).

**[OPEN Q-029]** Confirm standard routings per product group and typical stage skips.

---

## 4. Versioning & effectivity [CONFIRMED requirement]
- BOM & Routing revisions are immutable once ACTIVE; superseding preserves history.
- A **Production Order** snapshots the **BOM rev + Routing rev** it was released with, so later BOM changes never alter historical orders (auditability).
- **[OPEN Q-030]** Approval authority for BOM/Routing release (industrial engineering? production manager?).

---

## 5. Configure-vs-author [PROPOSAL]
Because products are highly parametric, consider **templated BOM/Routing generation** from the product spec (e.g. structure → BOM lines) with engineer review, rather than fully manual authoring. Recommended as a *later* enhancement, not the first build.

---

## 6. Assumptions & questions
A-012 consumption basis · A-013 setup vs running waste · A-014 alternates. Questions Q-026…Q-030. Consolidated in [`open-questions.md`](./open-questions.md).
