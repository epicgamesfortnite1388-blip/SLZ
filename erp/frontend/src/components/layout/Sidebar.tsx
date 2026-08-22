import { useTranslation } from 'react-i18next';
import { NavLink } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import type { PermissionCode } from '@/api/types';

interface NavItem {
  /** i18n key for the label. */
  labelKey: string;
  to: string;
  /** Permission required to see this item; omit for always-visible. */
  permission?: PermissionCode;
  end?: boolean;
}

/**
 * Navigation model. Only the dashboard exists in the foundation shell.
 * Future modules add entries here with their `module.resource.action` permission.
 */
const NAV_ITEMS: NavItem[] = [
  { labelKey: 'nav.dashboard', to: '/', end: true },
  { labelKey: 'nav.masterData', to: '/master-data', end: true },
  { labelKey: 'organization.companies.title', to: '/organization/companies', permission: 'organization.company.view' },
  { labelKey: 'organization.sites.title', to: '/organization/sites', permission: 'organization.site.view' },
  { labelKey: 'organization.departments.title', to: '/organization/departments', permission: 'organization.department.view' },
  { labelKey: 'organization.siteCapabilities.title', to: '/organization/site-capabilities', permission: 'organization.sitecapability.view' },
  { labelKey: 'partners.title', to: '/master-data/partners', permission: 'partners.partner.view' },
  { labelKey: 'products.title', to: '/master-data/products', permission: 'catalog.product.view' },
  { labelKey: 'productGroups.title', to: '/master-data/product-groups', permission: 'catalog.productgroup.view' },
  { labelKey: 'productTypes.title', to: '/master-data/product-types', permission: 'catalog.producttaxonomy.view' },
  { labelKey: 'productClasses.title', to: '/master-data/product-classes', permission: 'catalog.producttaxonomy.view' },
  { labelKey: 'productFamilies.title', to: '/master-data/product-families', permission: 'catalog.producttaxonomy.view' },
  { labelKey: 'materials.title', to: '/master-data/materials', permission: 'catalog.material.view' },
  { labelKey: 'uoms.title', to: '/master-data/uoms', permission: 'catalog.uom.view' },
  { labelKey: 'uomConversions.title', to: '/master-data/uom-conversions', permission: 'catalog.uom.view' },
  { labelKey: 'employees.title', to: '/master-data/employees', permission: 'hr.employee.view' },
  { labelKey: 'engineering.customerProducts.title', to: '/engineering/customer-products', permission: 'engineering.customerproduct.view' },
  { labelKey: 'engineering.specifications.title', to: '/engineering/specifications', permission: 'engineering.specification.view' },
  { labelKey: 'tooling.title', to: '/engineering/tooling', permission: 'engineering.tooling.view' },
  { labelKey: 'manufacturing.workCenters.title', to: '/manufacturing/work-centers', permission: 'manufacturing.workcenter.view' },
  { labelKey: 'manufacturing.machines.title', to: '/manufacturing/machines', permission: 'manufacturing.machine.view' },
  { labelKey: 'manufacturing.boms.title', to: '/manufacturing/boms', permission: 'manufacturing.bom.view' },
  { labelKey: 'manufacturing.routings.title', to: '/manufacturing/routings', permission: 'manufacturing.routing.view' },
  { labelKey: 'inventory.warehouses.title', to: '/inventory/warehouses', permission: 'inventory.warehouse.view' },
  { labelKey: 'inventory.access.title', to: '/inventory/warehouse-access', permission: 'inventory.warehouseaccess.view' },
  { labelKey: 'quality.characteristics.title', to: '/quality/characteristics', permission: 'quality.characteristic.view' },
  { labelKey: 'quality.plans.title', to: '/quality/plans', permission: 'quality.plan.view' },
  { labelKey: 'procurement.requisitions.title', to: '/procurement/requisitions', permission: 'procurement.requisition.view' },
  { labelKey: 'procurement.orders.title', to: '/procurement/orders', permission: 'procurement.order.view' },
  { labelKey: 'sales.orders.title', to: '/sales/orders', permission: 'sales.order.view' },
  { labelKey: 'production.orders.title', to: '/production/orders', permission: 'production.order.view' },
  { labelKey: 'approvals.title', to: '/workflow/approvals' },
  { labelKey: 'workflow.definitions.title', to: '/workflow/definitions', permission: 'workflow.definition.view' },
  { labelKey: 'notifications.title', to: '/notifications' },
  { labelKey: 'documents.title', to: '/documents', permission: 'documents.attachment.view' },
  { labelKey: 'audit.title', to: '/audit/logs', permission: 'audit.log.view' },
  { labelKey: 'roles.title', to: '/identity/roles', permission: 'identity.role.manage' },
  { labelKey: 'users.title', to: '/identity/users', permission: 'identity.user.view' },
];

/** App sidebar. Items are filtered by the current user's permissions. */
export function Sidebar(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();

  const visibleItems = NAV_ITEMS.filter(
    (item) => !item.permission || hasPermission(item.permission),
  );

  return (
    <nav className="sidebar" aria-label={t('nav.dashboard')}>
      <div className="sidebar__title">{t('app.title')}</div>
      {visibleItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) =>
            `sidebar__link${isActive ? ' is-active' : ''}`
          }
        >
          <span className="sidebar__label">{t(item.labelKey)}</span>
        </NavLink>
      ))}
    </nav>
  );
}
