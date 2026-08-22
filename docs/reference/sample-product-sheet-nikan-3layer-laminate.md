# Sample Product Sheet — Nikan 3-Layer Laminate (Libaro Coffee, 1 kg, Side Gusset, 50 cm)

> **Source PDF:** `C:\Users\RADIN\Downloads\Product Data Sheet - لمینت 3 لایه قهوه لیبارو یک کیلویی بغل گاست عرض 50 سانت.pdf`
> **Purpose:** faithful, machine-readable transcription of a REAL product data sheet exported by SLZ's existing system ("NSYS"). Evidence only — not an ERP schema proposal. `docs/SLZ-SOURCE-OF-TRUTH.md` remains authoritative.

---

## Document Metadata

| Item | Value | Status |
|---|---|---|
| PDF filename | `Product Data Sheet - لمینت 3 لایه قهوه لیبارو یک کیلویی بغل گاست عرض 50 سانت.pdf` | CONFIRMED_FROM_PDF |
| Number of pages | 3 | CONFIRMED_FROM_PDF |
| System of origin | NSYS (printed top-right of header) | CONFIRMED_FROM_PDF |
| Export timestamp | 2026-08-22 21:03:35 | CONFIRMED_FROM_PDF |
| Sheet title | Product Data Sheet | CONFIRMED_FROM_PDF |
| Header logo | "SLZ" with tagline "Solution Packaging Excellence" (small print) | CONFIRMED logo text / [UNCLEAR] exact tagline at rendered resolution |

---

## Raw Transcription

### Page 1 — Header block

> Source: PDF page 1

| Field (as labeled) | Exact value |
|---|---|
| Customer Product | لمینت 3 لایه قهوه لیبارو یک کیلویی بغل گاست عرض 50 سانت |
| NSYS Product Title | `MLTLYRFLM ROLL BOPP/PET/PE TK:117µm PRNT WD:500mm SLBL SLITTED JUMBO:1roll` |
| Customer Name | صنایع بسته بندی پوشش آرای نیکان |
| NSYS Product Code | 14445 |
| SP Code | 42102000008225 |
| SKU Code | 14445.6059.1 |

### Page 1 — Film & Printing (grid of parameter boxes)

> Source: PDF page 1

| Box label | Value | Tolerance |
|---|---|---|
| Roll Width (mm) | 500 | *[none shown]* |
| Jumbo Roll Width (mm) | 1220 | *[none shown]* |
| Opening Direction | Outside | — |
| Plate Mounting | Simple | — |
| No in Primeter *(sic — spelled "Primeter" in the PDF)* | 2 | — |
| No Of Cliché in roll width | 1 | — |
| Sleeve (mm) | 760 | — |
| Repeat (mm) | 760 | *[none shown]* |
| Print Tech | Classic | — |
| FG UPS | 1 | — |
| Print Side | Inside | — |

### Page 1 — Film Layers table

> Source: PDF page 1
> Table headers (exact): Layer · Material · Material Color · Thickness · Tolerance · Grammage · Tolerance · Reflection · Sealability · Corona · Chemical · Print · Print Type · Color Count

Each layer renders as multiple sub-rows (form-control states captured in the export). Transcribed as displayed:

| Layer | Material | Material Color | Thickness | Reflection | Sealability | Corona | Chemical | Print | Print Type | Color Count |
|---|---|---|---|---|---|---|---|---|---|---|
| A | BOPP | Transparent | 20 µm | Matte / Sealable / *(row)* 0 | | | | | | |
| A | BOPP | Transparent | 20 µm | Gloss | | Corona | | Printed | Reverse | 2 |
| A | BOPP | Transparent | 20 µm | Gloss | | | Chemical | | | 0 |
| B | PET | Metalized | 12 µm | Matte | | Corona | | | | 0 |
| B | PET | Metalized | 12 µm | Gloss | Sealable | Corona | | | | 0 |
| C | PE | Transparent | 85 µm | Gloss | Sealable | | | | | 0 |

- Tolerance and Grammage columns: empty for all three layers.
- [UNCLEAR — sub-rows appear to be alternative states of dropdown controls (Matte/Gloss × Sealable/Corona/Chemical), not additional physical surfaces. The meaningful row is likely the one with Print/Print Type/Color Count populated (layer A).]

