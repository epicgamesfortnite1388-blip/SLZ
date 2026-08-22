# Sample Product

## 1. Document Metadata

| Field | Value | Confidence | Source |
|---|---|---|---|
| Source PDF filename | `Product Data Sheet - کیسه پوشک هانیز سایز 3-38 عددی سایز متوسط.pdf` | CONFIRMED_FROM_PDF filename | Repository path |
| Page count | 3 | CONFIRMED_FROM_PDF | PDF page sequence |
| Document title | `Product Data Sheet` | CONFIRMED_FROM_PDF | PDF page 1 |
| Generator/system label | `NSYS` | CONFIRMED_FROM_PDF | PDF page 1 |
| Printed document date/time | `2026-08-22 21:09:42` | CONFIRMED_FROM_PDF | PDF page 1 |
| Customer | Blank in the PDF field | NOT_PROVIDED | PDF page 1 |
| Product code | `12975` (NSYS Product Code) | CONFIRMED_FROM_PDF | PDF page 1 |
| Customer product field | `38-3` | CONFIRMED_FROM_PDF | PDF page 1 |
| SP Code | `41061300602927` | CONFIRMED_FROM_PDF | PDF page 1 |
| SKU Code | `12975.3278.1` | CONFIRMED_FROM_PDF | PDF page 1 |
| Revision | Not shown | NOT_PROVIDED | PDF pages 1-3 |
| Status | Not shown | NOT_PROVIDED | PDF pages 1-3 |

The Persian filename identifies this as a Honey's diaper bag, size 3, 38-count, medium size. The customer-name field itself is blank, so that customer identity is retained as filename evidence only.

## 2. Raw Transcription

### PDF page 1

Visible labels and values, preserving source wording/casing and coded text:

```text
Product Data Sheet                                             NSYS
2026-08-22 21:09:42

Customer Product: 38-3
NSYS Product Title:
HYGNCBG SHEET PE TK:60�m WHITE PRNT SL:SD HNDL:LNR WD:70mm:TRANS
GS:BTN:54mm SPRFRTN RLZC:1 VNT:STR IHL:1 CORONA:1 WKT:42mm WKTHL
GRD:LD WD:386mm LNG:352mm BNDL:80pcs-SPNDL CARTON:11 BNDLS
Customer Name: [blank]
NSYS Product Code: 12975
SP Code: 41061300602927
SKU Code: 12975.3278.1
```

Film and printing header fields:

| PDF field | Exact value | Source page |
|---|---|---:|
| Roll Width (mm) | `770` with `+5 / -5` | 1 |
| Jumbo Roll Width (mm) | `770` with `+5 / -5` | 1 |
| Opening Direction | `Outside` | 1 |
| Plate Mounting | `Simple` | 1 |
| No in Primeter | `2` | 1 |
| No Of Cliché in roll width | `1` | 1 |
| Sleeve (mm) | `780` | 1 |
| Repeat (mm) | `776` with `+3 / -3` | 1 |
| Print Tech | `Classic` | 1 |
| FG UPS | `1` | 1 |
| Print Side | `Outside` | 1 |

Film Layers table:

| Layer | Material | Material Color | Thickness | Tolerance | Grammage | Grammage Tolerance | Reflection | Sealability | Corona | Chemical | Print | Print Type | Color Count | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---:|---|
| A | `PE` | `White` | `60 �m` | `+3 / -3` | blank | blank | `Matte` appears in the row block | `Sealable` appears in the row block | `Corona` appears in the row block | blank | `Printed` | `Surface` | `7` | Material/color/thickness/tolerance/print values CONFIRMED_FROM_PDF; treatment-column association partly UNCLEAR |

A second `Matte`, `Sealable`, and `0` row appears below the A row in the extracted layout. It is not clear whether this is a continuation/alternate row, a second rendering of the layer properties, or a table-alignment artifact. It is preserved as **UNCLEAR**, not discarded.

Print Colors table:

| Action Title | Ink Family | Process Ink Color | Spot Ink Coding | Spot Ink Code | Trama | Solid | Lpi | Confidence |
|---:|---|---|---|---|---|---|---|---|
| `1` | `Process Ready Ink` | `Cyan` | `--` | blank | blank | blank | `136` | CONFIRMED_FROM_PDF |
| `2` | `Process Ready Ink` | `Magenta` | `--` | `326 C` appears in the next code column | blank | blank | `136` | CONFIRMED_FROM_PDF; exact code-column alignment follows PDF layout |
| `3` | `Process Ready Ink` | `Yellow` | `--` | `317 C` appears in the next code column | blank | blank | `136` | CONFIRMED_FROM_PDF; exact code-column alignment follows PDF layout |
| `4` | `Spot Ready Ink` | `--` | `Pantone` | `266 C` | blank | blank | `136` | CONFIRMED_FROM_PDF |
| `5` | `Spot Ready Ink` | `--` | `Pantone` | `honeys gold` | blank | blank | `136` | CONFIRMED_FROM_PDF |
| `6` | `Spot Ready Ink` | `--` | `Pantone` | blank | blank | blank | `136` | CONFIRMED_FROM_PDF; Pantone code/name not populated |
| `7` | `Spot Ready Ink` | `--` | `Internal` | blank | blank | blank | `136` | CONFIRMED_FROM_PDF |

