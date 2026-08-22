# Sample Product

## 1. Document Metadata

| Field | Value | Confidence | Source |
|---|---|---|---|
| Source PDF filename | `Product Data Sheet - لمینت 3 لایه قهوه لیبارو یک کیلویی بغل گاست عرض 50 سانت.pdf` | CONFIRMED_FROM_PDF filename | Repository path |
| Page count | 3 | CONFIRMED_FROM_PDF | PDF page sequence |
| Document title | `Product Data Sheet` | CONFIRMED_FROM_PDF | PDF page 1 |
| Generator/system label | `NSYS` | CONFIRMED_FROM_PDF | PDF page 1 |
| Printed document date/time | `2026-08-22 21:03:35` | CONFIRMED_FROM_PDF | PDF page 1 |
| Customer | Blank in the PDF field | NOT_PROVIDED | PDF page 1 |
| Product code | `14445` (NSYS Product Code) | CONFIRMED_FROM_PDF | PDF page 1 |
| Customer product field | `50         3` as positioned in the extracted text | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR | PDF page 1 |
| SP Code | `42102000008225` | CONFIRMED_FROM_PDF | PDF page 1 |
| SKU Code | `14445.6059.1` | CONFIRMED_FROM_PDF | PDF page 1 |
| Revision | Not shown | NOT_PROVIDED | PDF page 1 |
| Status | Not shown | NOT_PROVIDED | PDF pages 1-3 |

The Persian filename identifies the product as a three-layer Libaro one-kilogram coffee laminate with side gusset and 50 cm width (the PDF states 500 mm), but that customer/product description is **not repeated in a populated customer-name field inside the PDF**. It is retained as filename evidence only.

## 2. Raw Transcription

### PDF page 1

Visible labels and values, preserving source wording/casing and coded text:

```text
Product Data Sheet                                             NSYS
2026-08-22 21:03:35

Customer Product: 50         3
NSYS Product Title:
MLTLYRFLM ROLL BOPP/PET/PE TK:117�m PRNT WD:500mm SLBL SLITTED
JUMBO:1roll
Customer Name: [blank]
NSYS Product Code: 14445
SP Code: 42102000008225
SKU Code: 14445.6059.1
```

Film and printing header fields:

| PDF field | Exact value | Source page |
|---|---|---:|
| Roll Width (mm) | `500` | 1 |
| Jumbo Roll Width (mm) | `1220` | 1 |
| Opening Direction | `Outside` | 1 |
| Plate Mounting | `Simple` | 1 |
| No in Primeter | `2` | 1 |
| No Of Cliché in roll width | `1` | 1 |
| Sleeve (mm) | `760` | 1 |
| Repeat (mm) | `760` | 1 |
| Print Tech | `Classic` | 1 |
| FG UPS | `1` | 1 |
| Print Side | `Inside` | 1 |

Film Layers table as extracted from the PDF layout:

| Layer | Material | Material Color | Thickness | Tolerance | Grammage | Tolerance | Reflection | Sealability | Corona | Chemical | Print | Print Type | Color Count | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---:|---|
| A | `BOPP` | `Transparent` | `20 �m` | blank | blank | blank | `Matte` / `Gloss` entries appear in the row block | `Sealable` appears in the row block | `Corona` appears in the row block | blank | `Printed` | `Reverse` | `2` | Material/color/thickness/print values CONFIRMED_FROM_PDF; treatment-column association UNCLEAR |
| B | `PET` | `Metalized` | `12 �m` | blank | blank | blank | `Gloss` / `Matte` entries appear in the row block | blank | `Corona` appears in the row block | `Chemical` appears in the row block | blank | blank | `0` | Material/color/thickness CONFIRMED_FROM_PDF; treatment-column association UNCLEAR |
| C | `PE` | `Transparent` | `85 �m` | blank | blank | blank | `Gloss` entries appear in the row block | `Sealable` appears in the row block | `Corona` appears in the row block | blank | blank | blank | `0` | Material/color/thickness CONFIRMED_FROM_PDF; treatment-column association UNCLEAR |

The text extraction emits `�m` for the micron symbol. The likely rendered unit is `µm`, but the exact character is **UNCLEAR** in the extracted text layer. The three listed thickness values sum to `117` when interpreted as microns, matching `TK:117�m` in the product title; the summation is an **INFERRED consistency check**, not a PDF-stated total field.

Lamination table:

| PDF field | Exact value | Source page |
|---|---|---:|
| Lamination / process row | `Lamination` | 1 |
| A~B | `Solvent Based` | 1 |
| AB~C | `Solvent Based` | 1 |
| Description | blank | 1 |

Print Colors table:

