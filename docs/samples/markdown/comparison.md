# SLZ Sample Product Comparison

## Scope and Sources

This document compares:

- **Product 1:** `Product Data Sheet - لمینت 3 لایه قهوه لیبارو یک کیلویی بغل گاست عرض 50 سانت.pdf` → `sample-product-01.md`
- **Product 2:** `Product Data Sheet - کیسه پوشک هانیز سایز 3-38 عددی سایز متوسط.pdf` → `sample-product-02.md`

Both source PDFs contain 3 pages and are labeled `Product Data Sheet` / `NSYS`. The comparison is evidence analysis only. It does not change ERP code, models, migrations, or business rules.

Confidence labels used below:

- `CONFIRMED_FROM_PDF` — explicitly visible in a source PDF.
- `INFERRED` — interpretation from context, not an explicit source statement.
- `UNCLEAR` — present but not semantically recoverable from the PDF extraction.
- `NOT_PROVIDED` — not present in the inspected PDF.
- `CONFLICT_REQUIRES_REVIEW` — requires comparison with authoritative ERP requirements; unresolved here.

## 1. Product Overview

| Field | Product 1 | Product 2 |
|---|---|---|
| Product identity | `Customer Product: 50         3` (meaning UNCLEAR) | `Customer Product: 38-3` |
| NSYS Product Code | `14445` | `12975` |
| SP Code | `42102000008225` | `41061300602927` |
| SKU Code | `14445.6059.1` | `12975.3278.1` |
| Product title | `MLTLYRFLM ROLL BOPP/PET/PE TK:117�m PRNT WD:500mm SLBL SLITTED JUMBO:1roll` | `HYGNCBG SHEET PE TK:60�m WHITE PRNT SL:SD HNDL:LNR WD:70mm:TRANS GS:BTN:54mm SPRFRTN RLZC:1 VNT:STR IHL:1 CORONA:1 WKT:42mm WKTHL GRD:LD WD:386mm LNG:352mm BNDL:80pcs-SPNDL CARTON:11 BNDLS` |
| Customer name field | Blank | Blank |
| PDF timestamp | `2026-08-22 21:03:35` | `2026-08-22 21:09:42` |
| Revision/status | NOT_PROVIDED | NOT_PROVIDED |
| Filename-described product | Three-layer Libaro coffee laminate, one kilogram, side gusset, 50 cm width (PDF roll width: 500 mm) | Honey's diaper bag, size 3, 38 count, medium size |
| Filename description confidence | CONFIRMED_FROM_PDF filename; not a populated PDF field | CONFIRMED_FROM_PDF filename; not a populated PDF field |

## 2. Fields Common to Both

The following fields or concepts appear in both PDFs, even where their values differ:

| Common field/concept | Product 1 evidence | Product 2 evidence | Reusable ERP concept? |
|---|---|---|---|
| Product-sheet identity | Product Data Sheet, NSYS | Product Data Sheet, NSYS | Likely reusable document/specification metadata; not a schema conclusion |
| Generated timestamp | Page 1 timestamp | Page 1 timestamp | Likely reusable source-document issue/generated timestamp; date role needs decision |
| Customer-product field | Page 1 | Page 1 | Reusable customer-product identity concept; exact coding policy remains open |
| Internal product code | `14445` | `12975` | Reusable product/customer-product code field; current ERP code is manual and coding derivation is open |
| SP Code | `42102000008225` | `41061300602927` | Reusable external/customer code field, if ownership is confirmed |
| SKU Code | `14445.6059.1` | `12975.3278.1` | Reusable external or ERP SKU field may be needed; derivation is not established |
| Film/web structure | Layer table | Layer table | Ordered material structure is already a confirmed ERP concept in `SpecLayer` |
| Material and material color | BOPP/PET/PE and colors | PE and White | Reusable product-spec layer attributes; current implementation has material and micron, while color treatment may need parameters |
| Thickness | Layer thickness values | PE thickness value | Reusable per-layer thickness with tolerance; current `SpecLayer` supports micron target/tolerance |
| Printing | Print Tech `Classic` | Print Tech `Classic` | Reusable printing process field; present in engineering spec |
| Print side/type | Inside/reverse | Outside/surface | Reusable print-side and print-type fields; current engineering scope supports print side/process |
| Colors | 2 print colors | 7 print colors | Reusable ordered color-slot concept; current `SpecColor` exists, but source-code/Pantone semantics need review |
| Tooling fields | Simple mounting, 2 perimeter, 1 cliché, sleeve 760 | Same except sleeve 780 | Reusable printing-tooling attributes; current tooling asset exists but does not clearly carry all sheet parameters |
| Repeat | 760 mm | 776 mm ±3 | Reusable print-repeat dimension/tolerance |
| Corona | C1 500 for layers A/B/C | C1/CL/CR values for PE | Reusable surface-treatment parameter concept; semantic dictionary is missing |
| Coded dimensional layout | Page-2 BLK helper | Page-2 BLK helper | Reusable parameter-set mechanism is likely; code dictionary and units are not established |
| Pallet requirements | Wooden 110*110; limits | Wooden 110*130; limits | Reusable packaging/pallet specification concept; current execution/packaging representation is incomplete or gated |
| Page-level tolerances | Several coded tolerances | Several coded tolerances | Reusable typed parameter tolerance concept; current `SpecParameter`/quality definition can carry generic values but mapping is unresolved |
| Customer name | Blank | Blank | Field exists in source format; values are NOT_PROVIDED in both samples |
| QC test results | None | None | Absence in both sheets is not evidence that QC execution is unnecessary |
| Named machines/work centers | None | None | Not provided in either PDF; current ERP resource masters cannot be populated from these sheets |
| Revision/status | None visible | None visible | Current ERP has revision/status; source-document linkage and interpretation need review |

Both product sheets therefore provide evidence for the existing ERP principle that packaging products are multi-attribute technical specifications rather than flat names. They do **not** prove that every repeated field should be implemented in one entity or that any field is a BOM line.

## 3. Product 1 Only

| Product 1-specific field/evidence | Source page | Interpretation status | ERP relevance |
|---|---:|---|---|
| Three-layer structure `BOPP / PET / PE` | 1 | CONFIRMED_FROM_PDF | Ordered spec layers; current engineering structure can represent the ordering |
| Layer colors/material states `Transparent`, `Metalized`, `Transparent` | 1 | CONFIRMED_FROM_PDF | May need material-color/appearance fields or typed parameters |
| Layer thicknesses `20 �m`, `12 �m`, `85 �m` | 1 | CONFIRMED_FROM_PDF; glyph UNCLEAR | Per-layer thickness values; current layer target/tolerance fields are relevant |
| Product title total `TK:117�m` | 1 | CONFIRMED_FROM_PDF; sum consistency INFERRED | Total thickness may be a derived/display field, but no decision is made here |
| Solvent-based lamination `A~B` and `AB~C` | 1 | CONFIRMED_FROM_PDF | Explicit pairwise lamination structure is not clearly first-class in current engineering/BOM docs |
| Two colors: White and Black | 1 | CONFIRMED_FROM_PDF | Current `SpecColor` concept appears suitable, subject to code/ink details |
| White is `Spot Ready Ink` with `Internal` coding | 1 | CONFIRMED_FROM_PDF | Color-slot coding/reference field may be needed |
| Reverse print / inside print | 1 | CONFIRMED_FROM_PDF | Current print-side/type fields are relevant |
| Finished roll width 500 mm vs. jumbo width 1220 mm | 1 | CONFIRMED_FROM_PDF | Master/output width distinction may need explicit engineering or routing semantics |
| Roll output target `71.00 Kg`, `1,169.00 m`, `440.00 mm` with ±5% | 3 | CONFIRMED_FROM_PDF | Roll/output specification is currently outside the implemented definition layer |
| Core `3"`, 500 mm length, 102.2 mm external diameter, raw core `11401980` | 3 | CONFIRMED_FROM_PDF | Packaging/core item and dimensional requirement need semantic mapping |
| FirstPack PE sheet title with `TK:13�m`, 600 mm width, 1000 mm length, 150 mm coded gusset | 3 | CONFIRMED_FROM_PDF; code meanings partly UNCLEAR | Product-specific packaging requirement; not confirmed as a consumed BOM line |
| Wooden pallet size 110*110 | 3 | CONFIRMED_FROM_PDF | Product-specific palletization value |
| Pallet 3 rows / 12 max units / 170 cm / 900 Kg | 3 | CONFIRMED_FROM_PDF | Product-specific packing constraints |
| General comment codes `42102000008227 42102000008226` | 3 | CONFIRMED_FROM_PDF; meaning UNCLEAR | Possible edited-roll/source references; no current explicit mapping |