The source table also shows `Action Title` rows 1 through 7. The values `326 C`, `317 C`, `266 C`, `honeys gold`, and the blank sixth spot-code position are preserved exactly as text-layer output.

Print layout:

```text
OUTPUT FILM
Print Layout [PE White 60�m Surface]
```

The micron symbol is emitted as `�` by the text layer; its rendered character is UNCLEAR in this extraction.

### PDF page 2

The page contains the coded output/layout diagram with headings:

`BLK | A | B1 | H1 | K1 | K2 | R1 | R2 | D1 | D2 | D4`

The two visible block rows are identical in nominal values:

| Block | A | B1 | H1 | K1 | K2 | R1 | R2 | D1 | D2 | D4 | Source page |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `BLK11` | `388` | `770` | `558` | `127` | `85` | `7` | `7` | `0` | `0` | `0` | 2 |
| `BLK12` | `388` | `770` | `558` | `127` | `85` | `7` | `7` | `0` | `0` | `0` | 2 |

Visible tolerances in the same diagram:

| Parameter group | Tolerance evidence | Confidence | Source page |
|---|---|---|---:|
| A | `+3 / -3` | CONFIRMED_FROM_PDF | 2 |
| B1 | `+5 / -5` | CONFIRMED_FROM_PDF | 2 |
| H1 | `+3 / -3` | CONFIRMED_FROM_PDF | 2 |
| K1 | `+2 / -2` | CONFIRMED_FROM_PDF | 2 |
| K2 | `+2 / -2` | CONFIRMED_FROM_PDF | 2 |
| R1 | `+1 / -1` | CONFIRMED_FROM_PDF | 2 |
| R2 | `+1 / -1` | CONFIRMED_FROM_PDF | 2 |
| D1 | `+1 / -1` | CONFIRMED_FROM_PDF | 2 |
| D2 | `+1 / -1` | CONFIRMED_FROM_PDF | 2 |
| D4 | `+1 / -1` | CONFIRMED_FROM_PDF | 2 |

The diagram also shows `BLK Parameter Helper` and a corona helper:

| Layer | Material | Corona Parameters | Source page |
|---|---|---|---:|
| A | `PE` | `C1 578 + 5 - 5`; `CL 117 + 5 - 5`; `CR 75 + 5 - 5` | 2 |

`C1`, `CL`, and `CR` are preserved as source codes. Their physical meaning and units are **UNCLEAR**.

### PDF page 3

The page contains a converting code/value matrix and pallet information.

Converting headings and exact nominal values:

| Code | Value | Tolerance | Source page |
|---|---:|---|---:|
| `V` | `42` | `+4 / -4` | 3 |
| `M` | `14` | `+2 / -2` | 3 |
| `M1` | `59` | `+5 / -5` | 3 |
| `M2` | `13` | `+3 / -3` | 3 |
| `M3` | `254` | `+1 / -1` | 3 |
| `M4` | `22` | `+2 / -2` | 3 |
| `J` | `6` | `+2 / -2` | 3 |
| `J1` | `9` | `+2 / -2` | 3 |
| `J2` | `13` | `+2 / -2` | 3 |
| `I` | `7` | `+2 / -2` | 3 |
| `I1` | `50` | `+2 / -2` | 3 |
| `S1` | `91` | `+3 / -3` | 3 |
| `S3` | `10` | `+5 / -5` | 3 |
| `W` | `93` | `+3 / -3` | 3 |
| `W1` | `30` | `+3 / -3` | 3 |
| `Y` | `386` | `+2 / -2` | 3 |
| `U` | `70` | `+2 / -2` | 3 |
| `U1` | `10` | `+2 / -2` | 3 |
| `Q` | `17` | `+2 / -2` | 3 |
| `K1` | `127` | `+3 / -3` | 3 |
| `K2` | `85` | `+3 / -3` | 3 |
| `R1` | `6` | `+2 / -2` | 3 |
| `R2` | `6` | `+2 / -2` | 3 |
| `G` | `54` | `+3 / -3` | 3 |
| `N` | `386` | `+3 / -3` | 3 |
| `P` | `352` | `+5 / -5` | 3 |

Additional converting flags/text:

| Field | Exact value | Confidence | Source page |
|---|---|---|---:|
| Handle | `Yes` | CONFIRMED_FROM_PDF | 3 |
| Slit | `17` appears adjacent to the converting labels; exact field association is UNCLEAR | CONFIRMED_FROM_PDF text; association UNCLEAR | 3 |

Pallet information:

