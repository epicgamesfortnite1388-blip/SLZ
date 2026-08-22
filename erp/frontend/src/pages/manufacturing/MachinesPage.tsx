import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { Machine } from '@/api/manufacturing';

/**
 * Browse machines. ``capability_profile`` is data-driven free-form JSON (web
 * width, color stations, speeds, …); the column renders its key count only —
 * adding a machine is adding data, never code (constraint #9).
 */
export function MachinesPage(): JSX.Element {
  const collection = useCollection<Machine>('/manufacturing/machines/');

  const columns: Column<Machine>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    {
      headerKey: 'manufacturing.fields.capabilities',
      render: (r) => Object.keys(r.capability_profile ?? {}).length,
      align: 'center',
    },
    {
      headerKey: 'masterData.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];

  return (
    <CollectionView
      titleKey="manufacturing.machines.title"
      subtitleKey="manufacturing.machines.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
    />
  );
}