Arithmetic note (INFERRED, not printed in PDF): 20 + 12 + 85 = 117 µm matches `TK:117µm` in the title.

### Page 1 — Laminations table

> Source: PDF page 1
> Table headers (exact): Lamination · Lamination Type · Description

| Lamination | Lamination Type | Description |
|---|---|---|
| A~B | Solvent Based | *[empty]* |
| AB~C | Solvent Based | *[empty]* |

[UNCLEAR — second bond label reads "AB~C"; whether this denotes "A+B to C" or "(A~B)~C" is not stated.]

### Page 1 — Print Colors table

> Source: PDF page 1
> Table headers (exact): Action · Title · Ink Family · Process Ink Color · Spot Ink Coding · Spot Ink Code · Trama · Solid · Lpi

| Action | Title | Process Ink Color | Spot Ink Coding | Spot Ink Code | Trama | Solid | Lpi |
|---|---|---|---|---|---|---|---|
| 1 | Spot Ready Ink | -- | Internal | White | OFF | ON | 50-300 |
| 2 | Process Ready Ink | Black | -- | | OFF | ON | 133 |

**OUTPUT FILM** section:

```
OUTPUT FILM
Print Layout   [BOPP Transparent 20µm Reverse]
```

> Source: PDF page 1. The design preview image appears on page 2.

### Page 2 — BLK parameters and drawing

> Source: PDF page 2
> Table headers (exact): `BLK · A · B1 · H1 · K1 · K2 · R1 · R2 · D1 · D2 · D4`

| Row | A | B1 | H1 | K1 | K2 | R1 | R2 | D1 | D2 | D4 |
|---|---|---|---|---|---|---|---|---|---|---|
| BLK11 | 380 | 500 | 500 | 0 | 0 | 0 | 1 | 14 | 6 | 0 |
| BLK11 (+) | | | | | | | | +1 | +1 | +1 |
| BLK11 (−) | | | | | | | | -1 | -1 | -1 |
| BLK12 | 380 | 500 | 500 | 0 | 0 | 0 | 0 | 14 | 6 | 0 |
| BLK12 (+) | | | | | | | | +1 | +1 | +1 |
| BLK12 (−) | | | | | | | | -1 | -1 | -1 |

Only columns D1, D2, D4 carry tolerances (+1/−1). Columns without entries show no tolerance in the PDF.

Diagram on page 2 (titled **"BLK Parameter Helper"**, identical layout to the diaper-bag sheet):
rectangle with `A` vertical, `B1` horizontal, `C` and `H1` inset lines, `R2` top-left corner mark, `K1`/`K2` inner-rectangle side margins, `CL`/`CR` edge marks, and bottom-left **"Eye Mark Parameters"**: black bar sized `D2` (height) × `D1` (width).

Page-2 image: roll of printed white/coffee-design film (design preview, two-up across web).

### Pages 2–3 — Corona section

> Sources: PDF page 2 (rows for A, B and one further row), page 3 (layer C)
> Table headers (exact): Layer · Material · Corona Parameters

| Layer | Material | Corona Parameters (as shown) |
|---|---|---|
| A | BOPP | C1 = 500 |
| B | PET | C1 = 500 |
| *[third row]* | | C1 = 500 |
| C | PE | *[empty]* |

[UNCLEAR — a third `C1 = 500` row appears at the bottom of page 2 without a visible layer label; its association is not stated. Layer C shows no corona parameters.]

### Page 3 — Comments

> Source: PDF page 3
> Section headers (exact): Comments · General Comments · Comments On Edited Rolls

| Field | Exact value |
|---|---|
| General Comments | در کنار 42102000008226 و 42102000008227 چاپ میشود. |
| Comments On Edited Rolls | *[empty]* |

(The Persian sentence was stored RTL; raw extraction showed reversed token order. Correct reading as above.)

POSSIBLE_MEANING: «چاپ میشود» = "is printed"; the sentence appears to state that this product prints alongside codes 42102000008226 and 42102000008227 (likely related SP Codes / ganging partners on the same cylinder). INFERRED — the codes' nature is not defined in the PDF.

### Page 3 — Product Requirements table

> Source: PDF page 3
> Table headers (exact): Package Type · Title · Amount · Unit · Operation