| Action Title | Ink Family | Process Ink Color | Spot Ink Coding | Spot Ink Code | Trama | Solid | Lpi | Confidence |
|---:|---|---|---|---|---|---|---|---|
| `1` | `Spot Ready Ink` | `--` | `Internal` | blank | blank | blank | `50-300` | Row values CONFIRMED_FROM_PDF; exact visual column alignment retained from PDF layout |
| `2` | `Process Ready Ink` | `Black` | `--` | blank | blank | blank | `133` | CONFIRMED_FROM_PDF |

Print layout:

```text
OUTPUT FILM
Print Layout [BOPP Transparent 20�m Reverse]
```

The source text contains `�m` in this layout label; the micron symbol is UNCLEAR for the same encoding reason described above. Source: PDF page 1.

### PDF page 2

The page contains a coded dimensional/layout diagram with the following visible column headings:

`BLK | A | B1 | H1 | K1 | K2 | R1 | R2 | D1 | D2 | D4`

The two visible rows and tolerances are transcribed below. The headings are retained as codes because the PDF does not provide a legend expanding them.

| Block | A | B1 | H1 | K1 | K2 | R1 | R2 | D1 | D2 | D4 | Source page |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `BLK11` | `380` | `500` | `500` | `0` | `0` | `0` | `1` | `14` | `6` | `0` | 2 |
| `BLK12` | `380` | `500` | `500` | `0` | `0` | `0` | `0` | `14` | `6` | `0` | 2 |

Visible tolerance markers in the same diagram:

| Block | D1 tolerance | D2 tolerance | D4 tolerance | Confidence |
|---|---|---|---|---|
| `BLK11` | `+1 / -1` | `+1 / -1` | `+1 / -1` | CONFIRMED_FROM_PDF; association inferred from column position |
| `BLK12` | `+1 / -1` | `+1 / -1` | `+1 / -1` | CONFIRMED_FROM_PDF; association inferred from column position |

The PDF labels this area `BLK Parameter Helper`. The units for the coded values are not printed on this page. The meaning of `BLK`, `A`, `B1`, `H1`, `K1`, `K2`, `R1`, `R2`, `D1`, `D2`, and `D4` is **UNCLEAR**.

Corona/material helper table:

| Layer | Material | Corona Parameters | Source page |
|---|---|---|---:|
| A | `BOPP` | `C1 500` | 2 |
| B | `PET` | `C1 500` | 2 |
| C | `PE` | `C1 500` (the row is continued on PDF page 3) | 2-3 |

### PDF page 3

Comments area:

| Field | Exact transcription | Confidence |
|---|---|---|
| General Comments | `.` followed by `42102000008227 42102000008226` | CONFIRMED_FROM_PDF; purpose UNCLEAR |
| Comments On Edited Rolls | blank | NOT_PROVIDED |

Product Requirements table:

| Package Type | Title | Amount | Unit | Operation | Source page |
|---|---|---:|---|---|---:|
| `Core` | `BBN CRDBRD INTDM:3" LNG:500mm EXTDM:102.2mm (13228) (RawCore: 11401980)` | `0.00` | blank | blank | 3 |
| `FirstPack` | `JMBBG SHEET PE TK:13�m TRANS SL:BTN GS:SD:150mm TUB:TUB WD:600mm LNG:1000mm GRD:LD (208)` | `0.00` | blank | blank | 3 |

Roll information:

| Field | Exact value | Tolerance | Source page |
|---|---:|---|---:|
| Roll Weight (Kg) | `71.00` | `+ 5% / - 5%` | 3 |
| Roll Length (m) | `1,169.00` | `+ 5% / - 5%` | 3 |
| Roll Diameter (mm) | `440.00` | `+ 5% / - 5%` | 3 |
| Core's Weight (Kg) | `1.50` | blank | 3 |

Pallet information:

| Field | Exact value | Source page |
|---|---|---:|
| Pallet | `PALLET SIZE:110*110 WOODEN` | 3 |
| Divider | blank or not legible as a separate value | 3 |
| Stretch Wrapping | blank or not legible as a separate value | 3 |
| Belt | blank or not legible as a separate value | 3 |
| Upper Guard / associated material text | `Cardboard` appears in the pallet table; exact column association is UNCLEAR | 3 |
| Number Of Rows | `3` | 3 |
| Max Units | `12` | 3 |
| Max Height (Cm) | `170.00` | 3 |
| Max Weight (Kg) | `900.00` | 3 |

No hand-written annotation, signature, drawing raster, or separate diagram image was exposed by the PDF text extraction. The page-2 block layout is a technical coded diagram/table, not a separately identified image.

## 3. Product Identity

| Field | Exact value | Confidence | Source page |
|---|---|---|---:|
| Customer | blank | NOT_PROVIDED | 1 |
| Product name/title | `MLTLYRFLM ROLL BOPP/PET/PE TK:117�m PRNT WD:500mm SLBL SLITTED JUMBO:1roll` | CONFIRMED_FROM_PDF | 1 |
| Product code | `14445` | CONFIRMED_FROM_PDF | 1 |
| Customer SKU/code | `42102000008225` (SP Code); `14445.6059.1` (SKU Code) | CONFIRMED_FROM_PDF | 1 |
| Revision | blank | NOT_PROVIDED | 1 |
| Status | blank | NOT_PROVIDED | 1 |
| Date | `2026-08-22 21:03:35` | CONFIRMED_FROM_PDF; date role UNCLEAR | 1 |

