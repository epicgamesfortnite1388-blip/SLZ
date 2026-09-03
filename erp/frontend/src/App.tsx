import { Route, Routes } from 'react-router-dom';
import { useDirection } from '@/i18n/useDirection';
import { ProtectedRoute } from '@/routes/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { MasterDataHomePage } from '@/pages/masterData/MasterDataHomePage';
import { PartnersPage } from '@/pages/masterData/PartnersPage';
import { PartnerEditPage } from '@/pages/masterData/PartnerEditPage';
import { PartnerCreatePage } from '@/pages/masterData/PartnerCreatePage';
import { PartnerDetailPage } from '@/pages/masterData/PartnerDetailPage';
import { ProductsPage } from '@/pages/masterData/ProductsPage';
import { ProductCreatePage } from '@/pages/masterData/ProductCreatePage';
import { ProductsDetailPage } from '@/pages/masterData/ProductsDetailPage';
import { ProductGroupsPage } from '@/pages/masterData/ProductGroupsPage';
import { ProductGroupCreatePage } from '@/pages/masterData/ProductGroupCreatePage';
import { ProductTypesPage } from '@/pages/masterData/ProductTypesPage';
import { ProductTypeCreatePage } from '@/pages/masterData/ProductTypeCreatePage';
import { ProductClassesPage } from '@/pages/masterData/ProductClassesPage';
import { ProductClassCreatePage } from '@/pages/masterData/ProductClassCreatePage';
import { ProductFamiliesPage } from '@/pages/masterData/ProductFamiliesPage';
import { ProductFamilyCreatePage } from '@/pages/masterData/ProductFamilyCreatePage';
import { MaterialsPage } from '@/pages/masterData/MaterialsPage';
import { MaterialCreatePage } from '@/pages/masterData/MaterialCreatePage';
import { MaterialDetailPage } from '@/pages/masterData/MaterialDetailPage';
import { UomsPage } from '@/pages/masterData/UomsPage';
import { UomCreatePage } from '@/pages/masterData/UomCreatePage';
import { UomConversionsPage } from '@/pages/masterData/UomConversionsPage';
import { UomConversionCreatePage } from '@/pages/masterData/UomConversionCreatePage';
import { EmployeesPage } from '@/pages/masterData/EmployeesPage';
import { EmployeeDetailPage } from '@/pages/masterData/EmployeeDetailPage';
import { EmployeeCreatePage } from '@/pages/masterData/EmployeeCreatePage';
import { CustomerProductsPage } from '@/pages/engineering/CustomerProductsPage';
import { CustomerProductCreatePage } from '@/pages/engineering/CustomerProductCreatePage';
import { CustomerProductDetailPage } from '@/pages/engineering/CustomerProductDetailPage';
import { SpecificationsPage } from '@/pages/engineering/SpecificationsPage';
import { ToolingAssetsPage } from '@/pages/engineering/ToolingAssetsPage';
import { ToolingAssetCreatePage } from '@/pages/engineering/ToolingAssetCreatePage';
import { ToolingAssetDetailPage } from '@/pages/engineering/ToolingAssetDetailPage';
import { WorkCentersPage } from '@/pages/manufacturing/WorkCentersPage';
import { WorkCenterCreatePage } from '@/pages/manufacturing/WorkCenterCreatePage';
import { WorkCenterDetailPage } from '@/pages/manufacturing/WorkCenterDetailPage';
import { MachinesPage } from '@/pages/manufacturing/MachinesPage';
import { MachineCreatePage } from '@/pages/manufacturing/MachineCreatePage';
import { MachineDetailPage } from '@/pages/manufacturing/MachineDetailPage';
import { BomRevisionsPage } from '@/pages/manufacturing/BomRevisionsPage';
import { BomRootsPage } from '@/pages/manufacturing/BomRootsPage';
import { BomRootCreatePage } from '@/pages/manufacturing/BomRootCreatePage';
import { BomRootDetailPage } from '@/pages/manufacturing/BomRootDetailPage';
import { RoutingRevisionsPage } from '@/pages/manufacturing/RoutingRevisionsPage';
import { RoutingRootDetailPage } from '@/pages/manufacturing/RoutingRootDetailPage';
import { RoutingRootsPage } from '@/pages/manufacturing/RoutingRootsPage';
import { RoutingRootCreatePage } from '@/pages/manufacturing/RoutingRootCreatePage';
import { WarehousesPage } from '@/pages/inventory/WarehousesPage';
import { WarehouseCreatePage } from '@/pages/inventory/WarehouseCreatePage';
import { WarehouseDetailPage } from '@/pages/inventory/WarehouseDetailPage';
import { WarehouseAccessPage } from '@/pages/inventory/WarehouseAccessPage';
import { TraceabilityUnitsPage } from '@/pages/inventory/TraceabilityUnitsPage';
import { StockBalancesPage } from '@/pages/inventory/StockBalancesPage';
import { CharacteristicsPage } from '@/pages/quality/CharacteristicsPage';
import { CharacteristicCreatePage } from '@/pages/quality/CharacteristicCreatePage';
import { QualityPlanRevisionsPage } from '@/pages/quality/QualityPlanRevisionsPage';
import { QualityPlanRootsPage } from '@/pages/quality/QualityPlanRootsPage';
import { QualityPlanRootCreatePage } from '@/pages/quality/QualityPlanRootCreatePage';
import { QualityPlanRootDetailPage } from '@/pages/quality/QualityPlanRootDetailPage';
import { QualityCheckResultsPage } from '@/pages/quality/QualityCheckResultsPage';
import { PurchaseRequisitionsPage } from '@/pages/procurement/PurchaseRequisitionsPage';
import { PurchaseRequisitionCreatePage } from '@/pages/procurement/PurchaseRequisitionCreatePage';
import { PurchaseOrdersPage } from '@/pages/procurement/PurchaseOrdersPage';
import { PurchaseOrderCreatePage } from '@/pages/procurement/PurchaseOrderCreatePage';
import { PurchaseOrderDetailPage } from '@/pages/procurement/PurchaseOrderDetailPage';
import { PurchaseRequisitionDetailPage } from '@/pages/procurement/PurchaseRequisitionDetailPage';
import { SalesOrdersPage } from '@/pages/sales/SalesOrdersPage';
import { SalesOrderCreatePage } from '@/pages/sales/SalesOrderCreatePage';
import { SalesOrderDetailPage } from '@/pages/sales/SalesOrderDetailPage';
import { ProductionOrdersPage } from '@/pages/production/ProductionOrdersPage';
import { ProductionOrderCreatePage } from '@/pages/production/ProductionOrderCreatePage';
import { ProductionOrderDetailPage } from '@/pages/production/ProductionOrderDetailPage';
import { ProductionExecutionCenter } from '@/pages/production/ProductionExecutionCenter';
import { AllocationsPage } from '@/pages/shipment/AllocationsPage';
import { GoodsReceiptsPage } from '@/pages/shipment/GoodsReceiptsPage';
import { ShipmentsPage } from '@/pages/shipment/ShipmentsPage';
import { PlanningPoliciesPage } from '@/pages/planning/PlanningPoliciesPage';
import { PlanningPolicyCreatePage } from '@/pages/planning/PlanningPolicyCreatePage';
import { PlanningRunPage } from '@/pages/planning/PlanningRunPage';
import { RecallsPage } from '@/pages/recall/RecallsPage';
import { RecallCreatePage } from '@/pages/recall/RecallCreatePage';
import { RecallDetailPage } from '@/pages/recall/RecallDetailPage';
import { CostSummaryPage } from '@/pages/costing/CostSummaryPage';
import { ApprovalsPage } from '@/pages/workflow/ApprovalsPage';
import { WorkflowDefinitionsPage } from '@/pages/workflow/WorkflowDefinitionsPage';
import { WorkflowDefinitionCreatePage } from '@/pages/workflow/WorkflowDefinitionCreatePage';
import { NotificationsPage } from '@/pages/notifications/NotificationsPage';
import { AuditLogPage } from '@/pages/audit/AuditLogPage';
import { RolesPage } from '@/pages/identity/RolesPage';
import { RoleCreatePage } from '@/pages/identity/RoleCreatePage';
import { RoleDetailPage } from '@/pages/identity/RoleDetailPage';
import { UsersPage } from '@/pages/identity/UsersPage';
import { UserCreatePage } from '@/pages/identity/UserCreatePage';
import { UserEditPage } from '@/pages/identity/UserEditPage';
import { PermissionsPage } from '@/pages/identity/PermissionsPage';
import { DocumentsPage } from '@/pages/documents/DocumentsPage';
import { CompaniesPage } from '@/pages/organization/CompaniesPage';
import { CompanyCreatePage } from '@/pages/organization/CompanyCreatePage';
import { SitesPage } from '@/pages/organization/SitesPage';
import { SiteCreatePage } from '@/pages/organization/SiteCreatePage';
import { DepartmentsPage, DepartmentCreatePage } from '@/pages/organization/DepartmentsPage';
import { SiteCapabilitiesPage, SiteCapabilityCreatePage } from '@/pages/organization/SiteCapabilitiesPage';