| Package Type | Title | Amount | Unit | Operation |
|---|---|---|---|---|
| Core | `BBN CRDBRD INTDM:3" LNG:500mm EXTDM:102.2mm (13228) (RawCore: 11401980)` | 0.00 | *[empty]* | *[empty]* |
| FirstPack | `JMBBG SHEET PE TK:13µm TRANS SL:BTN GS:SD:150mm TUB:TUB WD:600mm LNG:1000mm GRD:LD (208)` | 0.00 | *[empty]* | *[empty]* |

[UNCLEAR — Amount = 0.00 for both rows; whether this means "not yet quantified" or a real zero is not stated.]

### Page 3 — Roll Info table

> Source: PDF page 3
> Table headers (exact): Roll Weight (Kg) · Roll Length (m) · Roll Diameter (mm) · Core's Weight (Kg)

| Roll Weight (Kg) | Roll Length (m) | Roll Diameter (mm) | Core's Weight (Kg) |
|---|---|---|---|
| 71.00 (+5% / −5%) | 1,169.00 (+5% / −5%) | 440.00 (+5% / −5%) | 1.50 |

Note: tolerances here are **percentages**, unlike the mm tolerances elsewhere.

### Page 3 — Pallet Info

> Source: PDF page 3
> Table headers (exact): Pallet · Divider · Stretch Wrapping · Belt · Upper Guard · Number Of Rows · Max Units · Max Height (Cm) · Max Weight (Kg)

| Pallet | Divider | Stretch Wrapping | Belt | Upper Guard | Number Of Rows | Max Units | Max Height (Cm) | Max Weight (Kg) |
|---|---|---|---|---|---|---|---|---|
| PALLET SIZE:110*110 WOODEN | ✓ | ✓ | ✓ | Cardboard | 3 | 12 | 170.00 | 900.00 |

---

## Structured Product Extraction

### Customer
- Customer Name: صنایع بسته بندی پوشش آرای نیکان (CONFIRMED, page 1)

### Product Identity
- NSYS Product Code: 14445 (CONFIRMED)
- SP Code: 42102000008225 (CONFIRMED)
- SKU Code: 14445.6059.1 (CONFIRMED)

### Customer Product Code
- The field "Customer Product" holds the Persian descriptive name; no separate numeric customer code beyond SP/SKU codes. NOT PROVIDED IN PDF (as a distinct code).

### Product Description
- Encoded title (verbatim): `MLTLYRFLM ROLL BOPP/PET/PE TK:117µm PRNT WD:500mm SLBL SLITTED JUMBO:1roll`
- POSSIBLE_MEANING (all INFERRED): multi-layer film roll; BOPP/PET/PE structure; total thickness 117 µm; printed; width 500 mm; sealable; delivered slitted jumbo rolls, 1 roll per …(unit).

### Product Revision
- No revision number/date/approval block. NOT PROVIDED IN PDF.
- Trailing `.1` in SKU may be revision index — UNCLEAR.

### Dimensions
| Dimension | Value |
|---|---|
| Roll Width (output) | 500 mm |
| Jumbo Roll Width | 1220 mm |
| Sleeve | 760 mm |
| Repeat | 760 mm |
| BLK A / B1 / H1 | 380 / 500 / 500 (mm INFERRED) |
| Eye mark D1 / D2 | 14 / 6 (+1/−1 each) (mm INFERRED) |
| Roll Diameter (finished roll) | 440.00 mm (+5%/−5%) |
| Roll Length | 1,169.00 m (+5%/−5%) |

### Material Structure
Three layers (CONFIRMED):

| Layer | Material | Color | Thickness | Tolerance |
|---|---|---|---|---|
| A | BOPP | Transparent | 20 µm | none shown |
| B | PET | Metalized | 12 µm | none shown |
| C | PE | Transparent | 85 µm | none shown |

Total thickness per title: TK:117µm (CONFIRMED string; sum arithmetic INFERRED).

### Layer Structure
- Order A → B → C outward/inward direction NOT STATED in PDF (which face is outside is not defined; print is on BOPP reverse).
- Bonds: A~B solvent-based adhesive; AB~C solvent-based adhesive (CONFIRMED).

### Printing
- Print Side: Inside; Output film layout: `[BOPP Transparent 20µm Reverse]`; Plate Mounting: Simple; Print Tech: Classic; FG UPS: 1; No in Primeter: 2; No Of Cliché in roll width: 1; Opening Direction: Outside (all CONFIRMED strings).
- Note apparent tension: grid says "Print Side: Inside", output-film label says "Reverse", while layer A reflection rows include both "Reverse" and "Surface"-style states. Consistent reading (reverse/inside are the same concept) is INFERRED, not proven.

