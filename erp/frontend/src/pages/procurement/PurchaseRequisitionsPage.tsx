import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { useAsyncAction } from '@/hooks/useAsyncAction';
import { Alert, Button } from '@/components/ui';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import {
  transitionRequisition,
  type PurchaseRequisition,
  type PurchaseRequisitionStatus,
} from '@/api/procurement';

type ReqAction = 'submit' | 'approve' | 'reject' | 'cancel';

/** Allowed transitions per status (mirrors the server state machine for display
 * only — the backend is the authority and rejects anything illegal with 409). */
const REQ_ACTIONS: Record<PurchaseRequisitionStatus, ReqAction[]> = {
  DRAFT: ['submit', 'cancel'],
  SUBMITTED: ['approve', 'reject', 'cancel'],
  APPROVED: ['cancel'],
  REJECTED: [],
  CANCELLED: [],
};

/**
 * Browse purchase requisitions and drive their status transitions. Action
 * buttons are shown contextually (per the current status) to a manager; the
 * server enforces legality and audits every change.
 */
export function PurchaseRequisitionsPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const collection = useCollection<PurchaseRequisition>(
    '/procurement/requisitions/',
  );
  const asyncAct = useAsyncAction();

  const canManage = hasPermission('procurement.requisition.manage');

  const run = (id: string, act: ReqAction): Promise<boolean> =>
    asyncAct.run(`${id}:${act}`, async () => {
      await transitionRequisition(id, act);
      collection.reload()
    });

  const columns: Column<PurchaseRequisition>[] = [
    { headerKey: 'procurement.fields.number', render: (r) => r.number },
    {
      headerKey: 'procurement.fields.status',
      render: (r) => t(`procurement.reqStatuses.${r.status}`),
    },
    {
      headerKey: 'procurement.fields.needBy',
      render: (r) => r.need_by_date ?? '—',
    },
    {
      headerKey: 'procurement.fields.actions',
      align: 'center',
      render: (r) => {
        const actions = canManage ? REQ_ACTIONS[r.status] : [];
        if (actions.length === 0) return '—';
        return (
          <div className="row-actions">
            {actions.map((a) => (
              <Button
                key={a}
                size="sm"
                variant={a === 'cancel' || a === 'reject' ? 'secondary' : 'primary'}
                loading={asyncAct.busy === `${r.id}:${a}`}
                onClick={() => void run(r.id, a)}
              >
                {t(`procurement.actions.${a}`)}
              </Button>
            ))}
          </div>
        );
      },
    },
  ];

  return (
    <div className="stack">
      {asyncAct.error && (
        <Alert variant="danger" title={t('common.error')}>
          <p>{asyncAct.error.message}</p>
          <Button variant="secondary" size="sm" onClick={asyncAct.clearError}>
            {t('common.close')}
          </Button>
        </Alert>
      )}
      <CollectionView
        titleKey="procurement.requisitions.title"
        subtitleKey="procurement.requisitions.subtitle"
        columns={columns}
        rowKey={(r) => r.id}
        collection={collection}
        onRowClick={(r) => navigate('/procurement/requisitions/' + r.id)}
        headerAction={
        canManage ? (
          <Link to="/procurement/requisitions/new">
            <Button size="sm">{t('procurement.requisitions.new')}</Button>
          </Link>
        ) : null
      }
      />
    </div>
  );
}