| Field | Exact value | Source page |
|---|---|---:|
| Pallet | `PALLET SIZE:110*130 WOODEN` | 3 |
| Upper guard / associated material | `Plastic` appears in the pallet table; exact column association is UNCLEAR | 3 |
| Number Of Rows | `6` | 3 |
| Max Units | `60` | 3 |
| Max Height (Cm) | `160.00` | 3 |
| Max Weight (Kg) | `900.00` | 3 |
| Divider | blank or not legible as a separate value | 3 |
| Stretch Wrapping | blank or not legible as a separate value | 3 |
| Belt | blank or not legible as a separate value | 3 |

No hand-written annotation, signature, or separate raster drawing was exposed by the PDF text extraction. The page-2 and page-3 content is a technical coded diagram/table.

## 3. Product Identity

| Field | Exact value | Confidence | Source page |
|---|---|---|---:|
| Customer | blank | NOT_PROVIDED | 1 |
| Product name/title | `HYGNCBG SHEET PE TK:60�m WHITE PRNT SL:SD HNDL:LNR WD:70mm:TRANS GS:BTN:54mm SPRFRTN RLZC:1 VNT:STR IHL:1 CORONA:1 WKT:42mm WKTHL GRD:LD WD:386mm LNG:352mm BNDL:80pcs-SPNDL CARTON:11 BNDLS` | CONFIRMED_FROM_PDF | 1 |
| Product code | `12975` | CONFIRMED_FROM_PDF | 1 |
| Customer product code | `38-3` | CONFIRMED_FROM_PDF | 1 |
| SP Code | `41061300602927` | CONFIRMED_FROM_PDF | 1 |
| SKU Code | `12975.3278.1` | CONFIRMED_FROM_PDF | 1 |
| Revision | blank | NOT_PROVIDED | 1 |
| Status | blank | NOT_PROVIDED | 1 |
| Date | `2026-08-22 21:09:42` | CONFIRMED_FROM_PDF; date role UNCLEAR | 1 |

Possible meanings of title abbreviations are intentionally not asserted:

| Token | Possible meaning | Confidence |
|---|---|---|
| `HYGNCBG` | Possible hygiene bag product family code | POSSIBLE_MEANING |
| `TK` | Possible thickness | POSSIBLE_MEANING |
| `PRNT` | Possible printed | POSSIBLE_MEANING |
| `SL:SD` | Possible seal/construction code | POSSIBLE_MEANING |
| `HNDL:LNR` | Possible liner handle | POSSIBLE_MEANING |
| `GS:BTN` | Possible bottom gusset | POSSIBLE_MEANING |
| `SPRFRTN` | Possible perforation/tear feature | POSSIBLE_MEANING |
| `RLZC:1` | Possible roll/relaxation/count parameter | UNCLEAR |
| `VNT:STR` | Possible vent/structure code | UNCLEAR |
| `IHL:1` | Coded parameter; meaning UNCLEAR | UNCLEAR |
| `WKT:42mm` | Coded width/feature value | POSSIBLE_MEANING |
| `WKTHL` | Coded feature/handle label | UNCLEAR |
| `GRD:LD` | Possible grade low-density | POSSIBLE_MEANING |
| `WD`, `LNG`, `BNDL`, `SPNDL`, `CARTON`, `BNDLS` | Width, length, bundle and carton-related codes are possible readings; exact system dictionary not provided | POSSIBLE_MEANING |

## 4. Dimensions

### Film and print dimensions

| Dimension/parameter | Exact value | Unit | Tolerance | Confidence | Source page |
|---|---:|---|---|---|---:|
| Finished roll width | `770` | mm | `+5 / -5` | CONFIRMED_FROM_PDF | 1 |
| Jumbo roll width | `770` | mm | `+5 / -5` | CONFIRMED_FROM_PDF | 1 |
| Repeat | `776` | mm | `+3 / -3` | CONFIRMED_FROM_PDF | 1 |
| Sleeve | `780` | mm | blank | CONFIRMED_FROM_PDF | 1 |
| Layer thickness | `60 �m` | micron glyph UNCLEAR | `+3 / -3` | CONFIRMED_FROM_PDF text; unit glyph UNCLEAR | 1 |

### Coded block dimensions, PDF page 2

| Code | Exact value | Tolerance | Unit | Confidence |
|---|---:|---|---|---|
| `A` | `388` | `+3 / -3` | not provided | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR |
| `B1` | `770` | `+5 / -5` | not provided | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR |
| `H1` | `558` | `+3 / -3` | not provided | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR |
| `K1` | `127` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR |
| `K2` | `85` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR |
| `R1` | `7` | `+1 / -1` | not provided | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR |
| `R2` | `7` | `+1 / -1` | not provided | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR |
| `D1` | `0` | `+1 / -1` | not provided | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR |
| `D2` | `0` | `+1 / -1` | not provided | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR |
| `D4` | `0` | `+1 / -1` | not provided | CONFIRMED_FROM_PDF; semantic meaning UNCLEAR |

