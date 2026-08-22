import { useAuth } from '@/auth/AuthContext';
import { CollectionView, type Column } from '@/components/CollectionView';
import { StatusBadge } from '@/components/ui';
import { useCollection } from '@/hooks/useCollection';
import type { TraceabilityUnit } from '@/api/inventory';

export function TraceabilityUnitsPage(): JSX.Element {
  const { hasPermission } = useAuth();
  const collection = useCollection<TraceabilityUnit>(
    '/inventory/traceability-units/?page_size=100',
  );
  const canView = hasPermission('inventory.movement.view');

  if (!canView) return <></>;

  const columns: Column<TraceabilityUnit>[] = [
    {
      headerKey: 'inventory.fields.identifier',
      render: (r) => r.identifier,
    },
    {
      headerKey: 'inventory.fields.unitType',
      render: (r) => (
        <StatusBadge
          status={r.unit_type}
          variant={r.unit_type === 'ROLL' ? 'info' : r.unit_type === 'BATCH' ? 'success' : 'neutral'}
          label={r.unit_type}
        />
      ),
    },
    { headerKey: 'materials.title', render: (r) => r.material ?? '—' },
    { headerKey: 'masterData.fields.quantity', render: (r) => r.quantity ?? '—', align: 'end' },
    { headerKey: 'inventory.fields.notes', render: (r) => r.notes || '—' },
  ];

  return (
    <CollectionView
      titleKey="inventory.traceability.title"
      subtitleKey="inventory.traceability.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
    />
  );
}