### Colors
- Color Count: 2 on layer A (CONFIRMED). Colors: White (spot, internal coding), Black (process-ready). Layers B/C color count 0 (CONFIRMED).

### Inks
- Action 1: Spot Ready Ink, Spot Ink Coding = Internal, Spot Ink Code = `White`, Solid ON, Trama OFF, Lpi 50–300.
- Action 2: Process Ready Ink, Process Ink Color = `Black`, Solid ON, Trama OFF, Lpi 133.
- "Internal" ink registry meaning NOT DEFINED IN PDF. Asymmetric Lpi values (50–300 vs 133) UNCLEAR.

### Finishing
- Reflections per layer as transcribed (Gloss/Matte states). Lamination type: Solvent Based (both bonds). No coating/varnish section. NOT PROVIDED IN PDF otherwise.

### Sealing / Conversion
- This product ships as **slitted jumbo roll stock** (`SLITTED JUMBO:1roll`), not converted bags — bag-conversion dimension tables absent (no Converting section like the diaper sheet). INFERRED from title + absence.
- Sealability flags present on layers (A sub-row, B, C) — CONFIRMED strings.

### Tolerances
- Film & printing widths/repeat: none shown for this product.
- BLK D1/D2/D4: ±1 (mm INFERRED).
- Roll Info: ±5% on weight, length, diameter.

### Quantity
- JUMBO:1roll (title); pallet Max Units 12, Number Of Rows 3 (CONFIRMED).
- Product Requirements amounts: 0.00 for Core and FirstPack (CONFIRMED value; interpretation UNCLEAR).

### Weight
- Roll Weight 71.00 kg (+5%/−5%); Core's Weight 1.50 kg; Pallet max weight 900.00 kg (CONFIRMED).

### Packaging
- Core (Package Type "Core"): `BBN CRDBRD INTDM:3" LNG:500mm EXTDM:102.2mm (13228) (RawCore: 11401980)`
- FirstPack: `JMBBG SHEET PE TK:13µm TRANS SL:BTN GS:SD:150mm TUB:TUB WD:600mm LNG:1000mm GRD:LD (208)`
- POSSIBLE_MEANING (INFERRED): cardboard core, internal Ø 3", length 500 mm, external Ø 102.2 mm, with internal item code 13228 referencing a raw-material record (RawCore: 11401980); first-pack is a PE jumbo-bag sleeve/sheet 13 µm transparent, bottom seal(?), gusset(?) 150 mm, tubular, 600×1000 mm, LD grade, item code 208. All expansions UNCLEAR.
- Pallet: PALLET SIZE:110*110 WOODEN, divider ✓, stretch wrapping ✓, belt ✓, upper guard Cardboard, 3 rows, 12 units, max height 170.00 cm, max weight 900.00 kg.

### Quality Requirements
- No QC section, standards, or regulatory statements. NOT PROVIDED IN PDF.

### Production Requirements
- No machine/routing data. Sections imply stages only. INFERRED.

### Raw Materials
- The Product Requirements table references internal material codes `(13228)` / `(RawCore: 11401980)` and `(208)` — evidence that packaging consumables are master-data items with IDs (CONFIRMED codes exist). Adhesives: "Solvent Based" (type only; no item code). Layer resins: no codes given.

### Notes
- General Comments: در کنار 42102000008226 و 42102000008227 چاپ میشود. (CONFIRMED text)

---

## Material / Layer Structure

> Source: PDF page 1 (Film Layers, Laminations)

```
Layer A : BOPP, Transparent, 20 µm            ← Printed (Reverse), Color Count 2, corona C1=500
   ~~~ bond 1: Solvent Based (A~B) ~~~
Layer B : PET, Metalized, 12 µm               ← corona C1=500
   ~~~ bond 2: Solvent Based (AB~C) ~~~
Layer C : PE, Transparent, 85 µm              ← Sealable, no corona params shown
```

- Total: 117 µm (from title; sum INFERRED).
- Which layer faces the product/outside is NOT STATED.
- Sealability appears on A (sub-row), B, and C in various sub-rows — see UNCLEAR note in Raw Transcription.

---

