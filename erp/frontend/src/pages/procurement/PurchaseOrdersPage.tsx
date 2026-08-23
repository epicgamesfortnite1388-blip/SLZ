import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Alert, Button, ConfirmButton, StatusBadge } from '@/components/ui';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import { useAsyncAction } from '@/hooks/useAsyncAction';
import {
  transitionOrder,
  type PurchaseOrder,
  type PurchaseOrderStatus,
} from '@/api/procurement';

type OrderAction = 'approve' | 'send' | 'close' | 'cancel';

/** Allowed transitions per status (display only; server is the authority). The
 * lifecycle is truncated before goods receipt — receipt states are gated. */
const ORDER_ACTIONS: Record<PurchaseOrderStatus, OrderAction[]> = {
  DRAFT: ['approve', 'cancel'],
  APPROVED: ['send', 'cancel'],
  SENT: ['close', 'cancel'],
  CLOSED: [],
  CANCELLED: [],
};

/**
 * Browse purchase orders and drive their status transitions. Action buttons are
 * shown contextually to a manager; the server enforces legality and audits every
 * change. Failures surface inline instead of failing silently.
 */
export function PurchaseOrdersPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const collection = useCollection<PurchaseOrder>('/procurement/orders/');
  const action = useAsyncAction();

  const canManage = hasPermission('procurement.order.manage');

  const run = (id: string, orderAction: OrderAction): Promise<boolean> =>
    action.run(`${id}:${orderAction}`, async () => {
      await transitionOrder(id, orderAction);
      collection.reload();
    });

  const columns: Column<PurchaseOrder>[] = [
    { headerKey: 'procurement.fields.number', render: (r) => r.number },
    {
      headerKey: 'procurement.fields.status',
      render: (r) => <StatusBadge status={r.status} label={t(`procurement.orderStatuses.${r.status}`)} />,
    },
    { headerKey: 'procurement.fields.currency', render: (r) => r.currency },
    {
      headerKey: 'procurement.fields.expected',
      render: (r) => r.expected_date ?? '—',
    },
    {
      headerKey: 'procurement.fields.actions',
      align: 'center',
      render: (r) => {
        const actions = canManage ? ORDER_ACTIONS[r.status] : [];
        if (actions.length === 0) return '—';
        return (
          <div className="row-actions">
            {actions.map((a) => (
              a === 'cancel' ? (
                <ConfirmButton
                  key={a}
                  size="sm"
                  variant="secondary"
                  loading={action.busy === `${r.id}:${a}`}
                  confirmMessage={t('common.confirmAction')}
                  onConfirm={() => void run(r.id, a)}
                >
                  {t(`procurement.actions.${a}`)}
                </ConfirmButton>
              ) : (
                <Button
                  key={a}
                  size="sm"
                  loading={action.busy === `${r.id}:${a}`}
                  onClick={() => void run(r.id, a)}
                >
                  {t(`procurement.actions.${a}`)}
                </Button>
              )
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
        titleKey="procurement.orders.title"
        subtitleKey="procurement.orders.subtitle"
        columns={columns}
        rowKey={(r) => r.id}
        collection={collection}
        onRowClick={(r) => navigate('/procurement/orders/' + r.id)}
        headerAction={
          canManage ? (
            <Link to="/procurement/orders/new">
              <Button size="sm">{t('procurement.orders.new')}</Button>
            </Link>
          ) : null
        }
      />
    </div>
  );
}