## 4. Product 2 Only

| Product 2-specific field/evidence | Source page | Interpretation status | ERP relevance |
|---|---:|---|---|
| Single PE layer, white, 60 �m ±3 | 1 | CONFIRMED_FROM_PDF; glyph UNCLEAR | Current ordered layer concept is relevant |
| Seven print colors | 1 | CONFIRMED_FROM_PDF | Current `SpecColor` concept is relevant |
| Process colors Cyan, Magenta, Yellow | 1 | CONFIRMED_FROM_PDF | Current color/ink material concept is relevant |
| Spot codes `266 C`, `honeys gold`, blank Pantone, Internal | 1 | CONFIRMED_FROM_PDF; field placement partly UNCLEAR | Pantone/reference-code and internal-code semantics need review |
| Surface/outside print | 1 | CONFIRMED_FROM_PDF | Current print-side/type fields are relevant |
| Roll/jumbo width 770 mm ±5 | 1 | CONFIRMED_FROM_PDF | Product-specific width constraint |
| Repeat 776 mm ±3 and sleeve 780 mm | 1 | CONFIRMED_FROM_PDF | Product-specific print tooling/geometry constraints |
| Corona parameters `C1 578`, `CL 117`, `CR 75`, each ±5 | 2 | CONFIRMED_FROM_PDF | Zone/parameter semantics not currently clear |
| Coded title features: liner handle, bottom gusset, perforation/return, vent/structure, IHL, WKT | 1 | CONFIRMED_FROM_PDF; meanings UNCLEAR | Demonstrates need for typed/custom technical parameters and a confirmed code dictionary |
| Page-3 converting matrix with codes V through P | 3 | CONFIRMED_FROM_PDF; meanings/units UNCLEAR | Detailed converting geometry is not clearly represented by current generic routing header |
| `Handle: Yes` | 3 | CONFIRMED_FROM_PDF | Product-specific conversion feature |
| `Slit` with adjacent `17` | 3 | CONFIRMED_FROM_PDF text; association UNCLEAR | Requires semantic confirmation before modeling |
| Bundle `80pcs` | 1 | CONFIRMED_FROM_PDF; role partly UNCLEAR | Packaging hierarchy field may be needed |
| Carton `11 BNDLS` | 1 | CONFIRMED_FROM_PDF; role partly UNCLEAR | Packaging hierarchy field may be needed |
| Wooden pallet size 110*130 | 3 | CONFIRMED_FROM_PDF | Product-specific palletization value |
| Pallet 6 rows / 60 max units / 160 cm / 900 Kg | 3 | CONFIRMED_FROM_PDF | Product-specific packing constraints |
| `Plastic` in pallet table | 3 | CONFIRMED_FROM_PDF; column association UNCLEAR | Packaging-component field needs semantic mapping |

## 5. Structural Differences

| Area | Product 1 | Product 2 |
|---|---|---|
| Product form | Roll product / slitted jumbo roll according to title | Sheet/bag converting product according to title and converting page |
| Material architecture | Three ordered layers | One listed PE layer |
| Thickness | 20, 12, and 85 micron-text values; total 117 in title | 60 micron-text value with ±3 tolerance |
| Lamination | Explicit two solvent-based lamination links | No lamination listed |
| Printing | 2 colors, reverse/inside | 7 colors, surface/outside |
| Conversion detail | Mostly roll/core/packing requirements; no explicit handle | Detailed coded converting matrix and handle flag |
| Packaging unit | Roll, core, FirstPack, pallet | Bundle/carton language, pallet |
| Product-specific measurement density | Moderate, concentrated in roll/lamination data | High, concentrated in converting geometry and tolerances |

## 6. Material Differences

