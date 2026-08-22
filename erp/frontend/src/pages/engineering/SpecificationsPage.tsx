import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { useAsyncAction } from '@/hooks/useAsyncAction';
import { Alert, Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import { activateSpecification, type SpecificationRevision } from '@/api/engineering';

/**
 * Browse specification revisions. Read-oriented, but exposes the one
 * lifecycle transition the UI drives: activating a DRAFT revision (which the
 * backend atomically supersedes the prior ACTIVE one for). All rules are
 * server-side; the button is only shown for DRAFT rows to a manager.
 */
export function SpecificationsPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const collection = useCollection<SpecificationRevision>('/engineering/specifications/');
  const action = useAsyncAction();

  const canManage = hasPermission('engineering.specification.manage');

  const handleActivate = (id: string): Promise<boolean> =>
    action.run(`activate:${id}`, async () => {
      await activateSpecification(id);
      collection.reload()
    });

  const columns: Column<SpecificationRevision>[] = [
    { headerKey: 'engineering.fields.revisionNumber', render: (r) => `#${r.revision_number}`, align: 'center' },
    { headerKey: 'engineering.fields.status', render: (r) => t(`engineering.statuses.${r.status}`) },
    { headerKey: 'engineering.fields.specFormat', render: (r) => r.spec_format || '—' },
    { headerKey: 'engineering.fields.colors', render: (r) => r.number_of_colors, align: 'center' },
    {
      headerKey: 'engineering.fields.lamination',
      render: (r) => <BoolCell value={r.has_lamination} />,
      align: 'center',
    },
    {
      headerKey: 'engineering.fields.actions',
      align: 'center',
      render: (r) =>
        canManage && r.status === 'DRAFT' ? (
          <Button
            size="sm"
            loading={action.busy === `activate:${r.id}`}
            onClick={() => void handleActivate(r.id)}
          >
            {t('engineering.activate')}
          </Button>
        ) : (
          '—'
        ),
    },
  ];

  return (
    <div className="stack">
      {action.error && (
        <Alert variant="danger" title={t('common.error')}>
          <p>{action.error.message}</p>
          <Button variant="secondary" size="sm" onClick={action.clearError}>
            {t('common.close')}
          </Button>
        </Alert>
      )}
      <CollectionView
        titleKey="engineering.specifications.title"
        subtitleKey="engineering.specifications.subtitle"
        columns={columns}
        rowKey={(r) => r.id}
        collection={collection}
        onRowClick={(r) => navigate(`/engineering/customer-products/${r.root}`)}
      />
    </div>
  );
}
