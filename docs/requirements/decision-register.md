# SLZ ERP — Decision Register / دفتر تصمیم‌ها

Every unresolved architectural or business decision. **Status is never `CONFIRMED` merely because it is the software team's recommendation** — only SLZ sign-off moves a row to `CONFIRMED`.

Status values: `OPEN` (no decision) · `PROPOSED` (software-team recommendation, awaiting SLZ) · `CONFIRMED` (SLZ decided) · `DEFERRED` (intentionally postponed).

## Technical decisions

| ID | Decision | Options | Recommended | Business/Tech Owner | Status | Date |
|----|----------|---------|-------------|---------------------|--------|------|
| DR-001 | Backend technology | Django/Python · NestJS/TypeScript | Django/DRF (record-heavy ERP, mature migrations/audit) — team choice | Software team + Management | PROPOSED | 2026-08-20 |
| DR-002 | Primary database | PostgreSQL · other RDBMS | PostgreSQL (ACID, JSONB, constraints) | Software team | PROPOSED | 2026-08-20 |
| DR-003 | Hosting / deployment model | On-prem · Private cloud · Public cloud | On-prem/self-hosted likely (sanction/connectivity) — needs SLZ | Management + IT | OPEN | 2026-08-20 |
| DR-004 | Authentication | Local accounts · SSO/Active Directory · Kiosk+PIN/badge for floor | Local + AD if available; kiosk/PIN for operators | IT + Management | OPEN | 2026-08-20 |
| DR-005 | File / object storage | MinIO (self-host) · Cloud S3 | MinIO on-prem (self-hostable) | Software team + IT | PROPOSED | 2026-08-20 |
| DR-006 | Barcode / labeling technology | 1D barcode · QR/2D · RFID | QR for rolls/lots (data-rich) — confirm with trace granularity | Warehouse + IT | OPEN | 2026-08-20 |
| DR-007 | Accounting integration | Build later in-ERP · Integrate external accounting · None initially | Defer; define boundary first (manufacturing before accounting) | Finance + Management | OPEN | 2026-08-20 |
| DR-008 | Notification channels | In-app · Email · SMS · WhatsApp | In-app first; others on demand | Management | DEFERRED | 2026-08-20 |
| DR-009 | Background workers | Celery (Django) · BullMQ (Nest) | Follows DR-001 | Software team | PROPOSED | 2026-08-20 |
| DR-010 | Cache / broker | Redis · other | Redis | Software team | PROPOSED | 2026-08-20 |
| DR-011 | Frontend stack | React+TS · other | React + TypeScript (RTL/i18n, Jalali) | Software team | PROPOSED | 2026-08-20 |
| DR-012 | Scheduling engine | Manual/assisted finite-capacity · Automatic APS | Manual/assisted first; APS deferred | Planning + Software team | PROPOSED | 2026-08-20 |
| DR-013 | Machine data capture | Manual entry · PLC/SCADA/OPC-UA integration | Manual first; integrate only if feasible | Production + IT | OPEN | 2026-08-20 |
| DR-014 | Reporting/BI | Postgres views first · dedicated BI tool later | Views first | Software team | PROPOSED | 2026-08-20 |

## Business decisions (high-impact; cross-referenced to open questions)

| ID | Decision | Options | Recommended | Business Owner | Status | Date |
|----|----------|---------|-------------|----------------|--------|------|
| DR-020 | Roll tracking model *(Q-046)* | Serialize each roll · Lot + count | Serialize rolls (weights/lengths differ, drive genealogy) | Production + Warehouse | OPEN | 2026-08-20 |
| DR-021 | Inventoried intermediates / BOM levels *(Q-026)* | Track all stages · Track selected · Flow-through | Track stages that are physically stored/QC'd | Planning + Production | OPEN | 2026-08-20 |
| DR-022 | Traceability granularity *(Q-049)* | Roll · Pallet · Carton | At least lot/roll (food-contact) | Quality + Warehouse | OPEN | 2026-08-20 |
| DR-023 | Product coding scheme *(Q-019)* | Internal code + customer code · Customer code only | Internal code independent of customer | Sales + Engineering | OPEN | 2026-08-20 |
| DR-024 | Spec revision trigger rule *(Q-024)* | Any change = new rev · Threshold-based | Define per attribute class; approver named | Engineering + Management | OPEN | 2026-08-20 |
| DR-025 | BOM consumption basis & waste *(Q-027)* | Per-piece · Per-area/weight/length | Area/weight for film, per-piece for packaging | Engineering | OPEN | 2026-08-20 |
| DR-026 | Material valuation method *(Q-034)* | FIFO · Weighted-average · Lot-actual | Lot-actual for traceable materials — confirm w/ Finance | Finance | OPEN | 2026-08-20 |
| DR-027 | Costing methodology *(Q-031/033)* | Actual only · Standard+actual variance | Standard-at-quote + actual with variance | Finance | OPEN | 2026-08-20 |
| DR-028 | Over/under-delivery tolerance *(Q-006/037)* | Exact qty · ± % tolerance | ± % per industry norm — SLZ to set value | Management + Sales | OPEN | 2026-08-20 |
| DR-029 | Sampling / first-article policy *(Q-003)* | Mandatory new jobs · Mandatory all · Optional | Mandatory for new products | Sales + Quality | OPEN | 2026-08-20 |
| DR-030 | Tooling ownership & cost *(Q-004/036)* | Customer-paid · Amortized · Mixed | Confirm per commercial policy | Prepress + Finance | OPEN | 2026-08-20 |
| DR-031 | Material issue method *(Q-048)* | Explicit lot/roll issue · Backflush · Hybrid | Explicit for traceable, backflush for bulk | Production + Warehouse | OPEN | 2026-08-20 |
| DR-032 | Approval hierarchy & thresholds *(Q-054/056)* | Single-step · Tiered/multi-step | Tiered with maker≠checker on critical docs | Management + Finance | OPEN | 2026-08-20 |
| DR-033 | Role catalogue *(Q-053)* | Proposed 16-role set · SLZ-specific | Validate against real org | Management | OPEN | 2026-08-20 |
| DR-034 | Required KPIs & profitability dimensions *(Q-038)* | TBD | Define with management | Management + Finance | OPEN | 2026-08-20 |
| DR-035 | Recall capability *(Q-044)* | Full recall/mock-recall · Trace-only | Full recall for food-contact | Quality + Management | OPEN | 2026-08-20 |
| DR-036 | Shelf-life/FEFO enforcement *(Q-051)* | Enforce FEFO · Track only · None | Track; enforce for aging inks/adhesives | Warehouse + Quality | OPEN | 2026-08-20 |