Possible meanings of title abbreviations, kept separate from confirmed values:

| Token | Possible meaning | Confidence |
|---|---|---|
| `MLTLYRFLM` | Possible meaning: multi-layer film | POSSIBLE_MEANING |
| `TK` | Possible meaning: thickness | POSSIBLE_MEANING |
| `PRNT` | Possible meaning: printed | POSSIBLE_MEANING |
| `WD` | Possible meaning: width | POSSIBLE_MEANING |
| `SLBL` | Possible meaning: sealable | POSSIBLE_MEANING |
| `SLITTED` | Possible meaning: slit/slitted format | POSSIBLE_MEANING |
| `JUMBO:1roll` | Possible meaning: one jumbo roll | POSSIBLE_MEANING; `1roll` itself is CONFIRMED_FROM_PDF |
| `BBN CRDBRD` | Possible meaning: paper/cardboard | POSSIBLE_MEANING; raw title is authoritative |
| `INTDM`, `EXTDM`, `LNG`, `GS`, `TUB`, `WD`, `GRD`, `RawCore` | Coded packaging attributes; individual expansions are not established by the PDF | UNCLEAR / POSSIBLE_MEANING |

## 4. Dimensions

| Dimension/parameter | Exact value | Unit | Confidence | Source page |
|---|---:|---|---|---:|
| Finished roll width | `500` | mm | CONFIRMED_FROM_PDF | 1 |
| Jumbo roll width | `1220` | mm | CONFIRMED_FROM_PDF | 1 |
| Repeat | `760` | mm | CONFIRMED_FROM_PDF | 1 |
| Sleeve | `760` | mm | CONFIRMED_FROM_PDF | 1 |
| BLK11 A | `380` | unit not provided | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR | 2 |
| BLK11 B1 | `500` | unit not provided | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR | 2 |
| BLK11 H1 | `500` | unit not provided | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR | 2 |
| BLK11 K1/K2/R1 | `0`, `0`, `0` | unit not provided | CONFIRMED_FROM_PDF | 2 |
| BLK11 R2 | `1` | unit not provided | CONFIRMED_FROM_PDF | 2 |
| BLK11 D1/D2/D4 | `14`, `6`, `0` | unit not provided | CONFIRMED_FROM_PDF | 2 |
| BLK12 A/B1/H1 | `380`, `500`, `500` | unit not provided | CONFIRMED_FROM_PDF | 2 |
| BLK12 K1/K2/R1/R2 | `0`, `0`, `0`, `0` | unit not provided | CONFIRMED_FROM_PDF | 2 |
| BLK12 D1/D2/D4 | `14`, `6`, `0` | unit not provided | CONFIRMED_FROM_PDF | 2 |
| BLK rows D1/D2/D4 tolerances | `+1 / -1` | unit not provided | CONFIRMED_FROM_PDF; column association inferred | 2 |
| Layer A thickness | `20 �m` | micron symbol encoding UNCLEAR | CONFIRMED_FROM_PDF text; unit UNCLEAR | 1 |
| Layer B thickness | `12 �m` | micron symbol encoding UNCLEAR | CONFIRMED_FROM_PDF text; unit UNCLEAR | 1 |
| Layer C thickness | `85 �m` | micron symbol encoding UNCLEAR | CONFIRMED_FROM_PDF text; unit UNCLEAR | 1 |
| Roll weight | `71.00` | Kg | CONFIRMED_FROM_PDF | 3 |
| Roll length | `1,169.00` | m | CONFIRMED_FROM_PDF | 3 |
| Roll diameter | `440.00` | mm | CONFIRMED_FROM_PDF | 3 |
| Core inner diameter | `3"` embedded in core title | inch | CONFIRMED_FROM_PDF; field role from coded title | 3 |
| Core length | `500mm` embedded in core title | mm | CONFIRMED_FROM_PDF | 3 |
| Core external diameter | `102.2mm` embedded in core title | mm | CONFIRMED_FROM_PDF | 3 |
| FirstPack gusset | `150mm` embedded in title | mm | CONFIRMED_FROM_PDF; coded-field meaning partly UNCLEAR | 3 |
| FirstPack width | `600mm` embedded in title | mm | CONFIRMED_FROM_PDF | 3 |
| FirstPack length | `1000mm` embedded in title | mm | CONFIRMED_FROM_PDF | 3 |
| Core weight | `1.50` | Kg | CONFIRMED_FROM_PDF | 3 |
| Roll/pallet tolerances | `+ 5% / - 5%` for roll weight, length, diameter | percent | CONFIRMED_FROM_PDF | 3 |
| Pallet maximum height | `170.00` | Cm | CONFIRMED_FROM_PDF | 3 |
| Pallet maximum weight | `900.00` | Kg | CONFIRMED_FROM_PDF | 3 |

