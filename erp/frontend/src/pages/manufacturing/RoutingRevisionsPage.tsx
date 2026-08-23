import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { StatusBadge, Button } from '@/components/ui';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import { activateRoutingRevision, type StructureRevision } from '@/api/manufacturing';

/**
 * Browse Routing revisions and drive the activate transition (DRAFT → ACTIVE,
 * superseding the prior ACTIVE one atomically, server-side). Identical
 * lifecycle to BOM revisions — the same generic backend service powers both.
 */
export function RoutingRevisionsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<StructureRevision>('/manufacturing/routing-revisions/');
  const [activating, setActivating] = useState<string | null>(null);

  const canManage = hasPermission('manufacturing.routing.manage');

  const handleActivate = async (id: string): Promise<void> => {
    setActivating(id);
    try {
      await activateRoutingRevision(id);
      collection.reload();
    } finally {
      setActivating(null);
    }
  };

  const columns: Column<StructureRevision>[] = [
    {
      headerKey: 'manufacturing.fields.revisionNumber',
      render: (r) => `#${r.revision_number}`,
      align: 'center',
    },
    {
      headerKey: 'manufacturing.fields.status',
      render: (r) => <StatusBadge status={r.status} label={t(`manufacturing.statuses.${r.status}`)} />,
    },
    {
      headerKey: 'manufacturing.fields.effectiveFrom',
      render: (r) => r.effective_from ?? '—',
    },
    {
      headerKey: 'manufacturing.fields.actions',
      align: 'center',
      render: (r) =>
        canManage && r.status === 'DRAFT' ? (
          <Button
            size="sm"
            loading={activating === r.id}
            onClick={() => void handleActivate(r.id)}
          >
            {t('manufacturing.activate')}
          </Button>
        ) : (
          '—'
        ),
    },
  ];

  return (
    <CollectionView
      titleKey="manufacturing.routings.title"
      subtitleKey="manufacturing.routings.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
    />
  );
}
