# Business Processes — Order-to-Cash & Manufacturing Lifecycle

> Tags: **[CONFIRMED]** given by brief · **[ASSUMPTION]** industry default, validate · **[OPEN]** needs SLZ answer · **[PROPOSAL]** design recommendation.

This document validates the proposed business flow, decomposes it into sub-processes, identifies actors and hand-offs, and defines the state machines that govern the key business documents.

---

## 1. The proposed lifecycle (as given) [CONFIRMED as *proposed*, not as *correct*]

```
Customer inquiry → Technical requirements → Product specification → Quotation
→ Customer approval → Sales order → Artwork/engineering approval → BOM
→ Routing → Material requirements → Production planning
→ Purchasing/material reservation → Production → Quality control
→ Finished goods → Warehouse → Delivery → Actual costing → Profitability
```

The task explicitly says **do not assume this flow is correct**. Below is a critical review.

---

## 2. Critical review of the proposed flow

The linear sequence is a good first approximation but real MTO packaging plants deviate in several important ways. Each deviation is flagged for validation.

### 2.1 New product vs. repeat order are different paths [ASSUMPTION A-001]
- A **first-time product** (Engineer-To-Order) traverses the *full* chain: requirements → spec → artwork → tooling (plate/cylinder) → sampling/approval → first production.
- A **repeat order** (Make-To-Order) of an already-approved product should **skip** spec creation, artwork, tooling, BOM and routing authoring, jumping from sales order → production planning against the *existing approved revision*.
- **Implication:** the system needs a "product already exists / new revision / brand new" branch at order entry.
- **[OPEN Q-002]** What share of orders are repeats vs. new? This drives how much automation to invest in each path.

### 2.2 Sampling / pre-production approval loop is missing [ASSUMPTION A-002]
Flexible packaging almost always includes a **sample / proof / first-article approval** before bulk production:
- Color proof / draw-down approval (color matching).
- Printed sample or "roll sample" sign-off by the customer.
- **Implication:** insert **Sampling & First-Article Approval** between artwork approval and bulk production, possibly requiring its own short production run.
- **[OPEN Q-003]** Does SLZ require customer sign-off on a physical printed sample before every new job? For repeats?

### 2.3 Tooling (printing plates/cylinders) procurement is a distinct sub-flow [ASSUMPTION A-003]
Flexo printing needs **photopolymer plates / sleeves / mounting**, often produced externally from approved prepress files. This is a lead-time-critical, cost-bearing step that the linear flow hides inside "artwork approval."
- **Implication:** model **Printing Tooling** as its own object with its own procurement/creation and approval lifecycle, linked to an artwork revision.
- **[OPEN Q-004]** Are plates made in-house or outsourced? Who owns the tooling cost — SLZ or the customer?

### 2.4 Purchasing may precede the order (stock resins) [ASSUMPTION A-004]
Commodity resins (PE, PP, etc.) are often **stocked** and replenished on min/max, not purchased per order; only specialty inks/films/adhesives are bought to order.
- **Implication:** material requirements split into **allocate-from-stock** vs. **purchase-to-order**.
- **[OPEN Q-005]** Which materials are stocked vs. bought per job?

### 2.5 Production is multi-stage, not a single step [CONFIRMED by capability list]
"Production" is really a **chain of stage-level orders** (extrusion → printing → lamination → slitting → bag-making/converting), each producing an intermediate **roll/reel** that is inventoried, QC'd, and consumed downstream. See `manufacturing-processes.md`.

### 2.6 QC is *inline at every stage*, not only at the end [ASSUMPTION A-005]
Quality control occurs after extrusion (thickness/width), after printing (color/registration), after lamination (bond strength), and at final (dimensions/seal). A single terminal "Quality control" node understates this.

### 2.7 Costing & profitability are continuous, not a final step [PROPOSAL]
Actual costs accrue *as production happens* (material issues, machine hours, scrap). "Actual costing" at the end is the *closing/settlement*, but cost capture is continuous. Model both: **cost capture (continuous)** + **order cost settlement (on completion)**.

