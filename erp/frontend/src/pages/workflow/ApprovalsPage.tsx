import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Alert, Button } from '@/components/ui';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import { useAsyncAction } from '@/hooks/useAsyncAction';
import { recordDecision, type WorkflowInstance } from '@/api/workflow';

/**
 * The signed-in user's personal approval inbox: workflow instances on which
 * they still have a pending step. Approving / rejecting is self-service (the
 * server only lets an assigned, still-pending approver act), so the page needs
 * authentication only — no module permission. An optional comment is captured
 * per row; the server records it against the step for audit.
 *
 * This is the generic engine's UI: it surfaces whatever workflows are
 * configured and routed to the user. It hard-codes no business approval rule.
 */
export function ApprovalsPage(): JSX.Element {
  const { t } = useTranslation();
  const collection = useCollection<WorkflowInstance>('/workflow/instances/mine/');
  const [comments, setComments] = useState<Record<string, string>>({});
  const action = useAsyncAction();

  const decide = (id: string, approve: boolean): Promise<boolean> =>
    action.run(`${id}:${approve ? 'approve' : 'reject'}`, async () => {
      await recordDecision(id, approve, comments[id] ?? '');
      setComments((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      collection.reload();
    });

  const columns: Column<WorkflowInstance>[] = [
    { headerKey: 'approvals.fields.workflow', render: (r) => r.definition },
    {
      headerKey: 'approvals.fields.target',
      render: (r) => `${r.entity_type} #${r.entity_id}`,
    },
    {
      headerKey: 'approvals.fields.state',
      render: (r) => t(`approvals.states.${r.state}`),
    },
    {
      headerKey: 'approvals.fields.comment',
      render: (r) => (
        <input
          type="text"
          className="input"
          value={comments[r.id] ?? ''}
          placeholder={t('approvals.fields.commentPlaceholder')}
          aria-label={t('approvals.fields.comment')}
          onChange={(e) =>
            setComments((prev) => ({ ...prev, [r.id]: e.target.value }))
          }
        />
      ),
    },
    {
      headerKey: 'approvals.fields.actions',
      align: 'center',
      render: (r) => (
        <div className="row-actions">
          <Button
            size="sm"
            variant="primary"
            loading={action.busy === `${r.id}:approve`}
            onClick={() => void decide(r.id, true)}
          >
            {t('approvals.actions.approve')}
          </Button>
          <Button
            size="sm"
            variant="secondary"
            loading={action.busy === `${r.id}:reject`}
            onClick={() => void decide(r.id, false)}
          >
            {t('approvals.actions.reject')}
          </Button>
        </div>
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
        titleKey="approvals.title"
        subtitleKey="approvals.subtitle"
        columns={columns}
        rowKey={(r) => r.id}
        collection={collection}
      />
    </div>
  );
}
