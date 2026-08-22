import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Alert, Button } from '@/components/ui';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import { useAsyncAction } from '@/hooks/useAsyncAction';
import {
  transitionToolingAsset,
  type ToolingAsset,
  type ToolingStatus,
} from '@/api/tooling';

type ToolingAction = 'retire' | 'reactivate';

/** Allowed transitions per status (display only; server is the authority). */
const TOOLING_ACTIONS: Record<ToolingStatus, ToolingAction[]> = {
  ACTIVE: ['retire'],
  RETIRED: ['reactivate'],
};

/**
 * Browse cliché / sheet / set tooling assets (SR-03) and drive their lifecycle.
 * Usage-life is shown as ``count / limit``; the row is flagged when the recorded
 * usage has reached the configured limit. The server enforces every transition.
 */
export function ToolingAssetsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<ToolingAsset>('/engineering/tooling-assets/');
  const action = useAsyncAction();

  const canManage = hasPermission('engineering.tooling.manage');

  const run = (id: string, toolingAction: ToolingAction): Promise<boolean> =>
    action.run(`${id}:${toolingAction}`, async () => {
      await transitionToolingAsset(id, toolingAction);
      collection.reload();
    });

  const columns: Column<ToolingAsset>[] = [
    { headerKey: 'tooling.fields.code', render: (r) => r.code },
    { headerKey: 'tooling.fields.name', render: (r) => r.name_fa },
    {
      headerKey: 'tooling.fields.type',
      render: (r) => t(`tooling.types.${r.tooling_type}`),
    },
    {
      headerKey: 'tooling.fields.status',
      render: (r) => t(`tooling.statuses.${r.status}`),
    },
    {
      headerKey: 'tooling.fields.usage',
      align: 'end',
      render: (r) => {
        const limit = r.usage_life_limit == null ? '∞' : r.usage_life_limit;
        const text = `${r.usage_count} / ${limit}`;
        return r.is_life_exceeded ? (
          <span className="text-danger">{text}</span>
        ) : (
          text
        );
      },
    },
    {
      headerKey: 'tooling.fields.actions',
      align: 'center',
      render: (r) => {
        const actions = canManage ? TOOLING_ACTIONS[r.status] : [];
        if (actions.length === 0) return '—';
        return (
          <div className="row-actions">
            {actions.map((a) => (
              <Button
                key={a}
                size="sm"
                variant={a === 'retire' ? 'secondary' : 'primary'}
                loading={action.busy === `${r.id}:${a}`}
                onClick={() => void run(r.id, a)}
              >
                {t(`tooling.actions.${a}`)}
              </Button>
            ))}
          </div>
        );
      },
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
        titleKey="tooling.title"
        subtitleKey="tooling.subtitle"
        columns={columns}
        rowKey={(r) => r.id}
        collection={collection}
        headerAction={
          canManage ? (
            <Link to="/engineering/tooling/new">
              <Button size="sm">{t('tooling.new')}</Button>
            </Link>
          ) : null
        }
      />
    </div>
  );
}