### Converting dimensions, PDF page 3

The codes and values below are transcribed from the converting diagram. The PDF provides no legend defining the code names or units.

| Code | Value | Tolerance | Unit | Confidence |
|---|---:|---|---|---|
| `V` | `42` | `+4 / -4` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `M` | `14` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `M1` | `59` | `+5 / -5` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `M2` | `13` | `+3 / -3` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `M3` | `254` | `+1 / -1` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `M4` | `22` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `J` | `6` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `J1` | `9` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `J2` | `13` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `I` | `7` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `I1` | `50` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `S1` | `91` | `+3 / -3` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `S3` | `10` | `+5 / -5` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `W` | `93` | `+3 / -3` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `W1` | `30` | `+3 / -3` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `Y` | `386` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `U` | `70` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `U1` | `10` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `Q` | `17` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `K1` | `127` | `+3 / -3` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `K2` | `85` | `+3 / -3` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `R1` | `6` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `R2` | `6` | `+2 / -2` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `G` | `54` | `+3 / -3` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `N` | `386` | `+3 / -3` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |
| `P` | `352` | `+5 / -5` | not provided | CONFIRMED_FROM_PDF; code meaning UNCLEAR |

## 5. Material Structure

The PDF explicitly lists one film layer. It does not explicitly call it a BOM.

| Layer | Material | Thickness | Treatment/appearance shown | Notes | Confidence | Source page |
|---|---|---|---|---|---|---:|
| A | `PE` | `60 �m`, tolerance `+3 / -3` | `White`; `Matte`; `Sealable`; `Corona`; `Printed`; `Surface`; color count `7` | A second `Matte/Sealable/0` row is present in extracted layout but its role is UNCLEAR | CONFIRMED_FROM_PDF for source values; row association partly UNCLEAR | 1 |

Corona helper values:

| Layer | Material | Corona parameters | Confidence | Source page |
|---|---|---|---|---:|
| A | `PE` | `C1 578 + 5 - 5`; `CL 117 + 5 - 5`; `CR 75 + 5 - 5` | CONFIRMED_FROM_PDF; code meanings/units UNCLEAR | 2 |

No resin grade, additive, ink quantity, packaging-material quantity, or BOM relationship is explicitly provided.

## 6. Printing

| Field | Exact value | Confidence | Source page |
|---|---|---|---:|
| Print technology | `Classic` | CONFIRMED_FROM_PDF | 1 |
| Print side | `Outside` | CONFIRMED_FROM_PDF | 1 |
| Print type/layout | `Surface`; `Print Layout [PE White 60�m Surface]` | CONFIRMED_FROM_PDF; micron glyph UNCLEAR | 1 |
| Number of colors | `7` in the PE layer table and seven action rows | CONFIRMED_FROM_PDF | 1 |
| Color 1 | `Cyan` | CONFIRMED_FROM_PDF | 1 |
| Color 1 ink family | `Process Ready Ink` | CONFIRMED_FROM_PDF | 1 |
| Color 2 | `Magenta` | CONFIRMED_FROM_PDF | 1 |
| Color 2 ink family | `Process Ready Ink` | CONFIRMED_FROM_PDF | 1 |
| Color 2 code value | `326 C` appears in the spot-code column position | CONFIRMED_FROM_PDF; exact field association follows table position | 1 |
| Color 3 | `Yellow` | CONFIRMED_FROM_PDF | 1 |
| Color 3 ink family | `Process Ready Ink` | CONFIRMED_FROM_PDF | 1 |
| Color 3 code value | `317 C` appears in the spot-code column position | CONFIRMED_FROM_PDF; exact field association follows table position | 1 |
| Color 4 | `--` process color; spot-ready | CONFIRMED_FROM_PDF | 1 |
| Color 4 spot coding/code | `Pantone` / `266 C` | CONFIRMED_FROM_PDF | 1 |
| Color 5 | `--` process color; spot-ready | CONFIRMED_FROM_PDF | 1 |
| Color 5 spot coding/code | `Pantone` / `honeys gold` | CONFIRMED_FROM_PDF | 1 |
| Color 6 | `--` process color; spot-ready | CONFIRMED_FROM_PDF | 1 |
| Color 6 spot coding/code | `Pantone` / blank | CONFIRMED_FROM_PDF; code not provided | 1 |
| Color 7 | `--` process color; spot-ready | CONFIRMED_FROM_PDF | 1 |
| Color 7 spot coding/code | `Internal` / blank | CONFIRMED_FROM_PDF | 1 |
| Lpi | `136` for each of the seven action rows | CONFIRMED_FROM_PDF | 1 |
| Plate mounting | `Simple` | CONFIRMED_FROM_PDF | 1 |
| Number in perimeter | `2` | CONFIRMED_FROM_PDF; field meaning UNCLEAR | 1 |
| Cliché count in roll width | `1` | CONFIRMED_FROM_PDF | 1 |
| Sleeve | `780` mm | CONFIRMED_FROM_PDF | 1 |
| Repeat | `776` mm with `+3 / -3` | CONFIRMED_FROM_PDF | 1 |
| FG UPS | `1` | CONFIRMED_FROM_PDF; meaning UNCLEAR | 1 |
| Artwork/file information | Not provided as a named artwork file | NOT_PROVIDED | 1-3 |
| Registration tolerance | Not explicitly labelled | NOT_PROVIDED | 1-3 |

