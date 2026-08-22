import { useTranslation } from 'react-i18next';
import { NavLink } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import type { PermissionCode } from '@/api/types';

interface NavItem {
  labelKey: string;
  to: string;
  permission?: PermissionCode;
  end?: boolean;
}

interface NavSection {
  labelKey: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    labelKey: 'nav.sectionOverview',
    items: [
      { labelKey: 'nav.dashboard', to: '/', end: true },
    ],
  },
  {
    labelKey: 'nav.sectionCommerce',
    items: [
      { labelKey: 'sales.orders.title', to: '/sales/orders', permission: 'sales.order.view' },
      { labelKey: 'procurement.requisitions.title', to: '/procurement/requisitions', permission: 'procurement.requisition.view' },
      { labelKey: 'procurement.orders.title', to: '/procurement/orders', permission: 'procurement.order.view' },
      { labelKey: 'shipment.grns.title', to: '/shipment/grns' },
    ],
  },
  {
    labelKey: 'nav.sectionOperations',
    items: [
      { labelKey: 'production.orders.title', to: '/production/orders', permission: 'production.order.view' },
      { labelKey: 'inventory.warehouses.title', to: '/inventory/warehouses', permission: 'inventory.warehouse.view' },
      { labelKey: 'inventory.traceability.title', to: '/inventory/traceability-units', permission: 'inventory.movement.view' },
      { labelKey: 'inventory.balances.title', to: '/inventory/balances', permission: 'catalog.material.view' },
    ],
  },
  {
    labelKey: 'nav.sectionQuality',
    items: [
      { labelKey: 'quality.characteristics.title', to: '/quality/characteristics', permission: 'quality.characteristic.view' },
      { labelKey: 'quality.plans.title', to: '/quality/plans', permission: 'quality.plan.view' },
      { labelKey: 'quality.checkResults.title', to: '/quality/check-results', permission: 'quality.results.view' },
    ],
  },
  {
    labelKey: 'nav.sectionMasterData',
    items: [
      { labelKey: 'nav.masterData', to: '/master-data', end: true },
      { labelKey: 'partners.title', to: '/master-data/partners', permission: 'partners.partner.view' },
      { labelKey: 'products.title', to: '/master-data/products', permission: 'catalog.product.view' },
      { labelKey: 'materials.title', to: '/master-data/materials', permission: 'catalog.material.view' },
      { labelKey: 'engineering.customerProducts.title', to: '/engineering/customer-products', permission: 'engineering.customerproduct.view' },
      { labelKey: 'engineering.specifications.title', to: '/engineering/specifications', permission: 'engineering.specification.view' },
    ],
  },
  {
    labelKey: 'nav.sectionEngineering',
    items: [
      { labelKey: 'manufacturing.boms.title', to: '/manufacturing/boms', permission: 'manufacturing.bom.view' },
      { labelKey: 'manufacturing.routings.title', to: '/manufacturing/routings', permission: 'manufacturing.routing.view' },
      { labelKey: 'manufacturing.workCenters.title', to: '/manufacturing/work-centers', permission: 'manufacturing.workcenter.view' },
      { labelKey: 'manufacturing.machines.title', to: '/manufacturing/machines', permission: 'manufacturing.machine.view' },
      { labelKey: 'tooling.title', to: '/engineering/tooling', permission: 'engineering.tooling.view' },
    ],
  },
  {
    labelKey: 'nav.sectionOrg',
    items: [
      { labelKey: 'organization.companies.title', to: '/organization/companies', permission: 'organization.company.view' },
      { labelKey: 'organization.sites.title', to: '/organization/sites', permission: 'organization.site.view' },
      { labelKey: 'organization.departments.title', to: '/organization/departments', permission: 'organization.department.view' },
      { labelKey: 'inventory.access.title', to: '/inventory/warehouse-access', permission: 'inventory.warehouseaccess.view' },
    ],
  },
  {
    labelKey: 'nav.sectionFinance',
    items: [
      { labelKey: 'costing.title', to: '/costing/summary', permission: 'costing.layer.view' },
      { labelKey: 'shipment.allocations.title', to: '/shipment/allocations', permission: 'shipment.allocation.view' },
    ],
  },
  {
    labelKey: 'nav.sectionAdmin',
    items: [
      { labelKey: 'approvals.title', to: '/workflow/approvals' },
      { labelKey: 'workflow.definitions.title', to: '/workflow/definitions', permission: 'workflow.definition.view' },
      { labelKey: 'notifications.title', to: '/notifications' },
      { labelKey: 'documents.title', to: '/documents', permission: 'documents.attachment.view' },
      { labelKey: 'audit.title', to: '/audit/logs', permission: 'audit.log.view' },
    ],
  },
  {
    labelKey: 'nav.sectionIdentity',
    items: [
      { labelKey: 'roles.title', to: '/identity/roles', permission: 'identity.role.manage' },
      { labelKey: 'users.title', to: '/identity/users', permission: 'identity.user.view' },
      { labelKey: 'permissions.title', to: '/identity/permissions', permission: 'identity.permission.view' },
    ],
  },
];

export function Sidebar(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();

  return (
    <nav className="sidebar" aria-label={t('nav.dashboard')}>
      <div className="sidebar__title">{t('app.title')}</div>
      {NAV_SECTIONS.map((section) => {
        const visibleItems = section.items.filter(
          (item) => !item.permission || hasPermission(item.permission),
        );
        // Hide empty sections entirely (e.g. costing for a non-coster).
        if (visibleItems.length === 0) return null;

        return (
          <div key={section.labelKey} className="sidebar__section">
            <div className="sidebar__section-title">{t(section.labelKey)}</div>
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
          </div>
        );
      })}
    </nav>
  );
}