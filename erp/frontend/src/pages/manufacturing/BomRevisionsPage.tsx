import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import { activateBomRevision, type StructureRevision } from '@/api/manufacturing';

/**
 * Browse Bill-of-Materials revisions and drive the one lifecycle transition the
 * UI exposes: activating a DRAFT revision (the backend atomically supersedes the
 * prior ACTIVE one). All rules are server-side; the button shows only for DRAFT
 * rows to a manager.
 */
export function BomRevisionsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<StructureRevision>('/manufacturing/bom-revisions/');
  const [activating, setActivating] = useState<string | null>(null);

  const canManage = hasPermission('manufacturing.bom.manage');

  const handleActivate = async (id: string): Promise<void> => {
    setActivating(id);
    try {
      await activateBomRevision(id);
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
      render: (r) => t(`manufacturing.statuses.${r.status}`),
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
      titleKey="manufacturing.boms.title"
      subtitleKey="manufacturing.boms.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
    />
  );
}