No separate gusset dimension for the finished roll is explicitly labelled outside the coded `FirstPack` title. The filename mentions side gusset, but that is filename evidence rather than a populated PDF field.

## 5. Material Structure

The PDF explicitly lists an ordered three-layer film structure. It does not explicitly call the list a BOM.

| Layer | Material | Thickness | Treatment/appearance shown | Notes | Confidence | Source page |
|---|---|---|---|---|---|---:|
| A | `BOPP` | `20 �m` | `Transparent`; `Matte`, `Gloss`, `Sealable`, and `Corona` appear in the layer block | `Printed`, `Reverse`; color count `2` appears in the table block | CONFIRMED_FROM_PDF for listed values; treatment association UNCLEAR | 1 |
| B | `PET` | `12 �m` | `Metalized`; `Gloss`, `Matte`, `Chemical`, and `Corona` appear in the layer block | Exact treatment-to-column mapping is not recoverable from text extraction | CONFIRMED_FROM_PDF for listed values; association UNCLEAR | 1 |
| C | `PE` | `85 �m` | `Transparent`; `Gloss`, `Sealable`, and `Corona` appear in the layer block | `C` row is continued across pages 2-3 in the corona helper | CONFIRMED_FROM_PDF for listed values; association UNCLEAR | 1-3 |

Lamination structure:

| Lamination stage/line | Lamination type | Description | Confidence | Source page |
|---|---|---|---|---:|
| `A~B` | `Solvent Based` | blank | CONFIRMED_FROM_PDF | 1 |
| `AB~C` | `Solvent Based` | blank | CONFIRMED_FROM_PDF | 1 |

The title contains `TK:117�m`. The sum `20 + 12 + 85 = 117` is an inferred consistency check only. No adhesive material, coat weight, resin grade, or supplier grade is named in the PDF.

## 6. Printing

| Field | Exact value | Confidence | Source page |
|---|---|---|---:|
| Print technology | `Classic` | CONFIRMED_FROM_PDF | 1 |
| Print side | `Inside` | CONFIRMED_FROM_PDF | 1 |
| Print type/layout | `Reverse`; `Print Layout [BOPP Transparent 20�m Reverse]` | CONFIRMED_FROM_PDF; micron glyph UNCLEAR | 1 |
| Number of colors | `2` in the BOPP layer table | CONFIRMED_FROM_PDF | 1 |
| Color 1 | `White` | CONFIRMED_FROM_PDF | 1 |
| Color 1 ink family | `Spot Ready Ink` | CONFIRMED_FROM_PDF | 1 |
| Color 1 spot coding | `Internal` | CONFIRMED_FROM_PDF | 1 |
| Color 1 Lpi/Trama value | `50-300` under `Lpi` in extracted layout | CONFIRMED_FROM_PDF; exact column association should be visually rechecked | 1 |
| Color 2 | `Black` | CONFIRMED_FROM_PDF | 1 |
| Color 2 ink family | `Process Ready Ink` | CONFIRMED_FROM_PDF | 1 |
| Color 2 spot coding | `--` | CONFIRMED_FROM_PDF | 1 |
| Color 2 Lpi value | `133` | CONFIRMED_FROM_PDF | 1 |
| Plate mounting | `Simple` | CONFIRMED_FROM_PDF | 1 |
| Number in perimeter | `2` | CONFIRMED_FROM_PDF | 1 |
| Cliché count in roll width | `1` | CONFIRMED_FROM_PDF | 1 |
| Sleeve | `760` mm | CONFIRMED_FROM_PDF | 1 |
| Repeat | `760` mm | CONFIRMED_FROM_PDF | 1 |
| FG UPS | `1` | CONFIRMED_FROM_PDF; meaning UNCLEAR | 1 |
| Artwork/file reference | Not provided as a named artwork file | NOT_PROVIDED | 1-3 |
| Print registration tolerance | Not explicitly labelled | NOT_PROVIDED | 1-3 |

## 7. Finishing / Conversion

| Operation or feature | Exact evidence | Confidence | Source page |
|---|---|---|---:|
| Lamination | `Lamination` | CONFIRMED_FROM_PDF | 1 |
| Lamination A to B | `A~B Solvent Based` | CONFIRMED_FROM_PDF | 1 |
| Lamination AB to C | `AB~C Solvent Based` | CONFIRMED_FROM_PDF | 1 |
| Slitting | `SLITTED` in NSYS Product Title | CONFIRMED_FROM_PDF; process-stage interpretation direct from wording | 1 |
| Sealing | `SLBL` in title and `Sealable` in layer table | CONFIRMED_FROM_PDF; `SLBL` expansion POSSIBLE_MEANING | 1 |
| Core winding | Core title and roll information are provided | CONFIRMED_FROM_PDF | 3 |
| Bag making/converting | No finished-bag operation explicitly shown; `FirstPack` is listed as a product requirement | NOT_PROVIDED as a confirmed operation; relationship UNCLEAR | 3 |
| Handles, zipper, valve, perforation, punching, folding | Not provided | NOT_PROVIDED | 1-3 |

