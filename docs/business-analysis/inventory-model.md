# Inventory & Traceability Model

> Tags: **[CONFIRMED]** · **[ASSUMPTION]** · **[OPEN]** · **[PROPOSAL]**.
> Central requirement (brief): **full forward + reverse traceability** and **transactional** stock movements. Inventory here spans raw materials, WIP rolls/reels, semi-finished, and finished goods.

---

## 1. Inventory object hierarchy [PROPOSAL]

Packaging inventory is **not** simple quantity-on-hand; it is **lot- and roll-tracked** with genealogy.

| Object | Description | Tracking level |
|--------|-------------|----------------|
| **Raw Material** | Item master: resin grade, film, ink, adhesive, solvent, core, carton, label. | item |
| **Raw Material Lot** | A received supplier lot (supplier batch #, GRN, COA). | lot |
| **Roll / Reel** | A physical wound roll — base film, printed, laminate, slit. Unique ID, weight, length, width, core. | serialized (each roll unique) |
| **Semi-finished product** | An inventoried intermediate (usually as rolls). | lot + roll |
| **Finished product** | Bags/pouches/roll-stock ready to ship, grouped in a **production batch/lot**. | lot (+ pack units) |
| **Packaging materials** | Cartons, cores, pallets, labels. | item / lot |

**[OPEN Q-046]** Are rolls individually serialized (each roll a unique tracked entity) or tracked only by lot+count? Recommendation: **serialize rolls** (weights/lengths differ per roll and drive genealogy & costing).

---

## 2. Warehouse & location model [CONFIRMED concepts]

```
Warehouse (physical/logical site)
 └─ Zone (optional)
     └─ Location (rack/bay/floor spot / staging / QC-hold / scrap)
```
- Location **types**: RM store, WIP/floor, FG store, QC-hold, quarantine, scrap, shipping-staging, returns.
- **[OPEN Q-047]** How many warehouses/sites? Is location-level (bin) tracking needed, or warehouse-level sufficient initially?

---

## 3. Stock movement model [CONFIRMED "stock movement"]

Every inventory change is an **immutable, append-only stock movement** (double-entry style: from-location → to-location, or in/out of a virtual location).

| Movement type | Trigger |
|---------------|---------|
| Receipt (GRN) | PO receipt of RM |
| Issue to production | Material consumed by work order (records lot/roll) |
| Production receipt | Batch/roll output posted from a work order |
| Transfer | Between locations/warehouses |
| Reservation / allocation | Soft-lock stock for an order (not a physical move) |
| Scrap issue | Scrap posting |
| Adjustment | Stock count correction (reason-coded) |
| Shipment issue | Delivery to customer |
| Return receipt | RMA back into stock/quarantine |

**Transactional guarantee (constraint #8):** consumption + output + genealogy links + cost capture for a work-order confirmation are committed as **one atomic transaction**; partial posting is not allowed.

**[OPEN Q-048]** Backflush (auto-consume per BOM on output) vs. explicit issue (operator scans each lot)? Recommendation: explicit lot/roll issue for traceable materials; backflush for bulk consumables — confirm.

---

## 4. Traceability model [CONFIRMED core principle]

### 4.1 Forward traceability
```
Supplier → RM Lot → (issued to) → Production Batch → Semi-finished (roll) →
→ (consumed by) → next Batch → … → Finished Batch → Delivery → Customer
```

### 4.2 Reverse traceability
Given a finished lot / delivery, walk **child→parent** links to reach every RM lot, machine, operator, shift, and QC result that contributed.

### 4.3 Genealogy mechanism [PROPOSAL]
- A **batch/roll genealogy** table records `parent_object → child_object` for every transformation (1:N split at slitting, N:1 merge at lamination, etc.).
- Every production batch stores: input lots/rolls consumed, machine, operator, shift, routing/BOM revision, spec revision, QC results, timestamps.
- Enables **recall / mock-recall**: "which deliveries contain RM lot X?" and "what made delivery Y?"

**[OPEN Q-049]** Required traceability granularity: per roll? per pallet? per carton? (Food-contact usually demands at least lot-level, often roll-level.)

---

## 5. Reservations & material availability [ASSUMPTION A-004/A-019]
- MRP computes requirements per production order; system **reserves** available stock and raises **purchase requests** for shortfalls.
- Reservation is a soft allocation visible in availability calculations (available = on-hand − reserved).
- **[OPEN Q-005/050]** Allocation policy: FIFO by lot? Nearest-expiry first? Reserve at order confirmation or at planning?

---

## 6. Lot attributes & expiry [ASSUMPTION A-020]
- RM lots: supplier, supplier lot #, GRN, received qty, COA, **expiry/shelf-life** (inks/adhesives age), storage conditions.
- FG lots: production date, spec rev, batch, best-before if applicable.
- **[OPEN Q-051]** Do materials/products have shelf-life/expiry that the system must enforce (FEFO)?

---

## 7. Units of measure [ASSUMPTION A-021]
- Multiple UoMs coexist: kg, m, m², µm, pieces, rolls, cartons, pallets. The model needs **UoM conversions** (e.g. kg ↔ m via grammage & width) per item.
- **[OPEN Q-052]** Confirm required UoMs and standard conversions (density/grammage per material).

---

## 8. Stock valuation
- Valuation method feeds costing; see `costing-model.md` §3. **[OPEN Q-034]** FIFO / weighted-average / lot-actual.

---

## 9. Assumptions & questions
A-019 reservations · A-020 lot/expiry · A-021 UoM. Questions Q-046…Q-052 (+Q-005/034). Consolidated in [`open-questions.md`](./open-questions.md).
