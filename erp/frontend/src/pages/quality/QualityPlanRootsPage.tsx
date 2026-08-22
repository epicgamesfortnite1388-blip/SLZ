import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { QualityPlan } from '@/api/quality';

/**
 * Browse quality plan roots — the durable identity of a versioned inspection
 * plan, each bound to a specific specification revision. Content lives in the
 * immutable revisions; this page lets you browse and create roots.
 */
export function QualityPlanRootsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<QualityPlan>('/quality/plans/');
  const canManage = hasPermission('quality.plan.manage');

  const columns: Column<QualityPlan>[] = [
    { headerKey: 'manufacturing.fields.specRevision', render: (r) => r.spec_revision },
    {
      headerKey: 'manufacturing.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];

  return (
    <CollectionView
      titleKey="quality.planRoots.title"
      subtitleKey="quality.planRoots.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      onRowClick={undefined}
      headerAction={
        canManage ? (
          <Link to="/quality/plans/new">
            <Button size="sm">{t('quality.planRoots.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}