## Manufacturing Interpretation

| PDF information | Possible ERP concept | Confidence |
|---|---|---|
| Customer + customer-product name | Customer / customer product identity | CONFIRMED mapping |
| 3-layer structure w/ per-layer thickness | Structure = ordered layers (product-model §3.1) | CONFIRMED |
| Laminations A~B, AB~C, Solvent Based | Lamination process steps + adhesive type | CONFIRMED data / INFERRED process stage |
| BOPP/PET/PE purchased or extruded in-house? | Make-vs-buy per layer | NOT DETERMINABLE FROM PDF |
| Print on BOPP reverse, 2 colors, cliché counts, repeat/sleeve | Printing prep incl. tooling | CONFIRMED spec / INFERRED rotogravure |
| Corona C1 per layer | Corona treatment step(s) | INFERRED |
| SLITTED JUMBO:1roll + Roll Info (weight/length/diameter) | Slitting operation; finished-goods roll definition | INFERRED |
| Core + FirstPack package requirements w/ item codes | Packaging BOM components referencing material master | CONFIRMED codes / INFERRED BOM role |
| Roll weight 71 kg ±5%, length 1169 m ±5% | Delivery quantity tolerance rules | CONFIRMED values |
| Pallet Info | Palletization/delivery spec | CONFIRMED |
| General Comments re: codes 42102000008226/…227 | Ganged printing (same cylinder across products) | INFERRED |

This document contains information that may correspond to: lamination-step modeling (bond-level adhesive type), packaging-component links to material master (item codes in parentheses), ganged-printing relationships between products, and percent-based delivery tolerances. It does NOT prove how these should be modeled.

---

## Potential ERP Gaps Revealed By This Document

Compared against `docs/business-analysis/product-model.md`, `bom-and-routing.md`, `manufacturing-processes.md`, `SLZ-SOURCE-OF-TRUTH.md`, `implementation-gap-matrix.md`.

| # | PDF evidence | Current ERP concept | Apparent gap | Confidence | Business decision needed? |
|---|---|---|---|---|---|
| 1 | Three parallel identifiers: NSYS Product Code 14445, SP Code 42102000008225, SKU 14445.6059.1 | Customer product + SKU (SR-01 derivation) | Relationship/derivation between the three systems undocumented | CONFIRMED presence | Yes |
| 2 | Lamination table with bond pairs (A~B, AB~C) and adhesive type | Finishing attributes exist generically; bond-level records not evidenced | Bond-level lamination steps (pairing + adhesive class) | CONFIRMED data | Possibly |
| 3 | Per-layer corona parameters (C1=500) incl. one unattributed row | Corona mentioned qualitatively (Q-012) | Structured corona parameters per layer | CONFIRMED data | Possibly |
| 4 | Package Requirements reference material-master codes inline: `(13228) (RawCore: 11401980)`, `(208)` | BOM components modeled in manufacturing app | Whether packaging requirements are spec attributes AND BOM lines simultaneously; ID namespaces | CONFIRMED codes exist | Yes |
| 5 | General comment ties this product to codes 42102000008226 & 42102000008227 (prints alongside) | No ganged-printing/campaign concept found in docs | Cross-product production/print relationship | CONFIRMED text / meaning INFERRED | Yes |
| 6 | Percent tolerances (±5%) on roll weight/length/diameter vs absolute mm tolerances elsewhere | Tolerances modeled as tol_low/tol_high | Need to support relative (%) tolerance type | CONFIRMED pattern | Possibly |
| 7 | BLK parameter sets + eye-mark diagram (also on diaper sheet) | Not represented in docs | Print-layout/conversion geometry storage | CONFIRMED data | Yes |
| 8 | Encoded NSYS title grammar (`MLTLYRFLM ROLL BOPP/PET/PE TK:117µm …`) | Individual spec attributes | Derived encoded-title requirement | CONFIRMED string | Yes — is grammar required? |
| 9 | Sheet exported by external NSYS system | Phase-1 ERP replaces/augments it? | Coexistence/migration scope | CONFIRMED origin | Yes — scope decision |

---

## Field Dictionary

Values verbatim. Confidence applies to possible-meaning attribution.