## 8. Quantity / Commercial Information

| Field | Exact value | Unit | Confidence | Source page |
|---|---:|---|---|---:|
| Jumbo quantity in title | `1roll` | roll | CONFIRMED_FROM_PDF | 1 |
| Product requirement amount for Core | `0.00` | blank | CONFIRMED_FROM_PDF; business meaning UNCLEAR | 3 |
| Product requirement amount for FirstPack | `0.00` | blank | CONFIRMED_FROM_PDF; business meaning UNCLEAR | 3 |
| Roll weight target | `71.00` | Kg | CONFIRMED_FROM_PDF | 3 |
| Roll weight tolerance | `+ 5% / - 5%` | percent | CONFIRMED_FROM_PDF | 3 |
| Roll length target | `1,169.00` | m | CONFIRMED_FROM_PDF | 3 |
| Roll length tolerance | `+ 5% / - 5%` | percent | CONFIRMED_FROM_PDF | 3 |
| Roll diameter target | `440.00` | mm | CONFIRMED_FROM_PDF | 3 |
| Roll diameter tolerance | `+ 5% / - 5%` | percent | CONFIRMED_FROM_PDF | 3 |
| Pallet max units | `12` | units | CONFIRMED_FROM_PDF | 3 |
| Pallet max weight | `900.00` | Kg | CONFIRMED_FROM_PDF | 3 |
| Over/under production allowance | No commercial allowance explicitly labelled; roll tolerances are separate | NOT_PROVIDED | 3 |

## 9. Packaging

| Packaging field | Exact value | Confidence | Source page |
|---|---|---|---:|
| Core | `BBN CRDBRD INTDM:3" LNG:500mm EXTDM:102.2mm (13228) (RawCore: 11401980)` | CONFIRMED_FROM_PDF | 3 |
| FirstPack | `JMBBG SHEET PE TK:13�m TRANS SL:BTN GS:SD:150mm TUB:TUB WD:600mm LNG:1000mm GRD:LD (208)` | CONFIRMED_FROM_PDF; code expansion UNCLEAR | 3 |
| Pallet | `PALLET SIZE:110*110 WOODEN` | CONFIRMED_FROM_PDF | 3 |
| Pallet separator/guard material visible | `Cardboard` | CONFIRMED_FROM_PDF; exact field association UNCLEAR | 3 |
| Number of rows | `3` | CONFIRMED_FROM_PDF | 3 |
| Maximum units | `12` | CONFIRMED_FROM_PDF | 3 |
| Maximum height | `170.00` | Cm | CONFIRMED_FROM_PDF | 3 |
| Maximum weight | `900.00` | Kg | CONFIRMED_FROM_PDF | 3 |
| Labels, barcode, carton count, bundle count | Not provided | NOT_PROVIDED | 3 |

## 10. Quality Requirements

| Requirement | Exact evidence | Confidence | Source page |
|---|---|---|---:|
| Layer thickness values | `20 �m`, `12 �m`, `85 �m` | CONFIRMED_FROM_PDF text; micron glyph UNCLEAR | 1 |
| Roll weight tolerance | `+ 5% / - 5%` | CONFIRMED_FROM_PDF | 3 |
| Roll length tolerance | `+ 5% / - 5%` | CONFIRMED_FROM_PDF | 3 |
| Roll diameter tolerance | `+ 5% / - 5%` | CONFIRMED_FROM_PDF | 3 |
| Coded layout tolerances | `+1 / -1` for the displayed D1/D2/D4 positions | CONFIRMED_FROM_PDF; column association inferred | 2 |
| Corona parameters | `C1 500` for A/B/C helper rows | CONFIRMED_FROM_PDF | 2-3 |
| Appearance/material attributes | Transparent, metalized, matte/gloss, sealable, corona, printed, reverse | CONFIRMED_FROM_PDF; some table-column associations UNCLEAR | 1 |
| Seal strength, bond strength, color delta, visual sampling | Not provided | NOT_PROVIDED | 1-3 |
| Inspection method/sampling | Not provided | NOT_PROVIDED | 1-3 |
| Food-contact requirement | Not provided | NOT_PROVIDED | 1-3 |

## 11. Production Information