*Origin detail for each Q-id: `../business-analysis/open-questions.md`. Requirements affected: `requirements-baseline.md`.*

## Decisions added / changed by Task 004A reconciliation (2026-08-21)

Source of change: `docs/reference/NEPTA_ERP_Feasibility_Study.md` (official SLZ document). Full rationale in `docs/reconciliation/` and `requirements-changelog.md`. Per the rule above, a row is `CONFIRMED` only when the SLZ document establishes it as fact.

| ID | Decision | Options | Recommended | Business Owner | Status | Date |
|----|----------|---------|-------------|----------------|--------|------|
| **DR-000** | **Build vs Buy (CRITICAL)** — custom build vs COTS | **Custom Django build (SELECTED)** · Buy MS Dynamics 365 F&O (doc rec., considered & rejected) · SAP S/4HANA | Custom build | Management | **CONFIRMED — Custom build** *(NQ-001 REJECTED; business decision 2026-08-21)* | 2026-08-21 |
| **DR-040** | Company scope / multi-company | Single company · **Multi-company (NEPTA group)** | Multi-company; phase-1 SLZ + Helena | Management | **CONFIRMED (business fact)** *(NQ-002 for full list)* | 2026-08-21 |
| **DR-041** | Site-specific capability & capacity | Uniform capability · **Site-scoped capability + capacity** | Site declares capabilities; capacity tables site-scoped | Production + Planning | **OPEN** (modeling approach) | 2026-08-21 |
| **DR-042** | Material subtyping for MRP | Single RM class · **Subtyped (resin/ink/solvent/consumable/packaging/regrind)** | Subtype discriminator on material master | Engineering + Planning | **CONFIRMED (business fact)** | 2026-08-21 |
| **DR-043** | Outsourced production operations | In-house only · **Operations may be outsourced (internal/external)** | Routing operation carries execution locus + QC-on-return | Production + Management | **OPEN** *(NQ-004)* | 2026-08-21 |
| **DR-044** | Product classification taxonomy | Flat category · **type→class→family + product group** | Multi-level taxonomy | Engineering + Sales | **CONFIRMED (business fact)** | 2026-08-21 |

### Status changes to existing decisions

| ID | Old status | New status | Reason |
|----|-----------|-----------|--------|
| DR-001 Backend tech | PROPOSED — CONFLICT FLAGGED | **CONFIRMED-COMPATIBLE (Django/DRF)** | DR-000 resolved in favour of custom build (2026-08-21); backend stack conflict cleared. Stack remains a technical proposal but is no longer blocked by build-vs-buy. |
| DR-002 Database | PROPOSED — CONFLICT FLAGGED | **CONFIRMED-COMPATIBLE (PostgreSQL)** | Same as DR-001 — conflict cleared by NQ-001 resolution. |
| DR-011 Frontend | PROPOSED — CONFLICT FLAGGED | **CONFIRMED-COMPATIBLE (React/TS)** | Same as DR-001 — conflict cleared by NQ-001 resolution. |
| DR-006 Barcode/labeling | OPEN | **OPEN (evidence added)** | Doc confirms roll/lot traceability need; QR still recommended, granularity open (Q-046). |
| DR-036 Shelf-life/FEFO | OPEN | **OPEN (evidence added)** | Doc confirms expiry tracked in material planning; enforcement policy still open (Q-051). |
| DR-007 Accounting integration | OPEN | **OPEN (tension recorded)** | Doc shows a full finance domain is expected (reinforces C-006 / NQ-010); still deferred for now. |

*No existing decision is moved to CONFIRMED by the document except the newly added business facts (DR-040, DR-042, DR-044). All parametric business rules (valuation, tolerances, thresholds) remain OPEN — the document gives requirements, not the numbers.*

### 2026-08-21 — Business decision on NQ-001 (Build vs Buy)

**DECISION (CONFIRMED by SLZ business):** SLZ will **build a custom ERP/MES from scratch**. The Microsoft Dynamics 365 F&O recommendation in the NEPTA feasibility study was **considered but is not the selected direction**.

**Rationale (business):** the system is highly specialised around SLZ's made-to-order flexible-packaging operations — product engineering, specifications, production, traceability, quality, costing, and company-specific workflows. The purpose is to build the system around SLZ's actual operational model rather than adapt SLZ to a generic ERP.

**Effects:**
- **NQ-001 → REJECTED/RESOLVED** (custom build selected). It no longer gates domain implementation.
- **DR-000 → CONFIRMED (Custom build).**
- DR-001/002/011 build-vs-buy conflict flags cleared (stacks remain technical proposals, now unblocked).
- The D365 recommendation is retained in the reconciliation record as *considered and not selected*; it does **not** drive architecture.
- **Domain implementation may proceed** (Task 004 Master Data onward), still respecting all remaining OPEN business decisions and the SLZ-specific rules.