### 2.8 Reverse flows are absent [ASSUMPTION A-006]
The proposed flow omits: order changes/cancellations, customer returns/complaints (RMA), rework loops, over/under-production handling (packaging commonly ships ±% of ordered quantity), and credit/hold.
- **[OPEN Q-006]** Does SLZ ship with an agreed over/under-delivery tolerance (e.g. ±10%)? This is standard in the industry and materially affects order fulfilment and invoicing.

---

## 3. Revised end-to-end process (proposed) [PROPOSAL]

```
                         ┌─────────────────────────── repeat order (approved revision exists) ──────────────────────────┐
                         │                                                                                              ▼
Inquiry ─► Technical requirements ─► Product specification (v) ─► Quotation ─► Customer approval ─► Sales Order
   │                                        │                                                          │
   │ (new product path)                     ▼                                                          ▼
   │                              Artwork (v) + Prepress ─► Printing tooling (plate/cylinder)     Production planning (MPS/scheduling)
   │                                        │                                                          │
   │                                        ▼                                                          ▼
   │                              First-article / sample approval ◄──────────────────┐         Material requirements (MRP)
   │                                        │                                         │                │
   └────────────────────────────────────────                                         │       ┌────────┴─────────┐
                                            ▼                                         │       ▼                  ▼
                                     BOM (v) + Routing (v) ──────────────────────────┘  Allocate stock     Purchase (PR ► PO ► receipt ► QC in)
                                            │                                                   └────────┬─────────┘
                                            ▼                                                            ▼
                              Production Orders per stage:  Extrusion ─► Printing ─► Lamination ─► Slitting ─► Converting/Bag-making
                                            │  (each: work orders, inline QC, scrap, rework, batch output as rolls)
                                            ▼
                              Final QC ─► Finished goods ─► Warehouse (FG) ─► Pick/Pack ─► Delivery/Shipment
                                            │                                                            │
                                            ▼                                                            ▼
                              Continuous cost capture ───────────────────────► Order cost settlement ─► Profitability
                                                                                                         ▲
                                                              Returns / complaints (RMA) ────────────────┘
```

**[OPEN Q-007]** Validate this revised map with production planning and sales. Especially the branch points and the sampling loop.

---

## 4. Sub-processes, actors & hand-offs

| # | Sub-process | Primary actor(s) | Key output document | Hand-off to |
|---|-------------|------------------|---------------------|-------------|
| 1 | Inquiry capture | Sales | Inquiry record | Technical / Sales eng. |
| 2 | Technical requirements | Sales engineering / R&D | Requirements sheet | Product spec |
| 3 | Product specification (versioned) | Technical / R&D | Product Spec revision | Costing / Quotation |
| 4 | Quotation | Sales + Costing | Quotation (versioned, priced) | Customer |
| 5 | Customer approval | Sales | Approved quotation | Order entry |
| 6 | Sales order | Sales / Order mgmt | Sales Order | Planning + Artwork |
| 7 | Artwork & prepress | Prepress / Design | Artwork revision + prepress files | Tooling |
| 8 | Printing tooling | Prepress / Purchasing | Plate/cylinder set | Production |
| 9 | Sample / first-article | Production + QC + Customer | Approved sample | BOM/Routing release |
| 10 | BOM authoring | Technical / Industrial eng. | BOM revision | Routing / MRP |
| 11 | Routing authoring | Industrial engineering | Routing revision | Planning |
| 12 | Production planning / scheduling | PPC (planning) | Production plan / schedule | Shop floor |
| 13 | MRP / material requirements | Planning | Requirement list | Purchasing / warehouse |
| 14 | Purchasing | Procurement | PR → PO → GRN | Warehouse (RM) |
| 15 | Production execution | Machine operators / supervisors | Work order confirmations, batches | QC / next stage |
| 16 | Quality control (inline + final) | QC | Quality checks, alerts, COA | Warehouse / rework |
| 17 | Finished goods & warehousing | Warehouse | Stock receipts, locations | Shipping |
| 18 | Delivery | Logistics / shipping | Delivery note / shipment | Customer / invoicing |
| 19 | Costing & profitability | Costing / finance | Cost settlement, margin report | Management |
| 20 | Returns / complaints | QC + Sales | RMA / CAPA | Rework / credit |

