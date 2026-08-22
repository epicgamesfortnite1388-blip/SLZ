import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
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
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const columns = useColumns();
  const collection = useCollection<UnitOfMeasure>('/catalog/uoms/');
  return (
    <CollectionView
      titleKey="uoms.title"
      subtitleKey="uoms.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        hasPermission('catalog.uom.manage') ? (
          <Link to="/master-data/uoms/new">
            <Button size="sm">{t('uoms.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}