- Product 1 uses `BOPP / PET / PE`, with BOPP transparent, PET metalized, and PE transparent. All three layer entries are `CONFIRMED_FROM_PDF` on page 1.
- Product 2 uses one listed `PE` layer, white, with `60 �m` and `+3/-3` tolerance. This is `CONFIRMED_FROM_PDF` on page 1.
- Product 1 explicitly names solvent-based lamination between A~B and AB~C. Product 2 has no lamination entry.
- Neither PDF gives resin grade, supplier, lot, ink quantity, adhesive grade, coat weight, or raw-material quantity sufficient to form a verified execution BOM.
- The existing ERP catalog distinguishes material subtypes, but these PDFs alone do not establish whether each layer, ink, core, or packaging title is an item master, a spec-layer reference, or an execution consumption line.

## 7. Process Differences

| Process area | Product 1 | Product 2 |
|---|---|---|
| Printing | Classic; reverse/inside; 2 colors; sleeve/repeat 760 | Classic; surface/outside; 7 colors; sleeve 780; repeat 776 ±3 |
| Lamination | A~B solvent based; AB~C solvent based | NOT_PROVIDED |
| Slitting | `SLITTED` in title | `Slit` with adjacent value `17`, meaning UNCLEAR |
| Converting | FirstPack/core requirements and roll output; specific conversion stage not fully stated | Explicit `Converting` section; handle yes; many coded geometry values |
| Roll output | Weight, length, diameter, core weight | Roll widths and printing dimensions; no roll weight/length/diameter table |
| Packing | Wooden 110*110 pallet; 3 rows; 12 units; 170 cm max height | Wooden 110*130 pallet; 6 rows; 60 units; 160 cm max height |
| Machines/work centers | NOT_PROVIDED | NOT_PROVIDED |

The high-level interpretations `printing → lamination → slitting → roll packing` for product 1 and `printing → converting → palletizing` for product 2 are **INFERRED** from sheet fields. Neither sheet provides a complete confirmed routing with sequence numbers, machine assignment, setup/run data, or execution results.

## 8. QC Differences

| QC/specification area | Product 1 | Product 2 |
|---|---|---|
| Thickness evidence | 20/12/85 micron-text values; no explicit per-layer tolerance shown | 60 micron-text value with ±3 |
| Width/repeat tolerances | Coded page-2 ±1 values; roll dimensions ±5% | Roll width ±5; repeat ±3; page-2/page-3 coded tolerances |
| Corona | `C1 500` per layer helper | `C1 578`, `CL 117`, `CR 75`, each ±5 |
| Appearance/material criteria | Transparent, metalized, matte/gloss, sealable, corona | White, matte, sealable, corona |
| Print/color criteria | White and Black; no ΔE/registration limit | 7 slots; Pantone/internal codes; no ΔE/registration limit |
| QC method/sampling/results | NOT_PROVIDED | NOT_PROVIDED |
| Strength/seal tests | NOT_PROVIDED | NOT_PROVIDED |

The repeated presence of tolerances is evidence that product-specific quality limits matter. It is **not** evidence that either sheet contains a complete quality plan or that a particular sampling method should be implemented.

## 9. Packaging Differences

- Product 1 is packaged as rolls: core requirements, roll weight/length/diameter, core weight, FirstPack coded requirement, and a wooden 110*110 pallet. Its pallet limits are 3 rows, 12 maximum units, 170.00 cm maximum height, and 900.00 Kg maximum weight.
- Product 2 includes product-title bundle/carton values (`80pcs`, `11 BNDLS`) and a wooden 110*130 pallet. Its pallet limits are 6 rows, 60 maximum units, 160.00 cm maximum height, and 900.00 Kg maximum weight.
- Product 1 shows `Cardboard` in the pallet table; product 2 shows `Plastic`. The exact pallet-component column association is `UNCLEAR` in the text extraction.
- Neither product provides a complete bilingual label, barcode, carton dimensions, pallet label, shipment label, or delivery-document definition.

## 10. Customer/Product-Specific vs. Potentially Reusable Concepts

### Appears customer/product-specific

These values vary directly between the samples or describe one product's physical design:

- Product codes, SP Codes, SKU Codes, customer-product values, and source timestamps.
- Layer count and layer sequence.
- Material/color/appearance and thickness values.
- Lamination presence and pair sequence.
- Print side, print type, number of colors, color names/codes, sleeve, repeat, and roll widths.
- Coded converting dimensions and feature flags such as `Handle: Yes`.
- Roll targets and tolerances.
- Core/FirstPack requirements.
- Bundle/carton quantities.
- Pallet size, rows, maximum units, maximum height, maximum weight, and pallet-component material.

