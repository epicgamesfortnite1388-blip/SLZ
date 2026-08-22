import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import {
  activateQualityPlanRevision,
  type QualityPlanRevision,
} from '@/api/quality';

/**
 * Browse Quality-Plan revisions and drive the one lifecycle transition the UI
 * exposes: activating a DRAFT revision (the backend atomically supersedes the
 * prior ACTIVE one). All rules are server-side; the button shows only for DRAFT
 * rows to a user with the manage permission.
 */
export function QualityPlanRevisionsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<QualityPlanRevision>(
    '/quality/plan-revisions/',
  );
  const [activating, setActivating] = useState<string | null>(null);

  const canManage = hasPermission('quality.plan.manage');

  const handleActivate = async (id: string): Promise<void> => {
    setActivating(id);
    try {
      await activateQualityPlanRevision(id);
      collection.reload();
    } finally {
      setActivating(null);
    }
  };

  const columns: Column<QualityPlanRevision>[] = [
    {
      headerKey: 'quality.fields.revisionNumber',
      render: (r) => `#${r.revision_number}`,
      align: 'center',
    },
    {
      headerKey: 'quality.fields.status',
      render: (r) => t(`quality.statuses.${r.status}`),
    },
    {
      headerKey: 'quality.fields.effectiveFrom',
      render: (r) => r.effective_from ?? '—',
    },
    {
      headerKey: 'quality.fields.actions',
      align: 'center',
      render: (r) =>
        canManage && r.status === 'DRAFT' ? (
          <Button
            size="sm"
            loading={activating === r.id}
            onClick={() => void handleActivate(r.id)}
          >
            {t('quality.activate')}
          </Button>
        ) : (
          '—'
        ),
    },
  ];

  return (
    <CollectionView
      titleKey="quality.plans.title"
      subtitleKey="quality.plans.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
    />
  );
}