The PDF text layer places `326 C` and `317 C` under the spot-code column position even though they occur adjacent to Magenta and Yellow rows. The exact visual field mapping should be confirmed from the rendered source if these codes are to drive ERP color records.

## 7. Finishing / Conversion

| Operation or feature | Exact evidence | Confidence | Source page |
|---|---|---|---:|
| Converting | `Converting` section and page-3 converting matrix | CONFIRMED_FROM_PDF | 2-3 |
| Handle | `Handle: Yes` | CONFIRMED_FROM_PDF | 3 |
| Slit | `Slit` label with adjacent value `17`; exact association is UNCLEAR | CONFIRMED_FROM_PDF text; association UNCLEAR | 3 |
| Seal/construction code | `SL:SD` in title | CONFIRMED_FROM_PDF; expansion UNCLEAR | 1 |
| Gusset/feature code | `GS:BTN:54mm:TRANS` in title | CONFIRMED_FROM_PDF; exact code semantics partly UNCLEAR | 1 |
| Perforation/tear code | `SPRFRTN` in title | CONFIRMED_FROM_PDF; possible meaning only | 1 |
| Vent/structure code | `VNT:STR` in title | CONFIRMED_FROM_PDF; meaning UNCLEAR | 1 |
| Lamination | Not provided | NOT_PROVIDED | 1-3 |
| Zipper, valve, punching, folding | Not provided as explicit named operations | NOT_PROVIDED | 1-3 |

Converting matrix values are listed in the Dimensions section because the PDF gives only coded geometry and tolerances, without a legend or operation narrative.

## 8. Quantity / Commercial Information

| Field | Exact value | Unit | Confidence | Source page |
|---|---:|---|---|---:|
| Customer product title bundle value | `BNDL:80pcs` | pcs | CONFIRMED_FROM_PDF; likely bundle quantity only as a possible meaning | 1 |
| Customer product title carton value | `CARTON:11 BNDLS` | bundles | CONFIRMED_FROM_PDF; exact grammar/meaning partly UNCLEAR | 1 |
| Pallet max units | `60` | units | CONFIRMED_FROM_PDF | 3 |
| Pallet max weight | `900.00` | Kg | CONFIRMED_FROM_PDF | 3 |
| Order quantity | Not provided | blank | NOT_PROVIDED | 1-3 |
| Production quantity | Not provided | blank | NOT_PROVIDED | 1-3 |
| Over/under allowance | Not provided | blank | NOT_PROVIDED | 1-3 |

`BNDL:80pcs` and `CARTON:11 BNDLS` are product-title attributes, not an explicit sales order quantity or production quantity.

## 9. Packaging

| Packaging field | Exact value | Confidence | Source page |
|---|---|---|---:|
| Bundle quantity in title | `80pcs` | CONFIRMED_FROM_PDF; unit/role direct, bundle interpretation possible | 1 |
| Carton quantity in title | `11 BNDLS` | CONFIRMED_FROM_PDF; exact field semantics partly UNCLEAR | 1 |
| Pallet | `PALLET SIZE:110*130 WOODEN` | CONFIRMED_FROM_PDF | 3 |
| Upper guard / associated material | `Plastic` appears in pallet table; exact column association UNCLEAR | 3 |
| Number of rows | `6` | CONFIRMED_FROM_PDF | 3 |
| Maximum units | `60` | CONFIRMED_FROM_PDF | 3 |
| Maximum height | `160.00` | Cm | CONFIRMED_FROM_PDF | 3 |
| Maximum weight | `900.00` | Kg | CONFIRMED_FROM_PDF | 3 |
| Divider, stretch wrapping, belt | blank or not legible as separate values | UNCLEAR / NOT_PROVIDED | 3 |
| Label/barcode/pallet label | Not provided | NOT_PROVIDED | 3 |

## 10. Quality Requirements

