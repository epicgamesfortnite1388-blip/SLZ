# Roles, Permissions & Auditability

> Tags: **[CONFIRMED]** · **[ASSUMPTION]** · **[OPEN]** · **[PROPOSAL]**.
> Constraints #4 (preserve history) and #5 (auditability) apply system-wide. Roles below are **proposals** derived from the process actors in `business-processes.md` §4 and **must be validated** against SLZ's real org.

---

## 1. Proposed roles [ASSUMPTION A-022]

| Role | Primary responsibilities | Key permissions |
|------|--------------------------|-----------------|
| **Sales / Account manager** | Inquiries, quotations, orders, customer comms | Create/edit inquiry, quotation, sales order; view customer products; cannot alter specs/BOM. |
| **Sales engineer / Technical** | Requirements, product specification | Author/revise product spec; request costing. |
| **Prepress / Design** | Artwork, prepress, color, tooling | Author/revise artwork; manage tooling & color recipes. |
| **Industrial engineer** | BOM, routing | Author/approve BOM & routing revisions. |
| **Production planner (PPC)** | Scheduling, MRP, production orders | Create/release production orders; assign machines; run MRP. |
| **Procurement / Purchasing** | Purchase requests, POs, suppliers | Create PR/PO; approve within limits; manage suppliers. |
| **Warehouse / Store keeper** | Receipts, issues, transfers, picking | Post stock movements; manage locations. |
| **Machine operator** | Execute work orders | Confirm work orders, post output/scrap/downtime; **cannot** edit specs/BOM. |
| **Production supervisor** | Shop-floor oversight | Release/hold work orders; approve rework; reassign. |
| **Quality inspector** | Inline & final QC | Record checks, raise alerts; put on QC-hold. |
| **Quality manager** | Disposition, CAPA, COA | Disposition NCRs, approve rework/concession, release holds, sign COA. |
| **Costing / Finance analyst** | Rates, cost settlement, margin | Maintain rates; view/settle costs; profitability reports. |
| **Maintenance technician / manager** | Maintenance orders | Create/close maintenance orders; log machine downtime. |
| **Logistics / Shipping** | Deliveries, shipments | Create delivery notes; confirm dispatch. |
| **Plant / Operations manager** | Oversight & approvals | Cross-module approvals, dashboards. |
| **System administrator** | Users, roles, master data | Manage RBAC, config; restricted from transactional edits by policy. |

**[OPEN Q-053]** Validate role list against SLZ's actual departments and job titles; several roles may merge in a smaller org, or one person may hold several.

---

## 2. Access-control model [PROPOSAL]

- **RBAC** (role-based) as the baseline: permissions grouped into roles; users hold one or more roles.
- Permissions expressed as **(action, resource)** pairs (e.g. `approve:quotation`, `release:production_order`, `post:stock_movement`).
- **Approval authorities** modeled as data (e.g. PO approval limits by amount, spec approval by role) — **not hard-coded** (consistent with constraint #9 philosophy).
- Consider **ABAC-lite** later (attribute conditions: warehouse scope, product-group scope) if SLZ needs data-scoped access. Recommend **not** in first build unless required.

**[OPEN Q-054]** Are there approval **thresholds** (e.g. PO value tiers, discount limits on quotations) and multi-step approvals? Provide the matrix.

**[OPEN Q-055]** Data-scoping needed (e.g. a planner sees only certain lines/warehouses)? Or is access plant-wide by role?

---

## 3. Segregation of duties [PROPOSAL]
Enforce that the same user cannot both (a) create and (b) approve the same critical document (PO, spec, BOM release) where SLZ policy requires it.
**[OPEN Q-056]** Which documents require maker≠checker enforcement?

---

## 4. Auditability [CONFIRMED constraint #5]

- **Immutable audit log** for every create/update/state-transition: who, what, before→after, timestamp (**UTC stored; rendered Jalali + Gregorian**), reason where applicable, source (UI/API/job).
- **Versioned entities** (spec, artwork, BOM, routing, quotation, price) keep full history; supersede never deletes.
- **Append-only** transactional records (stock movements, QC results, cost captures, confirmations) — corrections via reversing/adjusting entries, never destructive edits.
- Audit log is **read-only** to all roles except export; not editable even by admin.

**[OPEN Q-057]** Retention period and any regulatory audit requirements (tax authority, food-safety, ISO 9001 records)?

---

## 5. Authentication & identity [PROPOSAL]
- Username/password with strong policy initially; **[OPEN Q-058]** SSO/Active Directory integration required? Shop-floor operators may need **shared kiosk + PIN/badge** login — confirm.
- Bilingual UI per user preference (fa/en); date display per user (Jalali/Gregorian).

---

## 6. Assumptions & questions
A-022 role catalogue. Questions Q-053…Q-058. Consolidated in [`open-questions.md`](./open-questions.md).
