import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { UnitOfMeasure } from '@/api/masterData';

function useColumns(canManage: boolean): Column<UnitOfMeasure>[] {
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
    ...(canManage
      ? [
          {
            headerKey: 'common.actions',
            render: (r: UnitOfMeasure) => (
              <Link to={`/master-data/uoms/${r.id}/edit`} className="link-inline">
                {t('common.edit')}
              </Link>
            ),
          },
        ]
      : []),
  ];
}

export function UomsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canManage = hasPermission('catalog.uom.manage');
  const columns = useColumns(canManage);
  const collection = useCollection<UnitOfMeasure>('/catalog/uoms/');
  return (
    <CollectionView
      titleKey="uoms.title"
      subtitleKey="uoms.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        canManage ? (
          <Link to="/master-data/uoms/new">
            <Button size="sm">{t('uoms.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}
