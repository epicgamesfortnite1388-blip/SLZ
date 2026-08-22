import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { CollectionView, type Column } from '@/components/CollectionView';
import { StatusBadge } from '@/components/ui';
import { useCollection } from '@/hooks/useCollection';
import type { GoodsReceipt } from '@/api/grn';

export function GoodsReceiptsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<GoodsReceipt>('/procurement/grns/');
  const canView = hasPermission('procurement.grn.view');

  if (!canView) return <></>;

  const columns: Column<GoodsReceipt>[] = [
    { headerKey: 'procurement.fields.number', render: (r) => r.number },
    {
      headerKey: 'procurement.fields.status',
      render: (r) => <StatusBadge status={r.status} label={t(`procurement.reqStatuses.${r.status}`, r.status)} />,
    },
    { headerKey: 'procurement.fields.supplier', render: (r) => r.supplier },
    {
      headerKey: 'inventory.fields.warehouse',
      render: (r) => r.warehouse,
    },
    {
      headerKey: 'procurement.fields.notes',
      render: (r) => r.notes || '—',
    },
  ];

  return (
    <CollectionView
      titleKey="shipment.grns.title"
      subtitleKey="shipment.grns.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
    />
  );
}