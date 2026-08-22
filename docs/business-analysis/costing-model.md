# Costing Model (Actual Cost)

> Tags: **[CONFIRMED]** · **[ASSUMPTION]** · **[OPEN]** · **[PROPOSAL]**.
> **All formulas below are PROPOSALS. Do not finalize without SLZ business validation** (brief requirement). Constraint #10: model manufacturing costing *before* building financial accounting.

---

## 1. Costing philosophy [PROPOSAL]

- **Actual costing** driven by real consumption captured on the shop floor, **not** standard costing alone.
- **Recommendation:** capture **standard/estimated cost** at quotation time *and* **actual cost** during/after production, then report **variance** (estimate vs actual) per order. This gives quoting discipline and post-mortem margin analysis.
- Costs accrue **continuously** during production (cost capture) and are **settled** when the production/sales order closes (see `business-processes.md` §2.7).
- Cost is captured **per production batch / work order / stage**, then rolled up to the **sales order line** and **customer product**.

**[OPEN Q-031]** Does SLZ currently use standard costing, actual costing, or neither? What is the current costing method and currency (IRR/Toman)? Inflation handling for material prices?

---

## 2. Cost element taxonomy [CONFIRMED list from brief]

| # | Element | Nature | Proposed capture point | Basis |
|---|---------|--------|------------------------|-------|
| 1 | **Material** (resin, film, substrate) | Direct | Material issue to work order (with lot & actual price) | kg / m² consumed |
| 2 | **Ink** | Direct | Ink issue at printing | kg/g per color × coverage |
| 3 | **Adhesive** | Direct | Issue at lamination | g/m² × area |
| 4 | **Labor** | Direct/semi | Work-order time confirmations × labor rate | operator-hours |
| 5 | **Machine time** | Direct | Runtime confirmations × machine hourly rate | machine-hours |
| 6 | **Setup** | Direct | Setup time × (labor+machine) rate; often fixed per run | setup-hours / per run |
| 7 | **Energy** | Direct/allocated | Machine-hours × energy rate, or metered | kWh or machine-hour proxy |
| 8 | **Maintenance allocation** | Allocated | Maintenance cost pool ÷ machine-hours | allocation rate |
| 9 | **Packaging** | Direct | Cartons/cores/labels/pallets issued | per unit |
| 10 | **Scrap** | Loss/adjustment | Scrapped material + processing lost to scrap point | qty × accumulated cost |
| 11 | **Overhead** | Allocated | Overhead pool ÷ driver (machine-hr / labor-hr / value) | allocation rate |

**[OPEN Q-032]** Confirm this taxonomy is complete. Missing candidates: **tooling/plate amortization**, **freight/delivery**, **QC/lab cost**, **financing cost**, **customs/import duty** on materials, **waste disposal**. Should any be separate elements?

---

## 3. Proposed cost build-up (illustrative, UNVALIDATED) [PROPOSAL]

```
Direct material cost      = Σ (material issued_qty × actual_unit_cost)      [FIFO/weighted-avg by lot]
Direct ink cost           = Σ (ink_qty × ink_unit_cost)
Direct adhesive cost      = Σ (adhesive_qty × unit_cost)
Direct labor cost         = Σ (operator_hours × labor_rate_by_skill)
Machine cost              = Σ (machine_hours × machine_hourly_rate)
Setup cost                = Σ (setup_hours × (labor_rate + machine_rate))   [or fixed per run]
Energy cost               = Σ (machine_hours × energy_rate)   OR metered kWh × tariff
Maintenance allocation    = machine_hours × maintenance_alloc_rate
Packaging cost            = Σ (packaging_item_qty × unit_cost)
Scrap cost                = Σ (scrapped_input_value + processing_value_up_to_scrap_point) − scrap_recovery_value
Overhead                  = overhead_driver_qty × overhead_rate
------------------------------------------------------------------------------------------
Order actual cost         = sum of the above across all stages/work orders
Unit cost                 = Order actual cost ÷ good_units_delivered
```

> **[OPEN Q-033]** Rates (labor by skill, machine hourly, energy, maintenance, overhead) and their **allocation drivers** must all be supplied/validated by SLZ finance. **[OPEN Q-034]** Costing valuation method for materials: FIFO, weighted average, or lot-specific actual?

---

## 4. Scrap & yield cost treatment [ASSUMPTION A-015]
- Scrap carries the **accumulated cost up to the stage where it was scrapped** (film scrapped after printing costs more than film scrapped after extrusion).
- Recoverable scrap (regrind/resale) offsets cost at a **recovery value**.
- **[OPEN Q-035]** Does SLZ regrind/reuse or sell scrap? At what value? Is scrap cost absorbed into good units or reported separately?

## 5. Tooling amortization [ASSUMPTION A-016]
- Printing plates/cylinders are durable; cost is either **charged to the customer** (one-off) or **amortized** over expected runs.
- **[OPEN Q-004/036]** Customer-paid tooling vs amortized? If amortized, over what volume/time?

## 6. Over/under-production & costing [ASSUMPTION A-017]
- If SLZ ships ±% of ordered quantity, actual cost spreads over actual good units; invoicing may be on delivered qty.
- **[OPEN Q-006/037]** Confirm commercial rule.

---

## 7. Cost capture points map [PROPOSAL]

| Event | Cost captured |
|-------|---------------|
| Material issue to work order | material/ink/adhesive/packaging (actual lot price) |
| Work-order time confirmation | labor + machine + setup + energy + maintenance alloc |
| Scrap posting | scrap cost + reason |
| Downtime posting | (optional) idle cost / OEE loss |
| Production order close | roll-up, apply overhead, compute WIP→FG value |
| Sales order close | total order cost, unit cost, **margin vs quoted price** |

---

## 8. Profitability [PROPOSAL]
```
Revenue (delivered qty × price)  −  Order actual cost  =  Gross margin
Margin % = Gross margin ÷ Revenue
```
Reportable by: sales order, customer product, customer, product group, machine/work center (contribution). **[OPEN Q-038]** Which profitability dimensions does management want first?

---

## 9. Explicit non-goals for this task [CONFIRMED constraint #10]
- No general ledger, AR/AP, tax, or financial-statement accounting is designed here. Costing is a **manufacturing cost** capability; integration with accounting is a **later** task.

---

## 10. Assumptions & questions
A-015 scrap cost accumulation · A-016 tooling amortization · A-017 over/under production. Questions Q-031…Q-038 (+Q-004/006). Consolidated in [`open-questions.md`](./open-questions.md).
