# Manufacturing Processes & Production Model

> Tags: **[CONFIRMED]** · **[ASSUMPTION]** · **[OPEN]** · **[PROPOSAL]**.
> This document describes the physical process chain SLZ operates and the *data model concepts* used to represent production. It deliberately keeps machine behaviour **data-driven** (constraint #9: no hard-coded machine logic).

---

## 1. The flexible-packaging process chain [CONFIRMED capabilities, sequence ASSUMPTION A-007]

SLZ's public capabilities map to a typical converting chain. Not every product uses every stage — the **routing** (see `bom-and-routing.md`) selects which stages apply.

```
 Resin/compound
      │
      ▼
 (1) FILM FORMING ──► Blown film  |  Cast film     ──► produces base film ROLL
      │
      ▼
 (2) PREPRESS  (color matching, plate/cylinder prep)   [prepares tooling & color, not a film stage]
      │
      ▼
 (3) FLEXO PRINTING ──► prints artwork onto film       ──► printed ROLL (semi-finished)
      │
      ▼
 (4) LAMINATION / EXTRUSION-LAMINATION ──► bonds 2+ webs (+adhesive/cold seal/coating) ──► laminate ROLL
      │
      ▼
 (5) CURING / AGING (solventless/solvent adhesives need time)   [ASSUMPTION A-008]
      │
      ▼
 (6) SLITTING / REWINDING ──► cuts master roll to width, rewinds ──► slit ROLLS
      │
      ▼
 (7) CONVERTING / BAG-MAKING ──► seals, cuts, punches ──► FINISHED bags/pouches/sheets
      │
      ▼
 (8) INSPECTION / PACKING ──► final QC, cartoning, palletizing ──► FINISHED GOODS
```

**Finishing effects** referenced by SLZ — cold seal, spot matte, gloss, special effects — are applied at printing/lamination/coating stages, driven by the product spec, not separate machines necessarily. **[OPEN Q-010]** Which effects are inline vs. separate passes/machines?

**[OPEN Q-011]** Provide the actual machine list per stage (make, count, web widths, speed ranges, color stations, gearless/geared, etc.) so capability profiles can be modeled. Do **not** hard-code; capture as data.

---

## 2. Stage-by-stage description

### 2.1 Blown film / Cast film (extrusion) [CONFIRMED]
- **Input:** resin blends (PE/PP/PA/EVOH…), masterbatch, additives.
- **Output:** base film roll, characterised by thickness (micron), width, layer structure (mono/multilayer, e.g. 3/5/7-layer coex), treatment (corona).
- **Key parameters (data-driven):** layer recipe, target micron, width, corona dyne level, output kg/h.
- **[OPEN Q-012]** Number of extrusion layers / co-extrusion capability? Corona treatment inline?

### 2.2 Prepress & color matching [CONFIRMED]
- Converts approved artwork into print-ready separations, generates **printing tooling** (photopolymer plates/sleeves or cylinders), and defines the **color standard** (spot colors, ΔE tolerance, ink recipe).
- Output objects: prepress file set, tooling set, color recipe — all versioned and tied to an **artwork revision**.

### 2.3 Flexographic printing [CONFIRMED]
- **Input:** base film roll + tooling + inks (+ solvents).
- **Output:** printed roll (semi-finished).
- **Key parameters:** number of colors/stations, ink per color, anilox spec, print speed, registration tolerance, repeat length.
- **[OPEN Q-013]** Max number of print stations (colors)? Solvent-based, water-based, or UV flexo inks?

### 2.4 Lamination / extrusion-lamination [CONFIRMED]
- Bonds webs (e.g. PET/PE, PET/AL/PE) using adhesive (solvent, solventless) or extrusion lamination.
- **Key parameters:** structure (web layup), adhesive type & coat weight (g/m²), line speed, cure schedule.
- Cold seal application also modeled here or as a coating pass.

### 2.5 Slitting / rewinding [ASSUMPTION A-009]
- Cuts master rolls to ordered widths, rewinds to target roll length/diameter.
- Generates multiple child rolls from one parent (1→N lot genealogy).

### 2.6 Converting / bag-making [CONFIRMED "converting"]
- Produces final format: bags, pouches (stand-up, 3-side seal, etc.), sheets, sleeves.
- **Key parameters:** bag type, seal type, dimensions, gusset, zipper/valve, print position.
- **[OPEN Q-014]** Which bag/pouch formats does SLZ make? Enumerate.

### 2.7 Inspection & packing [ASSUMPTION A-010]
- Final QC, count/weigh, carton & palletize, label (bilingual), stage for shipment.

---

## 3. Production model concepts

The brief lists concepts each production process must represent. Mapping to proposed entities:

| Concept | Modeled as | Notes |
|---------|-----------|-------|
| **Machine** | `machine` entity | Belongs to a work center; has a **capability profile** (data). |
| **Work center** | `work_center` entity | Logical stage grouping (e.g. "Printing"); groups interchangeable machines. |
| **Capacity** | attributes on machine/work center + calendar | Rated speed (m/min or kg/h), shifts, availability calendar. |
| **Setup time** | operation/work-order attribute | Time to prepare (mount plates, thread web, color set). |
| **Runtime** | derived from qty ÷ rated speed + confirmations | Planned vs actual captured separately. |
| **Changeover** | changeover matrix | Time depends on *from→to* product/tooling; data-driven matrix, **not** hard-coded. |
| **Operators** | `operator`/user assignment + skill/qualification | Which roles/skills can run which machine. |
| **Materials** | BOM consumption at operation | Inputs consumed per work order (with lot). |
| **Output** | production batch → roll(s)/units | Good output posted to inventory. |
| **Scrap** | scrap record on work order | Qty + reason code + stage; feeds cost & yield. |
| **Quality checks** | inline QC tied to operation/batch | Pass/fail, measurements. |
| **Downtime** | downtime record | Reason-coded machine stoppage; feeds OEE & cost. |
| **Alternative machines** | routing alt-resources / work-center pool | Operation can run on any qualified machine; planner or system chooses. |

### 3.1 Machine capability profile [PROPOSAL — satisfies "no hard-coded machine logic"]
Each machine carries a **data-driven profile** instead of code branches:
- Web width min/max, thickness range, speed range, #color stations (print), layer count (extrusion), supported materials/structures, supported bag/seal types, energy draw, standard setup/changeover baselines.
- Planning & validation logic reads these attributes generically. Adding a machine = adding data, not code.

**[OPEN Q-015]** For each machine: rated capacity, valid ranges, and which operations/products it can perform.

### 3.2 Work order execution model [PROPOSAL]
```
Production Order (stage, product rev, qty)
   └─► Work Order(s) (operation on a chosen machine)
          ├─ setup (planned/actual)
          ├─ run confirmations (qty good, qty scrap, time, downtime events)
          ├─ material issues (with RM lot / parent roll)
          ├─ inline quality checks
          └─ output → Production Batch → Roll(s)/Units (to inventory, with genealogy)
```

### 3.3 Yield, scrap & waste [ASSUMPTION A-011]
- Every stage has expected yield %; actual yield = good ÷ input. Scrap reason codes per stage (edge trim, setup waste, print defect, lamination bubble, etc.).
- **[OPEN Q-016]** Standard/expected scrap % per stage? Are setup/edge-trim wastes tracked separately from defect scrap?

### 3.4 Roll & batch genealogy [CONFIRMED principle — traceability]
- Extrusion batch → parent roll → (printing) printed roll → (lamination) laminate roll → (slitting) N child rolls → (converting) finished units.
- Each transformation records **parent→child** links preserving forward & reverse traceability (see `inventory-model.md`).

---

## 4. Downtime, OEE & maintenance [PROPOSAL]
- Downtime events (reason-coded) + runtime + quality feed **OEE** (availability × performance × quality) per machine.
- **Maintenance order** entity (from brief): planned/preventive & breakdown maintenance, linked to machine; maintenance downtime feeds cost allocation and availability.
- **[OPEN Q-017]** Does SLZ want OEE tracking now, or only basic downtime capture? Is there existing PM scheduling?

---

## 5. Capacity & scheduling [PROPOSAL — defer detailed algorithm]
- Initial release: **finite-capacity-aware but manual/assisted scheduling** (planner assigns work orders to machines against a calendar). Full automatic APS scheduling is out of scope for first implementation.
- **[OPEN Q-018]** Current planning method (spreadsheet? whiteboard? existing MRP)? Bottleneck stage(s)?

---

## 6. Assumptions & questions raised
A-007 chain sequence · A-008 curing/aging · A-009 slitting genealogy · A-010 inspection/packing · A-011 yield/scrap. Questions Q-010…Q-018. Consolidated in [`open-questions.md`](./open-questions.md).