| Requirement | Exact evidence | Confidence | Source page |
|---|---|---|---:|
| Layer thickness | `60 �m` | CONFIRMED_FROM_PDF text; unit glyph UNCLEAR | 1 |
| Layer thickness tolerance | `+3 / -3` | CONFIRMED_FROM_PDF | 1 |
| Roll width tolerance | `+5 / -5` | CONFIRMED_FROM_PDF | 1 |
| Repeat tolerance | `+3 / -3` | CONFIRMED_FROM_PDF | 1 |
| Coded block tolerances | Values from `+1/-1` through `+5/-5` as listed on page 2 | CONFIRMED_FROM_PDF; parameter meanings/units UNCLEAR | 2 |
| Corona parameters | `C1 578 +5 -5`, `CL 117 +5 -5`, `CR 75 +5 -5` | CONFIRMED_FROM_PDF; codes/units UNCLEAR | 2 |
| Converting dimensions | All page-3 code/value/tolerance rows | CONFIRMED_FROM_PDF | 3 |
| Visual/material attributes | White PE, matte, sealable, corona, surface print | CONFIRMED_FROM_PDF; some table-column mapping UNCLEAR | 1 |
| Seal strength, leak/burst, color delta, sampling method | Not provided | NOT_PROVIDED | 1-3 |
| Food-contact requirement | Not provided | NOT_PROVIDED | 1-3 |

## 11. Production Information

| Information | Evidence | Classification | Source page |
|---|---|---|---:|
| Film input/print substrate | Single PE layer, `60 �m`, white | CONFIRMED_FROM_PDF | 1 |
| Printing | Classic, seven colors, surface/outside print | CONFIRMED_FROM_PDF | 1 |
| Converting | `Converting` section and detailed page-3 code/value matrix | CONFIRMED_FROM_PDF | 2-3 |
| Handle operation/feature | `Handle Yes` | CONFIRMED_FROM_PDF | 3 |
| Slit feature/operation | `Slit` with adjacent `17` | CONFIRMED_FROM_PDF text; exact association UNCLEAR | 3 |
| Packing/palletizing | Pallet size and capacity constraints | CONFIRMED_FROM_PDF | 3 |
| Extrusion | Not explicitly stated | NOT_PROVIDED | 1-3 |
| Lamination | Not provided | NOT_PROVIDED | 1-3 |
| Machines/work centers | Not named | NOT_PROVIDED | 1-3 |
| Full process sequence | Printing → converting → palletizing is supported at a high level; exact sequence is not narrated | INFERRED | 1-3 |

## 12. Raw Materials

| Material | Grade/Type | Thickness | Width | Quantity | Unit | Notes | Confidence |
|---|---|---|---|---:|---|---|---|
| PE | film layer A; white | `60 �m`, tolerance `+3 / -3` | layer width blank; roll width `770` mm with `+5/-5` | blank | blank | Corona, sealable, surface printed; grade title code `GRD:LD` is retained but expansion is not asserted | CONFIRMED_FROM_PDF; unit glyph and grade meaning partly UNCLEAR |
| Cyan ink | `Process Ready Ink` | blank | blank | blank | blank | Action 1; Lpi `136` | CONFIRMED_FROM_PDF for print definition; raw-material quantity NOT_PROVIDED |
| Magenta ink | `Process Ready Ink` | blank | blank | blank | blank | Action 2; `326 C` appears adjacent in code column position; Lpi `136` | CONFIRMED_FROM_PDF; exact code mapping UNCLEAR |
| Yellow ink | `Process Ready Ink` | blank | blank | blank | blank | Action 3; `317 C` appears adjacent in code column position; Lpi `136` | CONFIRMED_FROM_PDF; exact code mapping UNCLEAR |
| Spot ink 4 | `Spot Ready Ink` | blank | blank | blank | blank | Pantone; code `266 C`; Lpi `136` | CONFIRMED_FROM_PDF |
| Spot ink 5 | `Spot Ready Ink` | blank | blank | blank | blank | Pantone; code/name `honeys gold`; Lpi `136` | CONFIRMED_FROM_PDF |
| Spot ink 6 | `Spot Ready Ink` | blank | blank | blank | blank | Pantone; code blank; Lpi `136` | CONFIRMED_FROM_PDF |
| Spot ink 7 | `Spot Ready Ink` | blank | blank | blank | blank | Internal coding; code blank; Lpi `136` | CONFIRMED_FROM_PDF |
| Packaging material | Pallet `110*130 WOODEN`; `Plastic` appears in pallet table | blank | blank | blank | blank | Exact pallet-component column association UNCLEAR | CONFIRMED_FROM_PDF |

## 13. Manufacturing Interpretation

1. **Customer/product specification** — `38-3`, product code `12975`, SP Code, SKU Code, coded bag title, structure, print, converting, and packaging values are **CONFIRMED_FROM_PDF**.
2. **Material structure** — one PE layer, white, `60 �m`, with `+3/-3` tolerance is **CONFIRMED_FROM_PDF**. Treating it as a BOM line is **INFERRED** and not established by the sheet.
3. **Printing** — seven-color surface/outside print using three process-ready colors plus four spot-ready/internal color definitions is **CONFIRMED_FROM_PDF**.
4. **Converting** — a detailed coded dimension matrix, handle flag, and slit-related value are **CONFIRMED_FROM_PDF**; the operational mapping of codes is **UNCLEAR**.
5. **Palletizing** — a wooden `110*130` pallet with six rows, sixty maximum units, and maximum height/weight limits is **CONFIRMED_FROM_PDF**.
6. **Full chain `film → printing → converting → packing`** — supported as a high-level **INFERRED** interpretation; extrusion, raw-material compounding, QC execution, and machine assignment are not stated.