| Information | Evidence | Classification | Source page |
|---|---|---|---:|
| Printing | `Print Tech: Classic`, print colors, print layout | CONFIRMED_FROM_PDF | 1 |
| Lamination | `A~B Solvent Based`; `AB~C Solvent Based` | CONFIRMED_FROM_PDF | 1 |
| Slitting | `SLITTED` in product title | CONFIRMED_FROM_PDF | 1 |
| Winding/roll output | Roll width, length, diameter, weight, core | CONFIRMED_FROM_PDF | 1, 3 |
| Packing/palletizing | Pallet size, rows, units, max height/weight | CONFIRMED_FROM_PDF | 3 |
| Extrusion | Not explicitly stated for this product sheet | NOT_PROVIDED | 1-3 |
| Prepress/tooling preparation | Plate mounting, cliché count, sleeve are listed; no process narrative | CONFIRMED_FROM_PDF for fields; process interpretation INFERRED | 1 |
| Process sequence | Lamination rows and title support printing/lamination/slitting; full routing is not stated | INFERRED | 1 |
| Machines/work centers | Not named; `Classic` is a print-tech value, not a confirmed machine | NOT_PROVIDED | 1-3 |

## 12. Raw Materials

This table lists identifiable physical materials only. The PDF does not establish whether the listed film layers are BOM lines, specification-only layers, or stocked intermediates.

| Material | Grade/Type | Thickness | Width | Quantity | Unit | Notes | Confidence |
|---|---|---|---|---:|---|---|---|
| BOPP | film layer A; transparent | `20 �m` | blank at layer level | blank | blank | Printed/reverse values appear in the layer block; `C1 500` corona helper | CONFIRMED_FROM_PDF; unit glyph UNCLEAR |
| PET | film layer B; metalized | `12 �m` | blank at layer level | blank | blank | `C1 500` corona helper; other treatment associations UNCLEAR | CONFIRMED_FROM_PDF; unit glyph UNCLEAR |
| PE | film layer C; transparent | `85 �m` | blank at layer level | blank | blank | Sealable/corona values appear; `C1 500` helper row | CONFIRMED_FROM_PDF; unit glyph UNCLEAR |
| Cardboard/paper core | `BBN CRDBRD`, raw core `11401980` | blank | core `500mm` length | `0.00` in Product Requirements | unit blank | Core title also contains `INTDM:3"`, `EXTDM:102.2mm`, `(13228)` | CONFIRMED_FROM_PDF; code semantics partly UNCLEAR |
| FirstPack PE sheet/bag | `JMBBG SHEET PE`, `TK:13�m`, `TRANS` | `13�m` in coded title | `WD:600mm` | `0.00` | unit blank | `LNG:1000mm`, `GS:SD:150mm`, `TUB:TUB`, `GRD:LD`, `(208)` | CONFIRMED_FROM_PDF; code semantics and micron glyph UNCLEAR |
| Adhesive | Not named | blank | blank | blank | blank | Solvent-based lamination is specified, but no adhesive material/grade is identified | NOT_PROVIDED |
| Ink | White spot-ready; Black process-ready | blank | blank | blank | blank | Ink family/process colors are specified; material grades/quantities are not | CONFIRMED_FROM_PDF for print definition; raw-material status INFERRED |

## 13. Manufacturing Interpretation

1. **Customer/product specification** — `NSYS Product Code 14445`, SP Code, SKU Code, title, dimensions, structure, print definition, and packing definition are **CONFIRMED_FROM_PDF** (page 1, with packing on page 3).
2. **Material structure** — ordered BOPP → PET → PE film layers are **CONFIRMED_FROM_PDF** (page 1). Treating this as a BOM is **INFERRED** and explicitly not established by the document.
3. **Printing** — a two-color definition with white spot-ready ink and black process-ready ink, reverse print side/layout, tooling fields, and repeat/sleeve values is **CONFIRMED_FROM_PDF** (page 1).
4. **Lamination** — solvent-based lamination entries A~B and AB~C are **CONFIRMED_FROM_PDF** (page 1).
5. **Slitting/roll output** — the title says `SLITTED`; roll dimensions and core requirements are **CONFIRMED_FROM_PDF** (pages 1 and 3).
6. **Packing/palletizing** — pallet dimensions and capacity constraints are **CONFIRMED_FROM_PDF** (page 3).
7. **Full chain `extrusion → printing → lamination → slitting → packing`** — the complete chain is **INFERRED** from the fields and is not fully narrated or machine-assigned by the PDF.

## 14. Field Dictionary

