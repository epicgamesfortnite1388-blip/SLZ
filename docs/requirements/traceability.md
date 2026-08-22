# SLZ ERP — Traceability Matrix / ماتریس ردیابی

Purpose: let future development agents understand **why** each feature exists. Chain:
**Business Question/Assumption → Requirement → Domain Entity → Workflow → Future Module.**

Source IDs: Q-/A- from `../business-analysis/open-questions.md`; FR-/NFR- from `requirements-baseline.md`; entities/workflows/modules from `../business-analysis/open-questions.md` Part B.

| Origin (Q/A) | Requirement | Domain Entity | Workflow | Future Module |
|--------------|-------------|---------------|----------|---------------|
| product-model (core) | FR-001, FR-002 | CustomerProduct, ProductSpecification, ProductSpecificationRevision | Product-spec versioning | Engineering |
| constraint #4 | FR-003, FR-004, NFR-005 | ProductSpecificationRevision | Spec revision lifecycle | Engineering |
| product-model §3 | FR-005, FR-006 | SpecLayer, SpecParameter | Spec authoring | Engineering |
| Q-022 | FR-008 | SpecParameter (tolerances) | Spec authoring / QC limits | Engineering + Quality |
| Q-023 | FR-007 | SpecParameter (custom) | Customer-specific spec | Engineering |
| A-003 / Q-004/036 | FR-010, FR-095, DR-030 | Artwork, PrintingTooling, ToolingSet | Tooling lifecycle | Engineering + Costing |
| Q-024 | FR-011, DR-024 | ProductSpecificationRevision | Revision trigger/approval | Engineering |
| Q-025 | FR-012 | Artwork, ArtworkRevision | Artwork approval | Engineering |
| business-processes §5.1 | FR-021, FR-022 | Quotation, QuotationRevision, SalesOrder | Quote-to-order | Commercial |
| business-processes §5.2 | FR-023 | SalesOrder, SalesOrderLine | Sales-order lifecycle | Commercial |
| A-001 / Q-002 | FR-024 | SalesOrder, ProductSpecificationRevision | New-vs-repeat path | Commercial + Engineering |
| A-002 / Q-003 | FR-027, DR-029 | (Sample) ProductionOrder, QualityCheck | Sampling / first-article | Commercial + Quality + Manufacturing |
| A-006 | FR-025 | SalesOrder, Delivery (RMA) | Change orders / returns | Commercial + Quality |
| Q-006/037 | FR-026, DR-028 | SalesOrderLine, Delivery | Over/under-delivery | Commercial + Costing |
| Q-026 | FR-030, DR-021 | Bom, BomRevision, BomLine, Item(SFG) | BOM authoring | BOM/Routing + Inventory |
| A-012 / Q-027 | FR-032, FR-033, DR-025 | BomLine | BOM math / MRP | BOM/Routing + Planning |
| A-014 / Q-028 | FR-034 | BomLine (alternates) | Material substitution | BOM/Routing + Quality |
| Q-029 | FR-037 | Routing, RoutingRevision, Operation | Routing templates | BOM/Routing |
| bom-and-routing §4 | FR-038 | ProductionOrder (snapshot) | Production release | Manufacturing |
| Q-030 | FR-039 | Routing/Bom revision, ApprovalRule | BOM/Routing release | BOM/Routing + Platform |
| manufacturing §3 / #9 | FR-040, FR-048 | WorkCenter, Machine, MachineCapabilityProfile, ChangeoverMatrix | Machine capability config | Manufacturing |
| manufacturing §3.2 | FR-041, FR-042 | ProductionOrder, WorkOrder, WorkOrderConfirmation | Work-order execution | Manufacturing |
| A-011 / Q-016/042 | FR-043 | ScrapRecord | Scrap capture | Manufacturing + Costing |
| Q-043 | FR-044 | ReworkRecord, BatchGenealogy | Rework loop | Manufacturing + Quality |
| manufacturing §4 | FR-045, FR-100 | DowntimeEvent, MaintenanceOrder | Downtime / maintenance | Manufacturing + Maintenance |
| business-processes §5.5 | FR-046 | ProductionOrder | Production-order lifecycle | Manufacturing |
| manufacturing §3.4 | FR-047, FR-055 | ProductionBatch, Roll, BatchGenealogy | Genealogy / traceability | Manufacturing + Inventory |
| manufacturing §5 / Q-018 | FR-049, DR-012 | ProductionOrder, WorkCenter (capacity) | Planning / scheduling | Planning |
| inventory §1 | FR-050 | Item, RawMaterialLot | Incoming stock | Inventory + Procurement |
| Q-046 | FR-051, DR-020 | Roll | Roll tracking | Inventory |
| Q-047 | FR-052 | Warehouse, Location | Location management | Inventory |
| inventory §3 / #8 | FR-053, FR-054, NFR-006, NFR-008 | StockMovement | Stock posting (atomic) | Inventory |
| Q-049 | FR-060, DR-022 | RawMaterialLot, ProductionBatch, Roll | Trace granularity / recall | Inventory + Quality |
| A-019 / Q-005/050 | FR-056 | StockReservation, PurchaseRequest | Reservation / MRP shortfall | Planning + Procurement |
| A-021 / Q-052 | FR-057 | Uom, UomConversion | UoM conversion | Inventory |
| Q-048 | FR-058, DR-031 | StockMovement | Material issue method | Inventory + Manufacturing |
| A-020 / Q-051 | FR-059, DR-036 | RawMaterialLot (expiry) | Shelf-life / FEFO | Inventory + Quality |
| quality §1 | FR-070 | QualityPlan, QualityCharacteristic | QC plan authoring | Quality |
| A-005/018 / Q-039/040 | FR-071, FR-072 | QualityCheck | Inline & final QC | Quality |
| quality §4 / Q-041 | FR-073, FR-074 | QualityAlert, Disposition | NCR / disposition / hold | Quality |
| quality §6 / Q-044 | FR-075, DR-035 | BatchGenealogy, QualityCheck | Recall / mock-recall | Quality + Inventory |
| quality §7 / Q-045 | FR-076 | COA | COA issuance | Quality + Commercial |
| entity list | FR-080 | Supplier | Supplier management | Procurement |
| business-processes §5.6 | FR-081, FR-082 | PurchaseRequest, PurchaseOrder, GoodsReceipt, RawMaterialLot | Procure-to-receipt | Procurement + Inventory |
| A-004 / Q-005/050 | FR-083 | Item (stocked flag) | Stock vs buy-to-order | Procurement + Planning |
| costing §1/§7 | FR-090, FR-096 | CostRecord, OrderCostSettlement, ProfitabilityRecord | Cost capture / settlement | Costing |
| costing §2 / Q-032 | FR-091 | CostRecord (elements) | Cost taxonomy | Costing |
| costing §3 / Q-033 | FR-092, DR-027 | CostRate | Rate configuration | Costing |
| Q-034 | FR-093, DR-026 | StockMovement (valuation) | Inventory valuation | Costing + Inventory |
| A-015 / Q-035 | FR-094 | ScrapRecord, CostRecord | Scrap costing | Costing |
| Q-038 | FR-096, DR-034 | ProfitabilityRecord | Profitability reporting | Costing + Management |
| Q-031 | FR-097, DR-027 | CostRate, Quotation | Estimate-vs-actual | Costing |
| roles §4 / #5 | FR-110, NFR-005..007 | AuditLogEntry | Audit logging | Platform |
| roles §1–2 / Q-053 | FR-111, DR-033 | User, Role, Permission | RBAC | Platform |
| roles §2–3 / Q-054/056 | FR-112, DR-032 | ApprovalRule | Approval workflow | Platform |
| constraints #6/#7 | FR-113, NFR-010..012 | (all entities) i18n/date layer | Localization | Platform |
| architecture | FR-114, NFR-020 | (attachments) | Document storage | Platform |
| Q-057 | NFR-009 | AuditLogEntry | Retention/audit | Platform + Management |
| Q-058 | NFR-001, DR-004 | User | Authentication | Platform |
| Q-055 | NFR-002 | Role, Permission (scope) | Data-scoping | Platform |
| Q-059 | NFR-013, NFR-014 | (all) | Sizing/performance | Platform |
| Q-060 / Q-064 | NFR-021, NFR-022, DR-003 | (deployment) | Deployment | Platform + IT |
| Q-061 | NFR-023, DR-007 | (integration) | External integration | Platform + Finance |
| Q-062 | NFR-024, DR-013 | WorkOrderConfirmation | Shop-floor capture | Manufacturing + IT |

*Any FR/NFR without a validated origin decision must not be implemented until its `[BVR]`/`OPEN` items are resolved.*
