import { useTranslation } from 'react-i18next';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { UnitOfMeasure } from '@/api/masterData';

function useColumns(): Column<UnitOfMeasure>[] {
  const { t } = useTranslation();
  return [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    {
      headerKey: 'uoms.dimension',
      render: (r) => t(`uoms.dimensions.${r.dimension}`, { defaultValue: r.dimension }),
    },
    {
      headerKey: 'masterData.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];
}

export function UomsPage(): JSX.Element {
  const columns = useColumns();
  const collection = useCollection<UnitOfMeasure>('/catalog/uoms/');
  return (
    <CollectionView
      titleKey="uoms.title"
      subtitleKey="uoms.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
    />
  );
}