| PDF Field | Exact Value | Unit | Possible ERP Meaning | Confidence | Source Page |
|---|---|---|---|---|---:|
| Customer Product | `50         3` | blank | Customer product identity or variant fields | CONFIRMED_FROM_PDF; meaning UNCLEAR | 1 |
| NSYS Product Title | `MLTLYRFLM ROLL BOPP/PET/PE TK:117�m PRNT WD:500mm SLBL SLITTED JUMBO:1roll` | blank | Product specification title | CONFIRMED_FROM_PDF | 1 |
| NSYS Product Code | `14445` | blank | Internal product/customer-product code | CONFIRMED_FROM_PDF | 1 |
| SP Code | `42102000008225` | blank | Customer or external product code | CONFIRMED_FROM_PDF; ownership UNCLEAR | 1 |
| SKU Code | `14445.6059.1` | blank | SKU/product revision or variant code | CONFIRMED_FROM_PDF; derivation semantics UNCLEAR | 1 |
| Roll Width | `500` | mm | Finished roll width | CONFIRMED_FROM_PDF | 1 |
| Jumbo Roll Width | `1220` | mm | Input/master roll width | CONFIRMED_FROM_PDF | 1 |
| Opening Direction | `Outside` | blank | Winding/opening direction | CONFIRMED_FROM_PDF | 1 |
| Plate Mounting | `Simple` | blank | Printing tooling mounting method | CONFIRMED_FROM_PDF | 1 |
| No in Primeter | `2` | blank | Printing repeat/perimeter count | CONFIRMED_FROM_PDF; field meaning UNCLEAR | 1 |
| No Of Cliché in roll width | `1` | cliché | Tooling count across roll width | CONFIRMED_FROM_PDF | 1 |
| Sleeve | `760` | mm | Printing sleeve/repeat dimension | CONFIRMED_FROM_PDF | 1 |
| Repeat | `760` | mm | Print repeat length | CONFIRMED_FROM_PDF | 1 |
| Print Tech | `Classic` | blank | Print process/technology classification | CONFIRMED_FROM_PDF | 1 |
| FG UPS | `1` | blank | Finished-goods ups/stacking/pack parameter | CONFIRMED_FROM_PDF; meaning UNCLEAR | 1 |
| Print Side | `Inside` | blank | Surface/reverse print side | CONFIRMED_FROM_PDF | 1 |
| Layer A | `BOPP Transparent 20 �m` | micron likely | Ordered specification layer | CONFIRMED_FROM_PDF; unit glyph UNCLEAR | 1 |
| Layer B | `PET Metalized 12 �m` | micron likely | Ordered specification layer | CONFIRMED_FROM_PDF; unit glyph UNCLEAR | 1 |
| Layer C | `PE Transparent 85 �m` | micron likely | Ordered specification layer | CONFIRMED_FROM_PDF; unit glyph UNCLEAR | 1 |
| Lamination A~B | `Solvent Based` | blank | Lamination operation/type | CONFIRMED_FROM_PDF | 1 |
| Lamination AB~C | `Solvent Based` | blank | Lamination operation/type | CONFIRMED_FROM_PDF | 1 |
| Print color 1 | `White`, `Spot Ready Ink`, `Internal` | blank | Spec color/ink definition | CONFIRMED_FROM_PDF | 1 |
| Print color 2 | `Black`, `Process Ready Ink`, `--` | blank | Spec color/ink definition | CONFIRMED_FROM_PDF | 1 |
| BLK11 | `380, 500, 500, 0, 0, 0, 1, 14, 6, 0` under coded headings | unspecified | Converting/layout dimensional parameter set | CONFIRMED_FROM_PDF; meaning/unit UNCLEAR | 2 |
| BLK12 | `380, 500, 500, 0, 0, 0, 0, 14, 6, 0` under coded headings | unspecified | Converting/layout dimensional parameter set | CONFIRMED_FROM_PDF; meaning/unit UNCLEAR | 2 |
| Corona helper | `C1 500` for A, B, C | unspecified | Corona treatment parameter | CONFIRMED_FROM_PDF; characteristic meaning UNCLEAR | 2-3 |
| Core | `BBN CRDBRD ... RawCore: 11401980` | blank | Packaging/core material | CONFIRMED_FROM_PDF | 3 |
| FirstPack | `JMBBG SHEET PE ...` | blank | First/primary packaging requirement | CONFIRMED_FROM_PDF; meaning UNCLEAR | 3 |
| Roll weight | `71.00 +5%/-5%` | Kg / percent | Roll output target and tolerance | CONFIRMED_FROM_PDF | 3 |
| Roll length | `1,169.00 +5%/-5%` | m / percent | Roll output target and tolerance | CONFIRMED_FROM_PDF | 3 |
| Roll diameter | `440.00 +5%/-5%` | mm / percent | Roll output target and tolerance | CONFIRMED_FROM_PDF | 3 |
| Core's Weight | `1.50` | Kg | Core tare/weight specification | CONFIRMED_FROM_PDF | 3 |
| Pallet | `110*110 WOODEN` | unspecified dimension | Packaging/pallet specification | CONFIRMED_FROM_PDF | 3 |
| Pallet capacity | `3 rows; 12 max units; 170.00 cm; 900.00 Kg` | mixed | Palletization constraints | CONFIRMED_FROM_PDF | 3 |

## Potential ERP Gaps

These are documentation findings only. They do not prescribe implementation.