These are evidence of per-product specification data. They are not automatically global master data or global defaults.

### Appears potentially reusable as an ERP concept

These concepts occur in both sheets or align with existing SLZ documentation:

- Customer-specific product identity separate from technical revision.
- Internal product code plus external/customer code(s).
- Versioned specification metadata with issue/effective date and status, subject to source-document mapping.
- Ordered material layers with per-layer thickness and tolerance.
- Material appearance/color/treatment attributes.
- Print definition: process, side/type, color slots, ink family, reference coding, repeat, sleeve, cliché count, and plate mounting.
- Lamination pair sequence and lamination type, when applicable.
- Generic typed specification parameters with unit and tolerance for coded dimensions/features.
- Converting operation definition separated from engineering values and execution confirmations.
- Roll/output packaging specification, bundle/carton hierarchy, palletization constraints.
- Product-specific quality characteristics and tolerances linked to a versioned quality plan.
- Source PDF/document attachment with page-level evidence and revision/effectivity linkage.

These are candidate concepts for future analysis, not schema decisions. The current ERP source of truth remains authoritative.

## 11. Potential ERP Gaps Across the Two Sheets

| Evidence in one or both PDFs | Possible ERP concept | Current representation | Apparent gap | Confidence | Business decision required? |
|---|---|---|---|---|---|
| Dense coded titles and coded page-2/page-3 dimensions | Canonical technical-parameter dictionary with code, label, unit, datatype, tolerance | `SpecParameter` is typed/extensible, but no source-system code dictionary is documented | Semantics and units of source codes cannot be reliably represented as meaningful ERP data without a dictionary | CONFIRMED_FROM_PDF / UNCLEAR | YES |
| Product codes, SP Codes, SKU Codes, customer-product values | Multiple identifiers with source/ownership/type | CustomerProduct manual code exists; coding derivation remains open | Identifier roles and derivation/numbering rules are not resolved | CONFIRMED_FROM_PDF | YES |
| Layer material color/appearance, sealability, corona, chemical treatment | Layer treatment/attribute structure | `SpecLayer` has material, micron target, tolerance; free parameters exist | No clearly dedicated documented fields for all layer treatments and surface properties | CONFIRMED_FROM_PDF | YES |
| Print colors include process/spot/internal coding and named Pantone values | Versioned color recipe/reference-code model | `SpecColor` exists with ink material, alternative, coverage, ΔE tolerance | Source coding, Pantone/name/reference fields and exact slot semantics are not clearly complete | CONFIRMED_FROM_PDF | YES |
| Lamination pairs and solvent-based type in product 1 | Pairwise layer bonding/lamination operations with adhesive details | BOM/routing operations are generic; engineering spec has lamination flag | Pair sequence, adhesive type/grade, coat weight, cure requirements not clearly represented | CONFIRMED_FROM_PDF | YES |
| Product 1 roll weight/length/diameter/core; product 2 bundle/carton/pallet values | Product-specific packaging and output-unit specification | Packaging material subtype and generic products exist; execution packaging is deferred | No clearly complete packaging hierarchy/constraint model tied to a spec revision | CONFIRMED_FROM_PDF | YES |
| Dozens of dimensional tolerances | Toleranced spec parameters and quality characteristics | `SpecParameter` and quality-plan item limits exist; check execution is gated | Mapping PDF dimensions to named ERP characteristics and methods is unresolved | CONFIRMED_FROM_PDF | YES |
| Product 2 handle/converting geometry and product 1 roll/slit details | Converting-specific engineering definition linked to routing | Routing operations have generic setup/run fields; execution is gated | No confirmed semantic model for feature geometry, handles, slits, and coded dimensions | CONFIRMED_FROM_PDF / UNCLEAR | YES |
| No machine/work-center information in either sheet | Product-to-capability or operation resource qualification | WorkCenter/Machine masters and free-form capability profiles exist | These samples cannot populate resource assignment; no gap in the PDFs themselves | NOT_PROVIDED | NO |
| No measured QC result or sampling evidence | Quality execution records | Quality definition layer exists; execution is gated on Q-046 and related decisions | Cannot infer actual inspection workflow from these sheets | NOT_PROVIDED | YES |
| No actual lot, roll genealogy, scrap, downtime, or production confirmation | Execution traceability and manufacturing transactions | Explicitly gated/not implemented | Evidence sheets are definitions, not execution records; no direct conflict | NOT_PROVIDED | YES |