## 14. Field Dictionary

| PDF Field | Exact Value | Unit | Possible ERP Meaning | Confidence | Source Page |
|---|---|---|---|---|---:|
| Customer Product | `38-3` | blank | Customer product identity/size | CONFIRMED_FROM_PDF | 1 |
| NSYS Product Title | `HYGNCBG SHEET PE TK:60�m WHITE PRNT SL:SD HNDL:LNR WD:70mm:TRANS GS:BTN:54mm SPRFRTN RLZC:1 VNT:STR IHL:1 CORONA:1 WKT:42mm WKTHL GRD:LD WD:386mm LNG:352mm BNDL:80pcs-SPNDL CARTON:11 BNDLS` | blank | Product specification title | CONFIRMED_FROM_PDF | 1 |
| NSYS Product Code | `12975` | blank | Internal product/customer-product code | CONFIRMED_FROM_PDF | 1 |
| SP Code | `41061300602927` | blank | Customer or external product code | CONFIRMED_FROM_PDF; ownership UNCLEAR | 1 |
| SKU Code | `12975.3278.1` | blank | SKU/product revision or variant code | CONFIRMED_FROM_PDF; derivation semantics UNCLEAR | 1 |
| Roll Width | `770 +5/-5` | mm / percent | Film/roll width target and tolerance | CONFIRMED_FROM_PDF | 1 |
| Jumbo Roll Width | `770 +5/-5` | mm / percent | Master/input roll width target and tolerance | CONFIRMED_FROM_PDF | 1 |
| Opening Direction | `Outside` | blank | Winding/opening direction | CONFIRMED_FROM_PDF | 1 |
| Plate Mounting | `Simple` | blank | Printing tooling mounting method | CONFIRMED_FROM_PDF | 1 |
| No in Primeter | `2` | blank | Printing repeat/perimeter count | CONFIRMED_FROM_PDF; meaning UNCLEAR | 1 |
| No Of Cliché in roll width | `1` | cliché | Tooling count across roll width | CONFIRMED_FROM_PDF | 1 |
| Sleeve | `780` | mm | Printing sleeve dimension | CONFIRMED_FROM_PDF | 1 |
| Repeat | `776 +3/-3` | mm / tolerance | Print repeat length and tolerance | CONFIRMED_FROM_PDF | 1 |
| Print Tech | `Classic` | blank | Print process classification | CONFIRMED_FROM_PDF | 1 |
| FG UPS | `1` | blank | Finished-goods packaging/stacking parameter | CONFIRMED_FROM_PDF; meaning UNCLEAR | 1 |
| Print Side | `Outside` | blank | Surface print side | CONFIRMED_FROM_PDF | 1 |
| Layer A | `PE White 60 �m +3/-3` | micron likely | Ordered specification layer | CONFIRMED_FROM_PDF; unit glyph UNCLEAR | 1 |
| Color count | `7` | colors | Print definition | CONFIRMED_FROM_PDF | 1 |
| Print colors | Cyan, Magenta, Yellow, 266 C, honeys gold, blank Pantone, Internal | blank | Spec color/ink slots | CONFIRMED_FROM_PDF; some code alignment UNCLEAR | 1 |
| Corona helper | `C1 578 +5/-5; CL 117 +5/-5; CR 75 +5/-5` | unspecified | Surface-treatment quality/parameter fields | CONFIRMED_FROM_PDF; meanings/units UNCLEAR | 2 |
| Converting codes | `V`, `M`, `M1`, `M2`, `M3`, `M4`, `J`, `J1`, `J2`, `I`, `I1`, `S1`, `S3`, `W`, `W1`, `Y`, `U`, `U1`, `Q`, `K1`, `K2`, `R1`, `R2`, `G`, `N`, `P` | unspecified | Converting geometry/feature parameters | CONFIRMED_FROM_PDF; code dictionary absent | 3 |
| Handle | `Yes` | boolean | Converting feature requirement | CONFIRMED_FROM_PDF | 3 |
| Slit | `17` adjacent to label | unspecified | Slit/feature parameter | CONFIRMED_FROM_PDF text; association UNCLEAR | 3 |
| Bundle | `80pcs` | pieces | Bundle/packaging quantity | CONFIRMED_FROM_PDF; role partly UNCLEAR | 1 |
| Carton | `11 BNDLS` | bundles | Carton packaging quantity | CONFIRMED_FROM_PDF; role partly UNCLEAR | 1 |
| Pallet | `110*130 WOODEN` | unspecified dimension | Pallet specification | CONFIRMED_FROM_PDF | 3 |
| Pallet capacity | `6 rows; 60 max units; 160.00 cm; 900.00 Kg` | mixed | Palletization constraints | CONFIRMED_FROM_PDF | 3 |

