import { useTranslation } from 'react-i18next';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { WarehouseAccess } from '@/api/inventory';

/**
 * Browse per-user warehouse access grants (SR-10). Read-only in the foundation
 * slice: grants are created via the audited backend write path. ``warehouse``
 * and ``user`` are surfaced as their identifiers; the access level resolves its
 * label from i18n.
 */
export function WarehouseAccessPage(): JSX.Element {
  const { t } = useTranslation();
  const collection = useCollection<WarehouseAccess>('/inventory/warehouse-access/');

  const columns: Column<WarehouseAccess>[] = [
    { headerKey: 'inventory.fields.warehouse', render: (r) => r.warehouse },
    { headerKey: 'inventory.fields.user', render: (r) => r.user },
    {
      headerKey: 'inventory.fields.accessLevel',
      render: (r) => t(`inventory.accessLevels.${r.access_level}`),
      align: 'center',
    },
  ];

  return (
    <CollectionView
      titleKey="inventory.access.title"
      subtitleKey="inventory.access.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
    />
  );
}
