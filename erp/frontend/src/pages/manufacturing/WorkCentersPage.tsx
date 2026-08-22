import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { WorkCenter } from '@/api/manufacturing';

const columns: Column<WorkCenter>[] = [
  { headerKey: 'masterData.fields.code', render: (r) => r.code },
  { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
  { headerKey: 'masterData.fields.nameEn', render: (r) => r.name_en || '—' },
  {
    headerKey: 'manufacturing.fields.sequenceHint',
    render: (r) => r.sequence_hint,
    align: 'center',
  },
  {
    headerKey: 'masterData.fields.active',
    render: (r) => <BoolCell value={r.is_active} />,
    align: 'center',
  },
];

/** Browse work centers (production stages that group machines). */
export function WorkCentersPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const collection = useCollection<WorkCenter>('/manufacturing/work-centers/');

  return (
    <CollectionView
      titleKey="manufacturing.workCenters.title"
      subtitleKey="manufacturing.workCenters.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      onRowClick={(r) => navigate(`/manufacturing/work-centers/${r.id}`)}
      headerAction={
        hasPermission('manufacturing.workcenter.manage') ? (
          <Link to="/manufacturing/work-centers/new">
            <Button size="sm">{t('manufacturing.workCenters.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}