**[OPEN Q-008]** Confirm the real org units and who *approves* each hand-off (see `roles-and-permissions.md`).

---

## 5. Key state machines [PROPOSAL — validate transitions & authorities]

### 5.1 Quotation
```
DRAFT ─► UNDER_REVIEW ─► SENT ─► (ACCEPTED | REJECTED | EXPIRED)
  ▲                         │
  └──────── REVISED ◄────────┘   (new version; old version retained, immutable)
```
- ACCEPTED → triggers Sales Order creation. Superseded versions are preserved (history).

### 5.2 Sales Order
```
DRAFT ─► CONFIRMED ─► IN_PLANNING ─► IN_PRODUCTION ─► (PARTIALLY_)FULFILLED ─► CLOSED
   │           │            │              │
   └─ CANCELLED┘            └── ON_HOLD ◄───┘   (credit / material / customer hold)
```
- **[OPEN Q-009]** What conditions put an order ON_HOLD (credit limit? material shortage?) and who can release it?

### 5.3 Product Specification revision
```
DRAFT ─► IN_REVIEW ─► APPROVED ─► ACTIVE ─► SUPERSEDED
                          │                     ▲
                          └──── OBSOLETE         └─ (new revision approved)
```
- Only **ACTIVE** revisions can be ordered against. SUPERSEDED/OBSOLETE retained for traceability.

### 5.4 Artwork revision
```
DRAFT ─► INTERNAL_REVIEW ─► CUSTOMER_REVIEW ─► APPROVED ─► ACTIVE ─► SUPERSEDED
                                   │
                                   └─► CHANGES_REQUESTED ─► (new revision)
```

### 5.5 Production Order (per stage) — see manufacturing-processes.md for detail
```
PLANNED ─► RELEASED ─► IN_PROGRESS ─► (PAUSED) ─► COMPLETED ─► CLOSED
   │            │                                     │
   └─ CANCELLED ┘                                     └─► QC_HOLD ─► (PASS→next | FAIL→rework/scrap)
```

### 5.6 Purchase Order
```
DRAFT ─► APPROVED ─► SENT ─► PARTIALLY_RECEIVED ─► RECEIVED ─► (QC) ─► CLOSED
   └─ CANCELLED
```

### 5.7 Delivery / Shipment
```
PLANNED ─► PICKED ─► PACKED ─► DISPATCHED ─► DELIVERED ─► (CONFIRMED)
                                    └─► RETURNED (RMA)
```

> All state machines above are **[PROPOSAL]**. Transition *guards* (who may act, what preconditions) require SLZ validation and are listed in `open-questions.md`.

---

## 6. Cross-cutting requirements applied to processes

- **Versioning/history:** Quotation, Spec, Artwork, BOM, Routing, Price are all versioned; superseding never deletes.
- **Audit:** every transition records actor, timestamp (UTC + Jalali/Gregorian), reason where relevant.
- **Bilingual documents:** quotations, delivery notes, COAs must render in fa/en.
- **Transactional:** order confirmation, stock reservation, batch posting, and cost capture are atomic units of work.

---

## 7. Assumptions raised in this document

A-001 new vs repeat path · A-002 sampling loop · A-003 tooling sub-flow · A-004 stock vs buy-to-order · A-005 inline QC · A-006 reverse flows · plus open questions Q-002…Q-009. All consolidated in [`open-questions.md`](./open-questions.md).
