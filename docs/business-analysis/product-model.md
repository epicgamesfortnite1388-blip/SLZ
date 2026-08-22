# Product Model — Versioned Technical Specification

> Tags: **[CONFIRMED]** · **[ASSUMPTION]** · **[OPEN]** · **[PROPOSAL]**.
> Core principle (brief): **do not model packaging products as simple SKU records.** A packaging product is a *customer-specific, multi-attribute, versioned technical specification*, not a flat catalogue item.

---

## 1. Why a flat SKU model fails here [CONFIRMED rationale]

A pouch "SKU" hides dozens of engineering attributes that change independently: structure, thickness, print, colors, ink, adhesive, bag/seal type, tolerances, packing. Two orders that look like "the same bag" may differ in one layer or one Pantone. Costing, QC and traceability all depend on the *exact spec revision produced*. Therefore the model separates **identity** from **specification** from **revision**.

---

## 2. Layered product identity model [PROPOSAL]

```
Customer ──1:N──► Customer Product (stable identity: "Customer X's 1kg coffee pouch")
                       │
                       └──1:N──► Product Specification Revision (v1, v2, … immutable once approved)
                                      │  (exactly one ACTIVE at a time; history preserved)
                                      ├──► Structure (layers/materials)
                                      ├──► Dimensions & format
                                      ├──► Print definition (+ Artwork revision link)
                                      ├──► Finishing (lamination, cold seal, matte/gloss, effects)
                                      ├──► Tolerances
                                      └──► Packaging / delivery spec
```

- **Customer Product** = durable identity the customer refers to ("our coffee pouch"). Stable code, does not change across revisions.
- **Product Specification** = the engineering definition. **Every technical specification is versioned** (brief requirement).
- **Product Specification Revision** = an immutable snapshot; one is ACTIVE, older ones SUPERSEDED (retained for traceability & re-order of old versions).

**[OPEN Q-019]** Does SLZ keep an internal *product code* independent of customer product code? What numbering scheme (mask) is used?

---

## 3. Specification attribute groups

The brief lists attributes the model must represent. Proposed grouping (all attributes carry unit + tolerance where applicable):

### 3.1 Structure & material [CONFIRMED attributes]
| Attribute | Representation | Notes |
|-----------|----------------|-------|
| Material structure | Ordered list of **layers** | e.g. `PET12 / ADH / AL7 / ADH / PE80`. Each layer = material + micron + function. |
| Thickness | Per-layer micron + total | Total derived; each layer tolerance. |
| Substrate materials | FK to material master | PET, PE, PP, PA, AL, paper… |

Modeled as a **structure = ordered set of layers**, each layer referencing a material and a thickness (with tolerance). This is more expressive than a single "thickness" field and directly supports the multilayer nature.

### 3.2 Dimensions & format [CONFIRMED]
| Attribute | Representation |
|-----------|----------------|
| Width | mm + tolerance |
| Length | mm + tolerance (for bags/sheets) or roll length |
| Gusset / bottom | mm (if applicable) |
| Bag type | enum/master: flat, side-gusset, stand-up (doypack), 3-side-seal, pillow, sheet, sleeve, roll-stock… **[OPEN Q-014/020]** confirm list |
| Format | roll stock vs. finished bag |

### 3.3 Printing & color [CONFIRMED]
| Attribute | Representation |
|-----------|----------------|
| Printing (yes/no, process) | flexo; surface vs reverse print |
| Number of colors | integer + list of color slots |
| Ink | FK to ink master per color + coverage; ink system (solvent/water/UV) |
| Color standard | per spot color: Pantone/target + ΔE tolerance |
| Artwork | FK to **Artwork revision** |
| Print position/repeat | mm |

### 3.4 Finishing & effects [CONFIRMED]
| Attribute | Representation |
|-----------|----------------|
| Lamination | structure implies it; adhesive type + coat weight (g/m²) |
| Adhesive | FK to adhesive master |
| Cold seal | yes/no + pattern/coverage |
| Matte / gloss | finish enum + spot vs full |
| Spot matte effect | region/coverage flag |
| Special effects | free/enumerated (soft-touch, metallic, registered matte…) **[OPEN Q-021]** |

### 3.5 Tolerances [CONFIRMED — cross-cutting]
Tolerances are **not one field** — they attach to many attributes (thickness ±, width ±, color ΔE, seal strength min, bond strength min, print registration ±, delivered quantity ±%). Modeled as **spec parameter = {value, unit, tol_low, tol_high / min / max}**.
**[OPEN Q-022]** Provide SLZ's standard tolerance defaults per attribute and per product group.

### 3.6 Packaging & delivery spec [CONFIRMED "packaging"]
| Attribute | Representation |
|-----------|----------------|
| Primary pack | bags/roll per carton, winding direction, core ID, roll OD/weight |
| Secondary pack | cartons per pallet, pallet type, stretch-wrap |
| Labeling | bilingual label spec, barcode/QR, lot marking |
| Delivery unit | how customer receives it |

### 3.7 Customer-specific specifications [CONFIRMED]
- Arbitrary customer requirements not covered above: certifications (food-grade, migration limits), COA fields required, special markings, storage/shelf-life.
- Modeled as **typed custom spec attributes** (key/value with datatype + unit + optional tolerance) so new requirements don't need code changes.
- **[OPEN Q-023]** Which customer certifications/compliance regimes apply (food contact, ISO, halal, etc.)?

---

## 4. Versioning & history model [CONFIRMED requirement]

- **Every** spec revision is immutable after APPROVED/ACTIVE. Changes create a **new revision**; the prior becomes SUPERSEDED (never deleted).
- A production batch records the **exact spec revision** it was made to → enables "what spec produced this delivered lot" (reverse traceability).
- Re-orders can target a *specific historical revision* if the customer wants the old version.
- Effective-dated: `valid_from` / `valid_to`, `approved_by`, `approved_at` (UTC + Jalali/Gregorian).

State machine (see also `business-processes.md` §5.3):
```
DRAFT → IN_REVIEW → APPROVED → ACTIVE → SUPERSEDED
                       └→ OBSOLETE
```

**[OPEN Q-024]** What triggers a *new revision* vs. a *minor correction*? Who approves spec changes (technical? customer?)?

---

## 5. Relationship to BOM, artwork, tooling

- Spec revision → drives **BOM revision** (materials/quantities) and **Routing** (which stages).
- Spec's print definition → **Artwork revision** → **Printing tooling** (plates/cylinders) + **color recipe**.
- These are separate but linked lifecycles (a color tweak may bump artwork without changing structure BOM). See `bom-and-routing.md`.

**[OPEN Q-025]** Should artwork changes always force a new *product spec* revision, or can artwork revise independently while the spec stays ACTIVE? (Recommendation: independent, linked by reference.)

---

## 6. Product groups [CONFIRMED]
Cellulose & hygiene · Food packaging · Non-food packaging · General packaging · Shopping bags. Modeled as a **product category** on the customer product (drives defaults: e.g. food → migration/COA requirements).

---

## 7. Assumptions & questions
Questions Q-019…Q-025 (+ Q-014/020, Q-021, Q-022, Q-023). Consolidated in [`open-questions.md`](./open-questions.md).
