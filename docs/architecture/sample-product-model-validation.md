# SLZ Sample Product Model Validation

**Date:** 2026-08-22
**Scope:** Definition-layer validation against the two extracted real SLZ sample product sheets.
**Sources:** `docs/samples/markdown/sample-product-01.md`, `sample-product-02.md`, `comparison.md`, `docs/SLZ-SOURCE-OF-TRUTH.md`, `docs/PROJECT-STATUS.md`, `docs/business-decision-package.md`, and the relevant engineering/manufacturing/product-model architecture documents.

This is a validation record, not a schema decision. The sample PDFs are real product evidence, but they do not override the SLZ source of truth or resolve open business gates.

## Classification Legend

| Classification | Meaning |
|---|---|
| `DIRECTLY REPRESENTABLE` | Existing field/model stores the value without reinterpretation. |
| `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Existing generic or data-driven structure can preserve it, usually as a typed `SpecParameter`, material master value, quality-plan value, or attachment metadata. The source value must remain raw when its meaning is uncertain. |
| `REQUIRES MODEL GAP` | No appropriate semantic home exists in the current model. A raw parameter fallback may preserve evidence, but it does not provide a usable domain representation. |
| `BUSINESS-DECISION-GATED` | Representation depends on an unresolved SLZ decision and must not be implemented as policy. |
| `SOURCE DATA AMBIGUOUS` | The PDF contains a value, but its meaning, unit, column association, or ownership cannot safely be determined. |

## Current Model Inventory

| Concern | Current implementation | Validation consequence |
|---|---|---|
| Customer | `partners.Partner`, company-scoped, customer/supplier role flags | A populated customer can be linked directly; both sample PDF customer fields are blank. |
| Customer product identity | `engineering.CustomerProduct`, stable customer-specific root with manual `code` | Fits the confirmed identity-vs-revision model. The PDF's internal product code can be entered manually; SKU derivation remains open. |
| Specification | There is no standalone `Specification` model. `engineering.SpecificationRevision` is the implemented versioned specification record linked to `CustomerProduct`. | Do not create a duplicate `Specification` concept. |
| Revision | `core.versioning.Revision`: DRAFT → ACTIVE → SUPERSEDED/ARCHIVED, immutable after activation | Directly represents revision mechanics, but neither PDF contains a revision/status value. |
| Structure layers | Ordered `engineering.SpecLayer` rows with material, function, micron, and low/high micron tolerances | Directly represents ordered BOPP/PET/PE and PE layer structure. |
| Print colors | Ordered `engineering.SpecColor` rows with color name, ink/alternative ink, coverage, and ΔE tolerance | Directly represents color slots and ink material links. Pantone/internal source coding and ink-family labels have no dedicated fields. |
| Generic specification attributes | Typed `engineering.SpecParameter` rows with text/number/bool value, unit, and low/high tolerance | Safe preservation path for coded customer fields, layer treatments, corona values, packaging values, and source-system strings. It does not give those values a semantic domain model. |
| Tooling | `engineering.ToolingAsset`: cliché/sheet/set identity, customer/product link, lifecycle, usage-life, optional cliché warehouse | Represents tooling identity and life master data. It does not represent all print-job parameters or automatic usage capture. |
| BOM | Versioned `manufacturing.BillOfMaterials` / `BomRevision` / `BomLine` bound to a specification revision; quantities and UoM are present; output material optional | Can represent an authored BOM, but the PDFs do not establish that their layer/product-requirement tables are BOMs. Q-026 keeps inventoried levels open. |
| Routing | Versioned `manufacturing.Routing` / `RoutingRevision` / `RoutingOperation`, work center, optional output material, setup/run-rate data | Can represent an authored route. The PDFs do not provide a complete confirmed route or machine assignment. |
| Machines and capabilities | Company/site-scoped `Machine` with free-form `capability_profile` JSON | Safe data-driven home for confirmed machine capability data when supplied; neither PDF names a machine. |
| Materials | Company-scoped `catalog.Material` with subtype including resin, ink, solvent, packaging, semi-finished, finished | Directly represents identifiable materials, but the PDFs do not provide grades, quantities, lots, or BOM semantics. |
| UoM | `catalog.UnitOfMeasure` and same-dimension `UomConversion` | Supports mm, m, kg, pieces, rolls, cartons, and pallets if configured. The exact micron/roll/bundle unit strategy is not resolved by the PDFs. |
| Quality definition | Versioned `quality.QualityPlan` / items with characteristics, methods, limits, units, sampling text | Can represent authored product-specific QC plans. The PDFs contain no measured results or sampling method; execution is gated. |
| Documents | Generic `documents.Attachment` with filename, description, checksum, and target entity | Can attach the source PDF to a customer product/specification, but does not provide field-level/page-level provenance metadata. |
| Audit | Platform audit trail for audited mutations and lifecycle transitions | Covers future sample-data writes; no sample records are created in this task. |

## Product 1 — Three-Layer Laminate Roll

Source: `sample-product-01.md`; all page references below refer to the source PDF.

| PDF field/evidence | Current target | Classification | Validation |
|---|---|---|---|
| Customer Name blank | `partners.Partner` | `SOURCE DATA AMBIGUOUS` | The customer entity exists, but the PDF does not identify one. Do not infer the customer from the filename. |
| Customer Product `50         3` | `CustomerProduct.code` or parameter | `SOURCE DATA AMBIGUOUS` | The value is visible but its field semantics are not recoverable. Preserve raw if captured; do not assign it to code, size, or variant. Page 1. |
| NSYS Product Code `14445` | `CustomerProduct.code` | `DIRECTLY REPRESENTABLE` | Existing code is manual by design. Ownership as internal/customer code must remain documented. Page 1. |
| SP Code `42102000008225` | No dedicated alternate-identifier field | `BUSINESS-DECISION-GATED` | A second identifier is real evidence, but identifier ownership and coding scheme are open under Q-019/NQ-005. Preserve as a raw parameter or attachment note until decided. Page 1. |
| SKU Code `14445.6059.1` | No dedicated alternate-identifier field | `BUSINESS-DECISION-GATED` | Current source of truth says SKU/dependent-parameter derivation is system-owned, while implementation keeps `CustomerProduct.code` manual. Do not implement derivation from this sample. Page 1. |
| Product title and `JUMBO:1roll` | `CustomerProduct` name + `SpecificationRevision` fields/parameters | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Store the exact title as the product/spec name or a text parameter; do not parse abbreviations into authoritative fields. Page 1. |
| Timestamp `2026-08-22 21:03:35` | Revision effective dates or attachment metadata | `SOURCE DATA AMBIGUOUS` | Existing revision dates are lifecycle dates; the PDF does not state whether this is issue, print, or effective time. Preserve as source-document metadata/parameter, not as `effective_from`. Page 1. |
| Roll format / slitted jumbo | `SpecificationRevision.spec_format=ROLL_STOCK` | `DIRECTLY REPRESENTABLE` | The format is supported; `SLITTED` remains a raw title/process value. Page 1. |
| Roll width `500 mm` | `SpecificationRevision.width_mm` | `DIRECTLY REPRESENTABLE` | Existing dimensional field. Page 1. |
| Jumbo roll width `1220 mm` | No dedicated master-vs-output width field | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Preserve as a typed parameter such as the exact source key/value. Do not overload finished width. Page 1. |
| Repeat `760 mm` and sleeve `760 mm` | No dedicated repeat/sleeve fields | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Typed numeric parameters with units are supported; print-job semantics remain raw. Page 1. |
| Opening direction `Outside` | No dedicated field | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Preserve as a text parameter; no confirmed core field exists. Page 1. |
| Plate mounting `Simple`, perimeter `2`, cliché count `1`, `FG UPS 1` | `ToolingAsset` plus spec parameters | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Tooling identity is first-class; job-specific values belong in parameters until tooling/print semantics are confirmed. `FG UPS` is additionally ambiguous. Page 1. |
| Layers A/BOPP/Transparent/20 �m, B/PET/Metalized/12 �m, C/PE/Transparent/85 �m | Ordered `SpecLayer` | `DIRECTLY REPRESENTABLE` | Material, sequence, color text, and micron target fit. The extracted micron glyph remains uncertain. Page 1. |
| Layer thickness total `TK:117�m` | `SpecParameter` or derived presentation | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Store raw total if needed; the equality to 20+12+85 is only an inferred consistency check and must not become an authoritative calculation without policy. Page 1. |
| Reflection, sealability, corona, chemical values | Layer-specific treatment semantics | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Use typed parameters keyed to the exact raw source labels/values because table-column association is uncertain. There is no safe dedicated normalization. Pages 1-3. |
| Lamination `A~B Solvent Based`, `AB~C Solvent Based` | `has_lamination` plus parameters | `REQUIRES MODEL GAP` | The boolean header records presence only; no current child structure represents pair sequence or lamination process per interface. Raw `SpecParameter` preserves evidence but is not a semantic lamination model. Page 1. Dedicated modeling must not invent adhesive/cure semantics absent from the sheet. |
| Two print colors White/Internal and Black/Process Ready Ink | `SpecColor` | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Ordered color rows and ink material links fit. Ink material records must be configured as subtype INK. Page 1. |
| Print technology `Classic` | `SpecificationRevision.print_process` | `SOURCE DATA AMBIGUOUS` | Current choices are `NONE`, `FLEXO_SURFACE`, `FLEXO_REVERSE`; the PDF's `Classic` is not safely equivalent to a process enum. Preserve exact text in a parameter. Page 1. |
| Print side `Inside`, print type `Reverse` | `print_process=FLEXO_REVERSE` or parameter | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Reverse/surface is a confirmed architecture concept, but the PDF's exact `Inside`/`Reverse` pair should remain raw alongside any configured enum. Page 1. |
| Print layout `[BOPP Transparent 20�m Reverse]` | `SpecParameter` and `SpecLayer` | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Preserve exact layout string; do not parse it into a second layer or artwork model. Page 1. |
| `BLK11`/`BLK12` coded dimensions and ±1 values | `SpecParameter` | `SOURCE DATA AMBIGUOUS` | Values and tolerances can be stored with raw keys, but code meanings and units are absent. Page 2. |
| Corona helper `C1 500` for A/B/C | Layer-scoped `SpecParameter` | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Numeric value and raw code can be retained; characteristic/unit meaning remains unclear. Pages 2-3. |
| Product Requirements Core and FirstPack exact titles; amounts `0.00`, units/operations blank | `SpecParameter`, material master, attachment | `SOURCE DATA AMBIGUOUS` | Exact strings fit parameters; amount semantics and whether these are BOM/packaging lines are not established. Page 3. |
| Roll weight `71.00 Kg ±5%`, length `1,169.00 m ±5%`, diameter `440.00 mm ±5%`, core weight `1.50 Kg` | `SpecParameter` / quality definition | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Typed numeric values and tolerances are supported. Roll execution/serialization remains Q-046 gated. Page 3. |
| Core title and raw core `11401980` | `catalog.Material` subtype PACKAGING plus parameter | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | A core material can be configured, but title codes and dimensions do not establish a complete item master. Page 3. |
| Pallet `110*110 WOODEN`, rows `3`, max units `12`, height `170.00 cm`, weight `900.00 Kg`, `Cardboard` | Packaging parameters/material master | `REQUIRES MODEL GAP` | Exact values can be preserved as parameters, but there is no semantic product packaging hierarchy or pallet-constraint model. `Cardboard` column association is unclear. Page 3. |
| QC tolerances and appearance values | `QualityPlan` / `QualityPlanItem` plus parameters | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Plan definitions support characteristics/limits, but method/sampling/results are not in the PDF; execution is gated by Q-039/Q-040/Q-046. Pages 1-3. |
| Machines/work centers, actual quantities, lots, genealogy, production results | Manufacturing/inventory execution | `BUSINESS-DECISION-GATED` | Not provided by the PDF and blocked by Q-026/Q-046/Q-048/Q-049. Do not fabricate. |

## Product 2 — Printed PE Diaper Bag

Source: `sample-product-02.md`; all page references below refer to the source PDF.

| PDF field/evidence | Current target | Classification | Validation |
|---|---|---|---|
| Customer Name blank | `partners.Partner` | `SOURCE DATA AMBIGUOUS` | No customer can be safely selected from the PDF. |
| Customer Product `38-3` | `CustomerProduct.code` | `DIRECTLY REPRESENTABLE` | Existing customer-product identity can hold the value, subject to confirming ownership. Page 1. |
| NSYS Product Code `12975` | `CustomerProduct.code` | `DIRECTLY REPRESENTABLE` | Manual internal code field exists. Page 1. |
| SP Code `41061300602927`, SKU `12975.3278.1` | Alternate identifiers | `BUSINESS-DECISION-GATED` | Same Q-019/NQ-005 boundary as product 1. Preserve exact values as raw parameters only until identifier policy is confirmed. Page 1. |
| Product title and coded features | Customer product/spec name plus parameters | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Preserve the complete exact title. Do not infer meanings for `SL:SD`, `HNDL:LNR`, `SPRFRTN`, `RLZC`, `VNT:STR`, `IHL`, `WKT`, or `WKTHL`. Page 1. |
| Sheet/bag format, width `770 mm ±5`, repeat `776 mm ±3`, sleeve `780 mm` | `SpecificationRevision` header plus parameters | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Existing `SHEET` format and width/tolerance fields fit. Repeat and sleeve require parameters. Page 1. |
| Single PE/White/60 �m ±3 layer | Ordered `SpecLayer` | `DIRECTLY REPRESENTABLE` | Existing layer and micron tolerance fields fit. Page 1. |
| Seven color slots, Cyan/Magenta/Yellow, Pantone `266 C`, `honeys gold`, blank Pantone, Internal | `SpecColor` plus parameters | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Color rows fit; reference-code and ink-family semantics are not dedicated. `326 C`/`317 C` placement is partly uncertain. Page 1. |
| Print technology `Classic` | `print_process` | `SOURCE DATA AMBIGUOUS` | Do not map `Classic` to a process enum without confirmation. Preserve exact text. Page 1. |
| Print side `Outside`, print type `Surface` | `print_process=FLEXO_SURFACE` or parameter | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Surface/outside is a confirmed architecture concept; preserve raw values. Page 1. |
| Plate mounting `Simple`, perimeter `2`, cliché count `1`, sleeve `780`, repeat `776` | Tooling plus parameters | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Existing tooling identity and generic parameters are sufficient for evidence preservation. Page 1. |
| Page-2 `BLK11`/`BLK12` dimensions and individual tolerances | `SpecParameter` | `SOURCE DATA AMBIGUOUS` | Raw values/tolerances fit, but the parameter dictionary and units are absent. Page 2. |
| Corona `C1 578 ±5`, `CL 117 ±5`, `CR 75 ±5` | Layer-scoped `SpecParameter` / quality characteristic | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Preserve exact codes and tolerances. Their physical meanings are not established. Page 2. |
| Converting codes V, M, M1…P and tolerances | `SpecParameter` | `SOURCE DATA AMBIGUOUS` | Existing typed parameters preserve values; no safe interpretation of code meanings or units. Page 3. |
| `Handle: Yes` | `SpecParameter` or future converting feature | `REQUIRES MODEL GAP` | The generic parameter bag preserves the fact, but no semantic converting-feature field exists. A dedicated feature model requires a confirmed code/operation vocabulary. Page 3. |
| `Slit 17` | Parameter/routing | `SOURCE DATA AMBIGUOUS` | The label/value association and unit are unclear. Do not create a slit quantity/width field. Page 3. |
| Bundle `80pcs`, carton `11 BNDLS` | Packaging parameters | `REQUIRES MODEL GAP` | Exact values fit raw parameters, but bundle/carton hierarchy is not a current semantic model. Page 1. |
| Pallet `110*130 WOODEN`, rows `6`, max units `60`, height `160.00 cm`, weight `900.00 Kg`, `Plastic` | Packaging parameters/material master | `REQUIRES MODEL GAP` | Same packaging-hierarchy gap as product 1; `Plastic` field association is unclear. Page 3. |
| QC limits, thickness, width/repeat and corona tolerances | Quality plan definition | `REPRESENTABLE WITH EXISTING MODEL + CONFIGURATION` | Quality-plan definitions can carry named characteristics and limits once SLZ supplies methods/sampling. Execution remains gated. Pages 1-3. |
| Machines, actual quantities, lots, genealogy, production results | Execution layer | `BUSINESS-DECISION-GATED` | Not provided and blocked by Q-026/Q-046/Q-048/Q-049. |

## Cross-Model Findings

### Strong Fit

1. **Customer-specific versioned product identity** is the correct abstraction. Both sheets have stable product identifiers and dense revision-sensitive technical attributes; a flat `catalog.Product` would lose important engineering context.
2. **Ordered layer structure** is a strong direct fit. Product 1's three-layer BOPP/PET/PE structure and product 2's single PE layer can be represented by `SpecLayer` without turning layers into a BOM.
3. **Typed parameters with tolerances** are an appropriate confirmed escape hatch. They preserve exact customer/system codes and values while avoiding invented enums for unresolved SLZ vocabulary.
4. **Material subtypes, UoM, quality-plan definitions, tooling identity, BOM/routing revisions, attachments, and audit** all have existing architectural homes.
5. **No sample requires execution data** to validate the definition layer. The absence of lots, rolls, genealogy, confirmations, measured QC, and production quantities is consistent with the PDFs being product sheets rather than execution records.

### Structural Weaknesses

| Weakness | Current state | Severity | Safe action now |
|---|---|---|---|
| Alternate identifier ownership | Only one manual `CustomerProduct.code`; SP/SKU roles are unresolved | High, but gated | Preserve raw identifiers in parameters/source attachment; resolve Q-019/NQ-005 before first-class coding changes. |
| Pairwise lamination | Only `has_lamination` exists | Medium | Document as a semantic model gap; do not invent adhesive/cure fields. Raw parameters remain available. |
| Print color reference metadata | `SpecColor` lacks source coding/reference and ink-family fields | Medium | Preserve exact source values in parameters; a dedicated extension should follow a confirmed field dictionary. |
| Layer treatments | No dedicated layer appearance/corona/chemical/sealability fields | Medium | Use layer-scoped parameters because source table association is ambiguous. |
| Packaging hierarchy | No bundle/carton/pallet constraint structure | High for fulfilment, not definition-only blocker | Preserve exact packaging values in parameters/attachments; dedicated packaging model needs business confirmation and interacts with Q-026/Q-049. |
| Converting feature vocabulary | No semantic handle/slit/code dictionary | Medium | Preserve raw coded parameters; do not create fields from unexplained codes. |
| Source provenance | Attachment stores the PDF but not page/field provenance | Low/medium | Validation Markdown provides provenance now; controlled-document/field provenance policy remains open. |
| Detail UI readability | Existing page showed raw FK UUIDs and omitted several existing tolerance/color fields | Safe UI gap | Implemented in this milestone using existing APIs and fields only. |

### Fields With No Appropriate Semantic Home Today

The following can be preserved as raw `SpecParameter` values or a source-PDF attachment, but that is not the same as having a domain representation:

- SP Code and SKU Code as typed alternate identifiers with ownership/source.
- Pairwise lamination sequence and process/adhesive details.
- Per-color ink family, coding type, Pantone/reference code, and raw source code.
- Per-layer reflection, sealability, corona, and chemical-treatment structure.
- Bundle → carton → pallet packaging hierarchy and constraints.
- Handle/slit/converting feature definitions and the source-system code dictionary.
- PDF page/field provenance linked to individual parameter values.

These are not implemented as new models in this milestone because their safe shape is affected by Q-019, Q-024, Q-026, Q-039/Q-040, Q-046/Q-049, and the unresolved source-system vocabulary. Creating guessed fields would make the samples appear complete while damaging traceability.

## BOM, Routing, Tooling, and Master-Data Boundary

### BOM

Neither PDF proves that its layer table, core, FirstPack, bundle, or pallet rows are a BOM. `BomLine` requires a material, quantity, UoM, and optional consumption basis; the samples provide no reliable quantities or BOM semantics. Do not load these rows into BOMs automatically. Q-026 and Q-027 remain authoritative.

### Routing

Product 1 visibly includes lamination and slitting-related information; product 2 visibly includes converting and handle information. These are evidence of product requirements, not a complete route with confirmed sequence, work center, machine, setup, run rate, or output. `RoutingOperation` can represent a manually authored route after confirmation; no route fixture is safe now.

### Tooling

Both sheets contain tooling-adjacent values: plate mounting, cliché count, perimeter, sleeve, and repeat. `ToolingAsset` safely represents the physical cliché/sheet/set identity and usage-life only. Job-specific print parameters should remain linked specification data until artwork/tooling linkage and cost policy are confirmed.

### Materials and UoM

BOPP, PET, PE, ink, core/cardboard, and packaging references can map to `catalog.Material` subtypes when a human-authorized master record exists. The PDFs do not provide enough information to create authoritative material masters: customer ownership, grade, supplier, base UoM, and quantities are missing or coded. Micron values can be retained as numeric parameters with the exact source unit text; no new UoM normalization is inferred.

## Safe Implementation Decision

No backend model, migration, RBAC, fixture, or seed-data change is safe and necessary from these samples alone. The existing model intentionally provides a raw, typed parameter path for unresolved customer-specific attributes, and the remaining semantic gaps depend on business or source-system decisions.

A safe frontend correction is appropriate: the Customer Product detail screen now exposes existing tolerance fields, layer tolerances, color alternatives/ΔE, parameter datatype/value details, and human-readable FK labels. This improves validation without changing domain behavior.

## Business-Gated Items Left Untouched

- Q-019/NQ-005: product/SKU/alternate-identifier coding and derivation.
- Q-024: what changes create a new specification revision and who approves it.
- Q-026: which intermediates are real BOM/inventory levels.
- Q-027 and Q-016/042: BOM consumption bases, waste, and scrap policy.
- Q-039/Q-040: quality methods and sampling rules.
- Q-046: roll serialization vs. lot/count and all execution traceability.
- Q-048: explicit issue vs. backflush.
- Q-049: roll/pallet/carton traceability granularity.
- Q-053/Q-055: role catalogue and company/site visibility scoping.
- Q-004/036 and costing cluster: tooling cost and valuation/costing policy.

## Validation Verdict

**Product 1:** Representable as a customer product plus a versioned specification with ordered layers, print color slots, typed parameters, a source attachment, and manually authored downstream definitions. It is **not** safe to represent the PDF automatically as a BOM, routing, or execution record.

**Product 2:** Representable as a customer product plus a versioned specification with one PE layer, seven print slots, typed converting/packaging parameters, a source attachment, and manually authored downstream definitions. It is **not** safe to normalize the coded converting fields, bundle/carton hierarchy, or source identifiers automatically.

**Architecture conclusion:** The core product/specification architecture is validated for real SLZ product evidence. The main remaining weakness is semantic richness around lamination, print-reference metadata, converting features, packaging hierarchy, and source provenance; those should be addressed only after the relevant vocabulary and business gates are confirmed.