| PDF Field | Exact Value | Unit | Possible ERP Meaning | Confidence | Notes |
|---|---|---|---|---|---|
| Customer Product | لمینت 3 لایه قهوه لیبارو یک کیلویی بغل گاست عرض 50 سانت | — | Customer-facing name | CONFIRMED value / INFERRED meaning | 3-layer laminate, Libaro coffee, 1 kg, side gusset, 50 cm width |
| NSYS Product Title | `MLTLYRFLM ROLL BOPP/PET/PE TK:117µm PRNT WD:500mm SLBL SLITTED JUMBO:1roll` | mixed | Derived spec summary | CONFIRMED string / INFERRED purpose | Tokens: MLTLYRFLM=multi-layer film?, SLBL=sealable?, UNCLEAR individually |
| Customer Name | صنایع بسته بندی پوشش آرای نیکان | — | Customer entity | CONFIRMED | — |
| NSYS Product Code | 14445 | — | Internal product ID | CONFIRMED | — |
| SP Code | 42102000008225 | — | Secondary/partner code | UNCLEAR semantics | 14-digit numeric |
| SKU Code | 14445.6059.1 | — | Sellable unit code | CONFIRMED string / UNCLEAR segments | — |
| Roll Width (mm) | 500 | mm | Output roll width | CONFIRMED | No tolerance shown |
| Jumbo Roll Width (mm) | 1220 | mm | Parent web width | CONFIRMED | Implies 2-up slitting? (INFERRED; 1220 ≈ 2×500 + trim) |
| Opening Direction | Outside | — | Unwind/opening orientation | CONFIRMED value / UNCLEAR meaning | — |
| Plate Mounting | Simple | — | Cliché mounting enum | CONFIRMED value / UNCLEAR meaning | — |
| No in Primeter | 2 | count | Repeats around perimeter | POSSIBLE_MEANING | Misspelling preserved |
| No Of Cliché in roll width | 1 | count | Across-web clichés | POSSIBLE_MEANING | — |
| Sleeve (mm) | 760 | mm | Cylinder sleeve size | POSSIBLE_MEANING | — |
| Repeat (mm) | 760 | mm | Print repeat | CONFIRMED value / POSSIBLE_MEANING | — |
| Print Tech | Classic | — | Process enum | CONFIRMED value / UNCLEAR meaning | — |
| FG UPS | 1 | count | Unknown finished-goods count | UNCLEAR | — |
| Print Side | Inside | — | Reverse printing | CONFIRMED value | Matches "Reverse" output label (equivalence INFERRED) |
| Layer A | BOPP · Transparent · 20 µm | µm | Outer(?) printable layer | CONFIRMED | Face order NOT STATED |
| Layer B | PET · Metalized · 12 µm | µm | Barrier layer | CONFIRMED | Barrier role INFERRED from "Metalized" |
| Layer C | PE · Transparent · 85 µm | µm | Sealant layer | CONFIRMED value / sealant role INFERRED | — |
| Lamination A~B | Solvent Based | — | Bond 1 + adhesive class | CONFIRMED | Description column empty |
| Lamination AB~C | Solvent Based | — | Bond 2 + adhesive class | CONFIRMED | Label syntax UNCLEAR |
| Print Colors #1 | Spot Ready Ink · Internal · White · Lpi 50-300 | — | White ink station | CONFIRMED | Range-type Lpi value UNCLEAR |
| Print Colors #2 | Process Ready Ink · Black · Lpi 133 | — | Black station | CONFIRMED | — |
| OUTPUT FILM | Print Layout [BOPP Transparent 20µm Reverse] | — | Artwork/print-layout link | CONFIRMED string | — |
| BLK11 / BLK12 | A380 B1500 H1500 K10 K20 R10 R2 1/0 D114 D26 D40; ±1 on D1,D2,D4 | mm (INFERRED) | Layout blocks & eye marks | CONFIRMED values / UNCLEAR semantics | BLK11 R2=1 vs BLK12 R2=0 — only difference |
| Corona C1 (layers A, B, +1 unlabeled) | 500 | mm (INFERRED) | Corona treatment parameter | CONFIRMED value / UNCLEAR unit+meaning | Third row attribution UNCLEAR |
| General Comments | در کنار 42102000008226 و 42102000008227 چاپ میشود. | — | Free-text production note | CONFIRMED text / INFERRED meaning | Ganged-print hint |
| Core requirement | `BBN CRDBRD INTDM:3" LNG:500mm EXTDM:102.2mm (13228) (RawCore: 11401980)` | inch/mm mixed | Winding core component | CONFIRMED string / INFERRED expansion | Item refs UNCLEAR |
| FirstPack requirement | `JMBBG SHEET PE TK:13µm TRANS SL:BTN GS:SD:150mm TUB:TUB WD:600mm LNG:1000mm GRD:LD (208)` | µm/mm | Roll wrapping material | CONFIRMED string / INFERRED expansion | Item ref (208) UNCLEAR |
| Amount (both rows) | 0.00 | ? | Requirement quantity | CONFIRMED value / UNCLEAR meaning | Zero vs TBD |
| Roll Weight | 71.00 (+5%/−5%) | kg | Delivered roll target | CONFIRMED | Percent tolerance |
| Roll Length | 1,169.00 (+5%/−5%) | m | Delivered roll length | CONFIRMED | Thousands separator as printed |
| Roll Diameter | 440.00 (+5%/−5%) | mm | Finished roll OD | CONFIRMED | — |
| Core's Weight | 1.50 | kg | tare of core | CONFIRMED value / INFERRED meaning | — |
| Pallet | PALLET SIZE:110*110 WOODEN | cm (INFERRED) | Pallet type | CONFIRMED string | — |
| Divider / Stretch Wrapping / Belt | ✓ / ✓ / ✓ | flags | Packing ops | CONFIRMED | — |
| Upper Guard | Cardboard | — | Top protection | CONFIRMED | — |
| Rows / Max Units / Max Height / Max Weight | 3 / 12 / 170.00 / 900.00 | count/cm/kg | Pallet limits | CONFIRMED | — |

