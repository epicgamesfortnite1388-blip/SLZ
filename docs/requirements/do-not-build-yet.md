# SLZ ERP — Do NOT Build Yet / فهرست «فعلاً نسازید»

Purpose: prevent future coding agents from implementing uncertain functionality before SLZ decides. Each item lists **why it's blocked** and the **gate** (decision/ID) that unblocks it. Nothing below may be coded while its gate is `OPEN`.

Status of every item: **BLOCKED** until the referenced decision is `CONFIRMED`.

## Business-logic blocked (need SLZ decisions)
1. **Final costing formulas & rates** — no validated rates/method/valuation. Gate: Q-031, Q-033, Q-034 (DR-026, DR-027). *Build the configurable structure only, never hard-code numbers.*
2. **Material valuation engine** (FIFO/WA/lot-actual) — Gate: Q-034 (DR-026).
3. **Profitability & KPI reports** — undefined dimensions/KPIs. Gate: Q-038 (DR-034).
4. **Over/under-delivery & invoicing basis** — Gate: Q-006/037 (DR-028).
5. **Tooling cost model** (customer-paid vs amortized) — Gate: Q-004/036 (DR-030).
6. **Scrap cost absorption & regrind/resale value** — Gate: Q-035, A-015.
7. **Approval hierarchy & thresholds engine content** — matrix undefined. Gate: Q-054/056 (DR-032). *Engine may be built; rules must not be hard-coded.*
8. **Final role catalogue & data-scoping rules** — Gate: Q-053, Q-055 (DR-033).
9. **BOM consumption bases, waste factors, standard scrap %** — Gate: Q-027, Q-016/042 (DR-025).
10. **Standard routing templates & stage-skip rules** — Gate: Q-029.
11. **Quality inspection plans, methods, sampling (AQL vs 100%)** — Gate: Q-039, Q-040.
12. **Rework-vs-scrap decision rules & reason codes** — Gate: Q-043, Q-016/042.
13. **Spec-revision trigger rule & approver** — Gate: Q-024 (DR-024).
14. **Product coding/numbering scheme** — Gate: Q-019 (DR-023).
15. **Sampling / first-article mandatory rules** — Gate: Q-003 (DR-029).
16. **Shelf-life / FEFO enforcement rules** — Gate: Q-051 (DR-036).
17. **Customer change-order & RMA policies** — Gate: A-006.

## Foundational data-model choices blocked (do not migrate schema until decided)
18. **Roll serialization vs lot+count** — Gate: Q-046 (DR-020). *Blocks the traceability schema — highest priority.*
19. **Inventoried intermediates / real BOM levels** — Gate: Q-026 (DR-021).
20. **Traceability granularity (roll/pallet/carton)** — Gate: Q-049 (DR-022).
21. **Material issue method (explicit vs backflush)** — Gate: Q-048 (DR-031).

## Explicitly deferred capabilities (out of scope for early phases)
22. **Production scheduling optimization / automatic APS** — manual/assisted first. Gate: DR-012.
23. **Accounting / GL / AR / AP integration** — boundary undefined. Gate: Q-061 (DR-007), constraint #10.
24. **Machine / IoT / PLC / SCADA integration** — manual capture first. Gate: Q-062 (DR-013).
25. **Advanced OEE analytics** — basic downtime capture first. Gate: Q-017.
26. **Automated pricing rules** — pricing policy undefined.
27. **AI / ML features** (e.g. auto BOM/routing generation, demand forecasting) — not requested; premature.
28. **Customer portal** — not in Task 001 scope.
29. **Mobile application** — not in Task 001 scope.
30. **WhatsApp / SMS / email notification integrations** — Gate: DR-008 (deferred).
31. **Formal recall/mock-recall automation** — Gate: Q-044 (DR-035). *Design traceability to allow it; don't build the workflow yet.*
32. **Barcode/QR/RFID hardware integration** — Gate: DR-006, tied to Q-049.

## Deployment/platform choices blocked
33. **Hosting model & data residency** (on-prem vs cloud) — Gate: Q-060 (DR-003).
34. **Authentication mechanism** (local/SSO/AD/kiosk) — Gate: Q-058 (DR-004).
35. **External-system migration** (spreadsheets, existing tools) — Gate: Q-061.

---

**Safe to build regardless (see Task 003 recommendation):** the reusable **platform foundation** — i18n (fa/en, RTL) + Jalali/Gregorian date layer, audit/versioning primitives, RBAC/approval *engine* (without hard-coded rules), object storage, containerized scaffold. These do not depend on any OPEN business decision.

**Count:** 35 blocked/deferred items.