## Potential ERP Gaps

These are documentation findings only. They do not prescribe implementation.

| PDF evidence | Possible ERP concept | Current representation, if any | Apparent gap | Confidence | Business decision required? |
|---|---|---|---|---|---|
| Seven named/color-coded print slots, including Pantone `266 C`, `honeys gold`, a blank Pantone slot, and Internal coding | Versioned color/ink recipe with per-slot reference codes | Engineering `SpecColor` supports colors linked to ink materials, coverage, and ΔE tolerance; documented field set does not clearly include all code families/names | Pantone/reference-code and source-coding details are not clearly first-class in the implemented scope | CONFIRMED_FROM_PDF | YES |
| Coded title features for handle, gusset, perforation/tear, vent, liner, and other construction attributes | Typed product specification parameters | `SpecParameter` is the current extensibility mechanism | The PDF demonstrates a dense coded attribute vocabulary; no canonical parameter dictionary or unit/semantic mapping is established | CONFIRMED_FROM_PDF | YES |
| Converting matrix with 26 coded dimensions and individual tolerances | Converting operation geometry/parameter set | Free-form spec parameters can hold values, while routing operations hold operation headers | No confirmed domain dictionary or dedicated converting geometry model | CONFIRMED_FROM_PDF | YES |
| Corona values `C1`, `CL`, `CR` with tolerances | Surface-treatment quality/specification parameters | Free-form spec parameters and quality-plan limits exist; execution is gated | No clearly dedicated field semantics for corona zones/measurements | CONFIRMED_FROM_PDF | YES |
| Bundle `80pcs`, carton `11 BNDLS`, pallet rows/units/height/weight | Multi-level packaging and delivery specification | Catalog has packaging material subtype; sales/fulfilment packaging is explicitly deferred/gated | No clearly represented bundle/carton/pallet hierarchy tied to the product specification | CONFIRMED_FROM_PDF | YES |
| Handle `Yes` and slit-related `17` | Converting feature and operation parameters | No explicit execution feature model; routing operations are generic | Feature-specific converting requirements require a semantic decision and representation | CONFIRMED_FROM_PDF | YES |
| Product sheet has no QC results or inspection method despite many tolerances | Product-specific quality plan/check execution | Quality plan definition supports limits and sampling; execution is gated by Q-046 and related decisions | No evidence of how this sheet's tolerances map to named quality characteristics or sampling | CONFIRMED_FROM_PDF / NOT_PROVIDED | YES |
| Printed timestamp and no revision/status | Controlled source document/version linkage | Engineering revisions and generic attachments exist | No explicit mapping from source PDF issue timestamp to spec revision or document-control status | CONFIRMED_FROM_PDF | YES |

## Questions Raised By This Product

- Is `38-3` the customer product code, a size/count identifier, or both?
- Is the Persian filename's Honey's/diaper/size information authoritative when `Customer Name` is blank in the PDF?
- What is the exact rendered micron symbol in `TK:60�m` and the layer table, and should it be stored as `µm` or as the source glyph?
- What do `SL:SD`, `HNDL:LNR`, `GS:BTN`, `SPRFRTN`, `RLZC`, `VNT:STR`, `IHL`, `WKT`, `WKTHL`, and `GRD:LD` mean in the NSYS product-title dictionary?
- Are `WD:70mm`, `GS:BTN:54mm`, and `WKT:42mm` independent dimensions or parts of coded construction features?
- Is `BNDL:80pcs` the number of bags per bundle, and does `CARTON:11 BNDLS` mean eleven bundles per carton?
- Does `Slit` with adjacent value `17` mean seventeen slits, a slit width, or another converting parameter?
- What do the page-2 block codes and page-3 converting codes mean, and what units apply to each value?
- Are the `326 C` and `317 C` values Pantone/reference codes for Magenta and Yellow, or are they positioned in another field by the source system?
- What Pantone/reference code or name is intended for action 6, where the spot-code cell is blank?
- What does `FG UPS: 1` mean operationally?
- Is `Plastic` a pallet upper guard, stretch wrapping, divider, or another pallet component?
- Does the product use lamination, or is the single PE web the complete substrate/process definition?
- Is the product title's packaging information a specification target or an actual packing instruction?

## 17. Source-of-Truth Conflicts

No direct contradiction was established from the inspected evidence. The following items require review rather than resolution:

- `CONFLICT_REQUIRES_REVIEW`: The sheet contains a rich converting/packaging definition, while the ERP source of truth treats product specification, BOM/routing, and execution packaging as related but separate concepts and leaves packaging/delivery details and execution gated. The PDF does not establish which fields are engineering specification versus BOM/route execution data.
- `CONFLICT_REQUIRES_REVIEW`: The sheet contains `SKU Code: 12975.3278.1`, while the current ERP documentation says the SKU/product-coding derivation scheme is open and the implemented customer-product code is manual. The code is evidence, not a confirmed derivation rule.

