import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { Button } from '@/components/ui';
import { useCollection } from '@/hooks/useCollection';
import type { Material } from '@/api/masterData';

function useColumns(): Column<Material>[] {
  const { t } = useTranslation();
  return [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    {
      headerKey: 'materials.subtype',
      render: (r) => t(`materials.subtypes.${r.subtype}`, { defaultValue: r.subtype }),
    },
    {
      headerKey: 'materials.hazardous',
      render: (r) => <BoolCell value={r.is_hazardous} />,
      align: 'center',
    },
    {
      headerKey: 'masterData.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];
}

export function MaterialsPage(): JSX.Element {
  const { t } = useTranslation();
  const columns = useColumns();
  const collection = useCollection<Material>('/catalog/materials/');
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  
  const canManage = hasPermission('catalog.material.manage');
  
  return (
    <CollectionView
      titleKey="materials.title"
      subtitleKey="materials.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      onRowClick={(row) => navigate(`/master-data/materials/${row.id}`)}
      headerAction={
        canManage ? (
          <Link to="/master-data/materials/new">
            <Button size="sm">{t('materials.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}
