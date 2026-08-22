import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { Warehouse } from '@/api/inventory';

/**
 * Browse warehouses (company/site-scoped storage locations). The store-type
 * column resolves its label from i18n; the enum itself is enforced server-side.
 */
export function WarehousesPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<Warehouse>('/inventory/warehouses/');

  const columns: Column<Warehouse>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    {
      headerKey: 'inventory.fields.storeType',
      render: (r) => t(`inventory.storeTypes.${r.store_type}`),
    },
    {
      headerKey: 'masterData.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];

  return (
    <CollectionView
      titleKey="inventory.warehouses.title"
      subtitleKey="inventory.warehouses.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        hasPermission('inventory.warehouse.manage') ? (
          <Link to="/inventory/warehouses/new">
            <Button size="sm">{t('inventory.warehouses.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}
