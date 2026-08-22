import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Card } from '@/components/ui';
import type { PermissionCode } from '@/api/types';

interface Section {
  to: string;
  titleKey: string;
  descKey: string;
  permission: PermissionCode;
}

const SECTIONS: Section[] = [
  { to: '/master-data/partners', titleKey: 'partners.title', descKey: 'partners.subtitle', permission: 'partners.partner.view' },
  { to: '/master-data/product-groups', titleKey: 'productGroups.title', descKey: 'productGroups.subtitle', permission: 'catalog.productgroup.view' },
  { to: '/master-data/product-types', titleKey: 'productTypes.title', descKey: 'productTypes.subtitle', permission: 'catalog.producttaxonomy.view' },
  { to: '/master-data/product-classes', titleKey: 'productClasses.title', descKey: 'productClasses.subtitle', permission: 'catalog.producttaxonomy.view' },
  { to: '/master-data/product-families', titleKey: 'productFamilies.title', descKey: 'productFamilies.subtitle', permission: 'catalog.producttaxonomy.view' },
  { to: '/master-data/products', titleKey: 'products.title', descKey: 'products.subtitle', permission: 'catalog.product.view' },
  { to: '/master-data/materials', titleKey: 'materials.title', descKey: 'materials.subtitle', permission: 'catalog.material.view' },
  { to: '/master-data/uoms', titleKey: 'uoms.title', descKey: 'uoms.subtitle', permission: 'catalog.uom.view' },
  { to: '/master-data/uom-conversions', titleKey: 'uomConversions.title', descKey: 'uomConversions.subtitle', permission: 'catalog.uom.view' },
  { to: '/master-data/employees', titleKey: 'employees.title', descKey: 'employees.subtitle', permission: 'hr.employee.view' },
];

/** Master-data hub. Cards are filtered by the user's view permissions. */
export function MasterDataHomePage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();

  const visible = SECTIONS.filter((s) => hasPermission(s.permission));

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('masterData.title')}</h1>
        <p className="page-header__subtitle">{t('masterData.subtitle')}</p>
      </div>

      {visible.length === 0 ? (
        <Card>
          <div className="table-state table-state--empty">
            {t('masterData.noAccess')}
          </div>
        </Card>
      ) : (
        <div className="stat-grid">
          {visible.map((s) => (
            <Link key={s.to} to={s.to} className="link-card">
              <Card>
                <div className="stat-card__label">{t(s.titleKey)}</div>
                <div className="stat-card__note">{t(s.descKey)}</div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