## 12. Conflicts Requiring Review

1. `CONFLICT_REQUIRES_REVIEW`: Both sheets include identifiers called `SKU Code`, but the current ERP documentation records the SKU/product-coding derivation scheme as open (`Q-019` / `NQ-005`) and implements the customer-product code manually. The observed codes must not be treated as proof of a derivation algorithm.
2. `CONFLICT_REQUIRES_REVIEW`: Both sheets expose material layers and packaging requirements, but the ERP source of truth distinguishes ordered specification layers from BOM lines and leaves inventoried BOM levels/open execution semantics unresolved (`Q-026`). The PDFs do not resolve that distinction.
3. `CONFLICT_REQUIRES_REVIEW`: Both sheets show many operational dimensional values, but neither supplies a complete routing, named machines, actual production quantities, or measured QC results. The sheets must not override the ERP source-of-truth boundaries that keep execution and traceability gated.

## 13. Questions Raised By The Comparison

- Is the NSYS product-sheet format itself a controlled source document whose timestamp should link to a specific product-specification revision?
- Are the same coded fields (`BLK`, `A`, `B1`, `H1`, `K1`, `K2`, `R1`, `R2`, `D1`, `D2`, `D4`) shared across products, and where is their authoritative dictionary?
- Are product-1 roll/core constraints and product-2 bundle/carton constraints two variants of one packaging-specification concept, or separate packaging workflows?
- Which identifiers are customer-owned, which are NSYS-owned, and which are ERP-generated?
- Are layer treatment values such as `Corona`, `Chemical`, `Sealable`, `Matte`, and `Gloss` controlled vocabularies, free text, or measured/specification values?
- Are print color rows intended to become reusable color/ink master data, or are they revision-specific print slots only?
- Which PDF values are specification targets, which are packing instructions, and which are actual production limits?
- Should coded converting values be retained verbatim alongside any future normalized interpretation?
- Do both products require a product-specific quality plan, and which named characteristics/methods/sampling rules apply?
- Are roll output data and bundle/carton data captured before production, after production, or both?
- Does either product require lot/roll serialization and genealogy at execution time? The PDFs do not answer this; the source-of-truth gate `Q-046` remains authoritative.

## 14. Existing ERP Concepts Relevant to Both

The current documentation already describes or implements these related concepts:

- `CustomerProduct` as a customer-specific stable identity.
- `SpecificationRevision` with immutable active/superseded history.
- Ordered `SpecLayer` rows with material, micron target, and tolerance.
- `SpecColor` rows with ink material, alternative ink, coverage, and ΔE tolerance.
- `SpecParameter` for typed extensible values with units/tolerances.
- Versioned BOM and Routing definitions bound to a specification revision.
- WorkCenter and Machine masters with free-form capability profiles.
- Versioned QualityPlan and QualityPlanItem definitions.
- Catalog `Material` subtypes including ink, packaging, semi-finished, finished, and other categories.
- Generic document attachments and audit/versioning foundations.

The following remain explicitly incomplete or gated according to the current documentation: source-code derivation, artwork lifecycle, lamination/printing tooling detail beyond current fields, packaging hierarchy, stock/roll/lot genealogy, QC execution/results, production confirmations, and complete shipment/fulfilment semantics.

## 15. Conclusion

The two sheets are compatible evidence for a customer-specific, versioned flexible-packaging product specification, but they describe materially different product shapes:

- Product 1 is a laminated three-layer roll with solvent-based layer bonding and roll/core/pallet constraints.
- Product 2 is a single-layer PE printed diaper-bag product with seven-color surface printing, detailed converting dimensions, a handle flag, bundle/carton information, and different pallet constraints.

The PDFs strengthen the case for preserving exact source fields, ordered layers, per-field tolerances, print-slot coding, conversion geometry, and packaging constraints. They do not settle the open SLZ decisions about SKU derivation, BOM semantics, execution traceability, QC execution, code dictionaries, or business ownership. No ERP implementation decision is made here.