| PDF evidence | Possible ERP concept | Current representation, if any | Apparent gap | Confidence | Business decision required? |
|---|---|---|---|---|---|
| Detailed print fields: opening direction, plate mounting, perimeter count, cliché count, sleeve, repeat, FG UPS | Printing/tooling specification | Engineering spec has print process, number of colors, print side, and a first-class tooling asset; some extra fields can fit `SpecParameter` | No clearly dedicated representation for all print-tooling and winding parameters | CONFIRMED_FROM_PDF | YES |
| BOPP/PET/PE layer order with thickness and treatments | Ordered technical structure | `SpecLayer` supports ordered material, micron target, and tolerance | Treatment attributes such as reflection, sealability, corona, chemical treatment, and material color are not clearly first-class in the documented implementation; free parameters may be used | CONFIRMED_FROM_PDF | YES |
| Lamination rows `A~B` and `AB~C`, both `Solvent Based` | Layer-to-layer lamination operation and adhesive/process type | BOM/routing can represent operations and material lines; no explicit adhesive/coat-weight payload is listed in the implemented scope | No clearly dedicated structure for lamination pair sequence and adhesive details | CONFIRMED_FROM_PDF | YES |
| Roll weight, roll length, roll diameter, core weight, each with tolerances | Roll/output packaging specification | Roll/lot execution is gated; engineering header has dimensions but not roll packaging details | Roll output and winding constraints are not currently represented in the implemented definition layer | CONFIRMED_FROM_PDF | YES |
| Core and FirstPack coded requirements with amount `0.00` and blank units | Packaging materials and packaging instructions | `catalog.Material` and BOM lines exist; packaging subtype exists | Requirement amount semantics, unit, operation, and pallet/packaging instruction structure are unclear or absent | CONFIRMED_FROM_PDF | YES |
| Page-2 BLK11/BLK12 coded dimensions and `+1/-1` limits | Converting/layout parameter set | Free-form `SpecParameter` can hold values; no documented semantic dictionary | No confirmed model/field dictionary for these coded dimensions and their units | CONFIRMED_FROM_PDF | YES |
| Product date/time and no visible revision/status | Specification revision metadata | Engineering has revision number/status/effective dates; product sheet date is not mapped | Document issue date vs. revision/effectivity and source-document attachment need explicit linkage | CONFIRMED_FROM_PDF | YES |
| No QC execution values, methods, or sampling; only limits/targets | Quality plan and check execution | Quality plan definition supports characteristics, limits, stage labels, sampling; execution is gated | PDF-specific inspection method/sampling and execution evidence are absent | CONFIRMED_FROM_PDF / NOT_PROVIDED | YES |

## Questions Raised By This Product

- Is the PDF date/time (`2026-08-22 21:03:35`) a generated extraction/print timestamp, a product-sheet issue date, or an effective revision date?
- What does the `Customer Product` value `50         3` represent?
- Is the filename's Libaro/coffee/one-kilogram/side-gusset description the authoritative customer/product identity when `Customer Name` is blank in the PDF?
- Does `TK:117�m` represent the sum of the three layer thicknesses, and should the micron glyph be retained exactly as rendered?
- Which reflection, sealability, corona, and chemical values belong to each specific layer? The text layout does not preserve this column association reliably.
- What do the coded page-2 fields `BLK`, `A`, `B1`, `H1`, `K1`, `K2`, `R1`, `R2`, `D1`, `D2`, and `D4` mean, and what units apply?
- Are the `+1/-1` limits on page 2 dimensional tolerances for D1/D2/D4, or do they apply to another grouping in the diagram?
- What does `FG UPS: 1` mean operationally?
- Are the Product Requirements amounts `0.00` actual zero quantities, placeholders, or missing quantities? Why are units and operations blank?
- Is `FirstPack` part of the product's manufacturing/packaging specification or a separately stocked item?
- Are `42102000008227` and `42102000008226` edited-roll references, related codes, or comments?
- Is the listed solvent-based lamination sequence the complete routing, or are extrusion, curing, slitting, inspection, and packing steps omitted from this sheet?
- Is the `Cardboard` value a divider, an upper guard, or another pallet component?

## 17. Source-of-Truth Conflicts

No direct contradiction was established from the inspected evidence. The following items require review rather than resolution:

- `CONFLICT_REQUIRES_REVIEW`: The product sheet presents an operational-looking layer/lamination/packing definition, while the ERP source of truth distinguishes a technical specification from a BOM/routing and explicitly leaves which intermediates are inventoried open (`Q-026`). The sheet does not state that its layers or requirements are a BOM.
- `CONFLICT_REQUIRES_REVIEW`: The sheet has a `SKU Code`, while the current ERP documentation says the product coding/numbering scheme remains open (`Q-019` / `NQ-005`) and the implemented `CustomerProduct.code` is manual. This is evidence of a code, not proof of the future derivation rule.

