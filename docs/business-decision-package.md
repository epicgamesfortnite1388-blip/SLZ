# SLZ ERP — Business Decision Package

**Purpose:** let a single SLZ workshop close every gate that blocks remaining
engineering. Each section states the exact question, why the system needs the
answer, what is affected, the plausible options with their consequences, the
analyst recommendation **already on record** (never treated as confirmed), and
the engineering work unlocked once answered.

**How to read recommendations:** items marked *Analyst recommendation on
record* come from `docs/business-analysis/*`. They are proposals only — every
gate stays OPEN until SLZ confirms. Nothing in this package pre-implements any
option.

---

## 1. Q-046 — Roll serialization vs. lot + count  *(highest leverage)*

**Exact question (FR-051).** Rolls are physical objects with weight / length /
width / core. Is each roll a uniquely **serialized** tracked entity, or are
rolls tracked only as **lot + count**?

**Why needed.** Packaging inventory is not quantity-on-hand; it is lot- and
roll-tracked with genealogy (`inventory-model.md`). Every execution-layer table
keys off this choice: stock ledger granularity, GRN lines, material issue,
production output, QC results, allocation, shipment, recall queries.

**Affected surfaces.**
- DB: inventory movement/ledger schema, lot/roll tables, genealogy links.
- API: inventory + production + quality execution endpoints.
- UI: warehouse screens, production confirmation, shipment screens.

**Options & consequences.**

| Option | Consequences |
|---|---|
| **Serialize rolls** | Unique ID per roll with weight/length/width/core → exact genealogy, per-roll costing, precise recall scope; heavier data entry (mitigated by label scanning later, DR-006). |
| **Lot + count** | Lighter capture; genealogy and costing degrade to averages; recall scope widens to whole lots; weight variance invisible. |

*Analyst recommendation on record:* **serialize rolls** — weights/lengths differ
per roll and drive genealogy & costing.

**Unlocked after answer.** Stock movements & kardex, GRN, material issue,
production confirmations & output, genealogy links, QC result attachment,
allocation & shipment, recall trace queries.

---

## 2. Q-048 — Material issue method

**Exact question (FR-058).** Material issue via explicit lot/roll selection
and/or backflush — which method(s)?

**Why needed.** Determines how consumption is recorded against work orders and
which UX the shop floor needs.

**Options & consequences.**

| Option | Consequences |
|---|---|
| Explicit issue | Operator selects lot/roll per line: exact traceability, more floor effort. |
| Backflush | Auto-consume per BOM on output confirmation: fast, but traceability/costing rely on standard assumptions; waste visible only in aggregate. |
| Mixed | Analyst suggestion: explicit for traceable materials, backflush for bulk consumables — needs a rule for which materials qualify (may interact with Q-051). |

*Analyst recommendation on record:* mixed as above (**confirm**).

**Unlocked after answer.** Consumption posting engine, shop-floor issue UI,
WIP material variance views.

---

## 3. Q-049 — Traceability granularity

**Exact question (FR-060).** Required traceability granularity across labeling
and recall: roll / pallet / carton?

**Why needed.** Defines the labeling scheme, packaging-handling entities, and
how far recall walks must descend.

**Options & consequences.** Food-contact flexible packaging usually demands at
least lot-level, often roll-level. Pallet/carton layers add handling units on
top of the chosen roll/lot model rather than replacing it.

**Unlocked after answer.** Labeling/print-data design, packing/shipment units,
recall query depth.

---

## 4. Q-026 — Inventoried intermediates / real BOM levels

**Exact question (FR-030).** Multi-level BOMs mirror the production stages
(resin → base film → printed → laminate → slit → finished) — **which levels are
real inventoried intermediates** vs. flow-through?

**Why needed.** Decides whether BOMs are multi-level trees or flat one-level
recipes, which intermediates get warehouses/lots, and how WIP is represented.

**Options & consequences.**

| Option | Consequences |
|---|---|
| Flow-through stages | Single-level BOM per finished product; stages remain routing steps only; simplest planning. |
| Stocked intermediates | Multi-level BOM + intermediate warehouses/lots; enables stocking printed film for later conversion; more transactions and valuation points (interacts with Q-034). |

**Unlocked after answer.** Final BOM structure, routing-to-BOM linkage,
intermediate storage design, WIP accounting seams.

---

## 5. Q-055 / Q-053 — Data scoping & role catalogue  *(security-critical)*

**Exact questions.** Q-053: validate the proposed role list against the real
organization. Q-055: what **data-scoping** does each role need (who may see /
act on which company's / site's records)?

**Why needed.** There is currently **no user↔company binding**: any
authenticated user holding a module permission can access any company's records
of that module by ID. Full inventory of affected models/viewsets/frontend
surfaces: see `docs/architecture/multi-tenancy-preparation.md`.

**Decision inputs required from SLZ.**
1. Can one user belong to multiple companies/sites? Which relation is master?
2. Is visibility company-granular only, or site-granular for floor roles?
3. Who administers memberships (ties into Q-054 maker/checker)?
4. Confirm the final role catalogue (16-role proposal on record).

**Prepared engineering (no behavior implemented).** Read choke point exists on
the shared base viewset; write-path precedent exists (DR-040 serializer
invariants); generic-reference surfaces (attachments/workflow instances/audit
viewer) identified as the hard cases; cross-company regression-test strategy
drafted. Implementation becomes a systematic sweep once policy lands.

**Consequence of deferral:** the deployment must remain single-company until
this closes — this is the only gate that blocks safe production use of
otherwise-finished features.

---

## 6. Costing cluster — Q-034 / Q-031 / Q-033 (summary)

Material valuation method (FIFO/WA/lot-actual), cost rates & formulas, scrap
absorption/regrind value. The system keeps formulas configurable; nothing is
hard-coded. Needed before costing go-live; does not block definition-layer
work. Analyst risk note R-4: costing without validated rates misleads margins.

## 7. Q-038 — KPI definitions (summary)

Which profitability/KPI dimensions are actually managed. Dashboards ship only
with confirmed-data counts today; KPI views wait here.

## 8. DR-000 / NQ-001 — Build-vs-buy reaffirmation (summary)

An official feasibility study recommends buying Dynamics 365 F&O. The custom
build should be explicitly reaffirmed by SLZ before investing further —
program-level decision above all gates in this document.

## 9. Secondary questions worth batching into the same workshop

Q-019 product coding scheme · Q-024 spec-revision trigger/approver · Q-027
consumption bases/waste · Q-029 routing templates/stage skips · Q-039/Q-040
sampling methods · Q-043 rework-vs-scrap rules · Q-047 bin tracking · Q-051
shelf-life FEFO · Q-052 UoM set · Q-054 approval thresholds matrix · Q-060
hosting/data residency · Q-062 shop-floor capture.

---

*Prepared autonomously from repository evidence; no option has been selected
on SLZ's behalf.*