---

## Questions Raised By The Product Sheet

1. What exactly are `SP Code` and `SKU Code`, and how do they derive from the NSYS Product Code?
2. Does the ERP need to reproduce the encoded NSYS Product Title, or is it a legacy display artifact?
3. What does `AB~C` mean precisely in the Laminations table?
4. What is the layer order in space (outside→inside) for BOPP/PET/PE, and which side contacts the coffee?
5. Why do roll width (500) and jumbo width (1220) differ so much here but match (770/770) on other sheets — is jumbo width a purchasing or production attribute?
6. What is the third unlabeled Corona row (`C1 = 500`) associated with?
7. Are the referenced items `(13228) (RawCore: 11401980)` and `(208)` material-master codes, and in what namespace?
8. Is Amount 0.00 in Product Requirements intentional (quantity computed elsewhere) or incomplete data?
9. Do codes 42102000008226/…227 represent sibling products printed on the same cylinder (ganging)? Is there a campaign/grouping concept?
10. Is `Lpi 50-300` a range setting vs `136`/`133` fixed values elsewhere — what governs it?
11. Why do BLK11 and BLK12 differ only in R2 (1 vs 0)?
12. Was this sheet reviewed/approved by anyone? No approval block exists — is approval handled outside the document?

---

## Source Page References

| Content | PDF page |
|---|---|
| Header block (customer, codes, titles) | 1 |
| Film & Printing grid | 1 |
| Film Layers table | 1 |
| Laminations table | 1 |
| Print Colors table + OUTPUT FILM | 1 |
| Design preview image | 2 |
| BLK parameter table + helper diagram | 2 |
| Corona rows (A, B, third row) | 2 |
| Corona row (C) + Comments + Product Requirements + Roll Info + Pallet Info | 3 |

---

## Extraction Notes

- Extracted via PyMuPDF text plus visual inspection of rendered pages; tables reconciled against both sources because raw text order was scrambled (RTL Persian + multi-row UI forms).
- Persian preserved exactly: «لمینت 3 لایه قهوه لیبارو یک کیلویی بغل گاست عرض 50 سانت», «صنایع بسته بندی پوشش آرای نیکان», and the General Comments sentence (raw dump had visually-reversed digit order; corrected reading confirmed against rendered page).
- Multi-row artifacts in Film Layers (dropdown-state rows) transcribed as displayed and flagged UNCLEAR rather than silently collapsed.
- Mixed-unit strings preserved verbatim (e.g., `INTDM:3"` uses inches inside an otherwise metric string).
- Percent vs absolute tolerance distinction preserved deliberately.
- Nothing invented; all uncertain readings flagged. Companion file documenting the second provided sheet: `sample-product-sheet-haniz-diaper-bag.md`.