/** Root application: keeps direction in sync and declares the route table. */
export default function App(): JSX.Element {
  // Keep <html dir/lang> aligned with the active language.
  useDirection();

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />

        <Route path="master-data">
          <Route index element={<MasterDataHomePage />} />
          <Route
            path="partners"
            element={
              <ProtectedRoute requiredPermission="partners.partner.view">
                <PartnersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="partners/new"
            element={
              <ProtectedRoute requiredPermission="partners.partner.manage">
                <PartnerCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="partners/:id"
            element={
              <ProtectedRoute requiredPermission="partners.partner.view">
                <PartnerDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="partners/:id/edit"
            element={
              <ProtectedRoute requiredPermission="partners.partner.manage">
                <PartnerEditPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="products"
            element={
              <ProtectedRoute requiredPermission="catalog.product.view">
                <ProductsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="products/new"
            element={
              <ProtectedRoute requiredPermission="catalog.product.manage">
                <ProductCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="products/:id"
            element={
              <ProtectedRoute requiredPermission="catalog.product.view">
                <ProductsDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="product-groups"
            element={
              <ProtectedRoute requiredPermission="catalog.productgroup.view">
                <ProductGroupsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="product-groups/new"
            element={
              <ProtectedRoute requiredPermission="catalog.productgroup.manage">
                <ProductGroupCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="product-types"
            element={
              <ProtectedRoute requiredPermission="catalog.producttaxonomy.view">
                <ProductTypesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="product-types/new"
            element={
              <ProtectedRoute requiredPermission="catalog.producttaxonomy.manage">
                <ProductTypeCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="product-classes"
            element={
              <ProtectedRoute requiredPermission="catalog.producttaxonomy.view">
                <ProductClassesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="product-classes/new"
            element={
              <ProtectedRoute requiredPermission="catalog.producttaxonomy.manage">
                <ProductClassCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="product-families"
            element={
              <ProtectedRoute requiredPermission="catalog.producttaxonomy.view">
                <ProductFamiliesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="product-families/new"
            element={
              <ProtectedRoute requiredPermission="catalog.producttaxonomy.manage">
                <ProductFamilyCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="materials"
            element={
              <ProtectedRoute requiredPermission="catalog.material.view">
                <MaterialsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="materials/new"
            element={
              <ProtectedRoute requiredPermission="catalog.material.manage">
                <MaterialCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="materials/:id"
            element={
              <ProtectedRoute requiredPermission="catalog.material.view">
                <MaterialDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="uoms/new"
            element={
              <ProtectedRoute requiredPermission="catalog.uom.manage">
                <UomCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="uoms"
            element={
              <ProtectedRoute requiredPermission="catalog.uom.view">
                <UomsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="uom-conversions"
            element={
              <ProtectedRoute requiredPermission="catalog.uom.view">
                <UomConversionsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="uom-conversions/new"
            element={
              <ProtectedRoute requiredPermission="catalog.uom.manage">
                <UomConversionCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="employees"
            element={
              <ProtectedRoute requiredPermission="hr.employee.view">
                <EmployeesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="employees/new"
            element={
              <ProtectedRoute requiredPermission="hr.employee.manage">
                <EmployeeCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="employees/:id"
            element={
              <ProtectedRoute requiredPermission="hr.employee.view">
                <EmployeeDetailPage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="engineering">
          <Route
            path="customer-products"
            element={
              <ProtectedRoute requiredPermission="engineering.customerproduct.view">
                <CustomerProductsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="customer-products/new"
            element={
              <ProtectedRoute requiredPermission="engineering.customerproduct.manage">
                <CustomerProductCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="customer-products/:id"
            element={
              <ProtectedRoute requiredPermission="engineering.customerproduct.view">
                <CustomerProductDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="specifications"
            element={
              <ProtectedRoute requiredPermission="engineering.specification.view">
                <SpecificationsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="tooling"
            element={
              <ProtectedRoute requiredPermission="engineering.tooling.view">
                <ToolingAssetsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="tooling/new"
            element={
              <ProtectedRoute requiredPermission="engineering.tooling.manage">
                <ToolingAssetCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="tooling/:id"
            element={
              <ProtectedRoute requiredPermission="engineering.tooling.view">
                <ToolingAssetDetailPage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="manufacturing">
          <Route
            path="work-centers"
            element={
              <ProtectedRoute requiredPermission="manufacturing.workcenter.view">
                <WorkCentersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="work-centers/new"
            element={
              <ProtectedRoute requiredPermission="manufacturing.workcenter.manage">
                <WorkCenterCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="work-centers/:id"
            element={
              <ProtectedRoute requiredPermission="manufacturing.workcenter.view">
                <WorkCenterDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="machines"
            element={
              <ProtectedRoute requiredPermission="manufacturing.machine.view">
                <MachinesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="machines/new"
            element={
              <ProtectedRoute requiredPermission="manufacturing.machine.manage">
                <MachineCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="machines/:id"
            element={
              <ProtectedRoute requiredPermission="manufacturing.machine.view">
                <MachineDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="boms"
            element={
              <ProtectedRoute requiredPermission="manufacturing.bom.view">
                <BomRootsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="boms/new"
            element={
              <ProtectedRoute requiredPermission="manufacturing.bom.manage">
                <BomRootCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="boms/:id"
            element={
              <ProtectedRoute requiredPermission="manufacturing.bom.view">
                <BomRootDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="boms/:rootId/revisions"
            element={
              <ProtectedRoute requiredPermission="manufacturing.bom.view">
                <BomRootDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="bom-revisions"
            element={
              <ProtectedRoute requiredPermission="manufacturing.bom.view">
                <BomRevisionsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="routings"
            element={
              <ProtectedRoute requiredPermission="manufacturing.routing.view">
                <RoutingRootsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="routings/new"
            element={
              <ProtectedRoute requiredPermission="manufacturing.routing.manage">
                <RoutingRootCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="routings/:rootId/revisions"
            element={
              <ProtectedRoute requiredPermission="manufacturing.routing.view">
                <RoutingRootDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="routing-revisions"
            element={
              <ProtectedRoute requiredPermission="manufacturing.routing.view">
                <RoutingRevisionsPage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="inventory">
          <Route
            path="warehouses"
            element={
              <ProtectedRoute requiredPermission="inventory.warehouse.view">
                <WarehousesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="warehouses/new"
            element={
              <ProtectedRoute requiredPermission="inventory.warehouse.manage">
                <WarehouseCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="warehouses/:id"
            element={
              <ProtectedRoute requiredPermission="inventory.warehouse.view">
                <WarehouseDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="warehouse-access"
            element={
              <ProtectedRoute requiredPermission="inventory.warehouseaccess.view">
                <WarehouseAccessPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="traceability-units"
            element={
              <ProtectedRoute requiredPermission="inventory.movement.view">
                <TraceabilityUnitsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="balances"
            element={
              <ProtectedRoute requiredPermission="catalog.material.view">
                <StockBalancesPage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="quality">
          <Route
            path="characteristics"
            element={
              <ProtectedRoute requiredPermission="quality.characteristic.view">
                <CharacteristicsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="characteristics/new"
            element={
              <ProtectedRoute requiredPermission="quality.characteristic.manage">
                <CharacteristicCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="plans"
            element={
              <ProtectedRoute requiredPermission="quality.plan.view">
                <QualityPlanRootsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="plans/new"
            element={
              <ProtectedRoute requiredPermission="quality.plan.manage">
                <QualityPlanRootCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="plans/:id"
            element={
              <ProtectedRoute requiredPermission="quality.plan.view">
                <QualityPlanRootDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="plan-revisions"
            element={
              <ProtectedRoute requiredPermission="quality.plan.view">
                <QualityPlanRevisionsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="check-results"
            element={
              <ProtectedRoute requiredPermission="quality.results.view">
                <QualityCheckResultsPage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="procurement">
          <Route
            path="requisitions"
            element={
              <ProtectedRoute requiredPermission="procurement.requisition.view">
                <PurchaseRequisitionsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="requisitions/:id"
            element={
              <ProtectedRoute requiredPermission="procurement.requisition.view">
                <PurchaseRequisitionDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="requisitions/new"
            element={
              <ProtectedRoute requiredPermission="procurement.requisition.manage">
                <PurchaseRequisitionCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="orders"
            element={
              <ProtectedRoute requiredPermission="procurement.order.view">
                <PurchaseOrdersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="orders/:id"
            element={
              <ProtectedRoute requiredPermission="procurement.order.view">
                <PurchaseOrderDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="orders/new"
            element={
              <ProtectedRoute requiredPermission="procurement.order.manage">
                <PurchaseOrderCreatePage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="sales">
          <Route
            path="orders"
            element={
              <ProtectedRoute requiredPermission="sales.order.view">
                <SalesOrdersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="orders/:id"
            element={
              <ProtectedRoute requiredPermission="sales.order.view">
                <SalesOrderDetailPage />
              </ProtectedRoute>
            }
 />
          <Route
            path="orders/new"
            element={
              <ProtectedRoute requiredPermission="sales.order.manage">
                <SalesOrderCreatePage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="production">
          <Route
            path="orders"
            element={
              <ProtectedRoute requiredPermission="production.order.view">
                <ProductionOrdersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="orders/:id"
            element={
              <ProtectedRoute requiredPermission="production.order.view">
                <ProductionOrderDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="orders/new"
            element={
              <ProtectedRoute requiredPermission="production.order.manage">
                <ProductionOrderCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="execution-center"
            element={
              <ProtectedRoute requiredPermission="production.execution.view">
                <ProductionExecutionCenter />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="organization">
          <Route
            path="companies"
            element={
              <ProtectedRoute requiredPermission="organization.company.view">
                <CompaniesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="companies/new"
            element={
              <ProtectedRoute requiredPermission="organization.company.manage">
                <CompanyCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="sites"
            element={
              <ProtectedRoute requiredPermission="organization.site.view">
                <SitesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="sites/new"
            element={
              <ProtectedRoute requiredPermission="organization.site.manage">
                <SiteCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="departments"
            element={
              <ProtectedRoute requiredPermission="organization.department.view">
                <DepartmentsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="departments/new"
            element={
              <ProtectedRoute requiredPermission="organization.department.manage">
                <DepartmentCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="site-capabilities"
            element={
              <ProtectedRoute requiredPermission="organization.sitecapability.view">
                <SiteCapabilitiesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="site-capabilities/new"
            element={
              <ProtectedRoute requiredPermission="organization.sitecapability.manage">
                <SiteCapabilityCreatePage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="workflow">
          <Route
            path="approvals"
            element={
              <ProtectedRoute>
                <ApprovalsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="definitions"
            element={
              <ProtectedRoute requiredPermission="workflow.definition.view">
                <WorkflowDefinitionsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="definitions/new"
            element={
              <ProtectedRoute requiredPermission="workflow.definition.manage">
                <WorkflowDefinitionCreatePage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route
          path="notifications"
          element={
            <ProtectedRoute>
              <NotificationsPage />
            </ProtectedRoute>
          }
        />

        <Route path="/identity">
          <Route
            path="roles"
            element={
              <ProtectedRoute requiredPermission="identity.role.manage">
                <RolesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="roles/new"
            element={
              <ProtectedRoute requiredPermission="identity.role.manage">
                <RoleCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="roles/:id"
            element={
              <ProtectedRoute requiredPermission="identity.role.manage">
                <RoleDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="users"
            element={
              <ProtectedRoute requiredPermission="identity.user.view">
                <UsersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="users/new"
            element={
              <ProtectedRoute requiredPermission="identity.user.manage">
                <UserCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="users/:id/edit"
            element={
              <ProtectedRoute requiredPermission="identity.user.manage">
                <UserEditPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="permissions"
            element={
              <ProtectedRoute requiredPermission="identity.permission.view">
                <PermissionsPage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route
          path="documents"
          element={
            <ProtectedRoute requiredPermission="documents.attachment.view">
              <DocumentsPage />
            </ProtectedRoute>
          }
        />


        <Route path="audit">
          <Route
            path="logs"
            element={
              <ProtectedRoute requiredPermission="audit.log.view">
                <AuditLogPage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="costing">
          <Route
            path="summary"
            element={
              <ProtectedRoute requiredPermission="costing.layer.view">
                <CostSummaryPage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="planning">
          <Route
            path="policies"
            element={
              <ProtectedRoute requiredPermission="planning.policy.view">
                <PlanningPoliciesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="policies/new"
            element={
              <ProtectedRoute requiredPermission="planning.policy.manage">
                <PlanningPolicyCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="run"
            element={
              <ProtectedRoute requiredPermission="planning.suggestion.view">
                <PlanningRunPage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="recall">
          <Route
            path="recalls"
            element={
              <ProtectedRoute requiredPermission="recall.recall.view">
                <RecallsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="recalls/new"
            element={
              <ProtectedRoute requiredPermission="recall.recall.manage">
                <RecallCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="recalls/:id"
            element={
              <ProtectedRoute requiredPermission="recall.recall.view">
                <RecallDetailPage />
              </ProtectedRoute>
            }
          />
        </Route>

        <Route path="shipment">
          <Route
            path="allocations"
            element={
              <ProtectedRoute requiredPermission="shipment.allocation.view">
                <AllocationsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="deliveries"
            element={
              <ProtectedRoute requiredPermission="shipment.delivery.view">
                <ShipmentsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="grns"
            element={
              <ProtectedRoute requiredPermission="procurement.grn.view">
                <GoodsReceiptsPage />
              </ProtectedRoute>
            }
          />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
