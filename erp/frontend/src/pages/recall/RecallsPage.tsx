import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import type { Recall } from '@/api/recall';
import { Button, StatusBadge } from '@/components/ui';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';

/** Format an ISO datetime as a short date for list cells. */
const day = (iso: string | null): string => (iso ? iso.slice(0, 10) : '—');

/**
 * Browse recalls for the active company. Creating a recall never mutates
 * inventory or shipments — exposure is computed on demand on the detail page.
 */
export function RecallsPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const collection = useCollection<Recall>('/recall/recalls/');

  const columns: Column<Recall>[] = [
    { headerKey: 'recall.fields.code', render: (r) => r.code },
    {
      headerKey: 'recall.fields.status',
      render: (r) => <StatusBadge status={r.status} label={r.status_label} />,
    },
    {
      headerKey: 'recall.fields.severity',
      render: (r) => t(`recall.severities.${r.severity}`),
    },
    { headerKey: 'recall.fields.affectedUnits', render: (r) => r.affected_count, align: 'center' },
    { headerKey: 'recall.fields.initiatedAt', render: (r) => day(r.initiated_at) },
    { headerKey: 'recall.fields.reason', render: (r) => r.reason },
  ];

  return (
    <CollectionView
      titleKey="recall.recalls.title"
      subtitleKey="recall.recalls.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      onRowClick={(r) => navigate(`/recall/recalls/${r.id}`)}
      headerAction={
        hasPermission('recall.recall.manage') ? (
          <Link to="/recall/recalls/new">
            <Button size="sm">{t('recall.recalls.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}
