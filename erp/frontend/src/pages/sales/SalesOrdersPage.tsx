import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { useAsyncAction } from '@/hooks/useAsyncAction';
import { Alert, Button, ConfirmButton, StatusBadge } from '@/components/ui';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import {
  transitionSalesOrder,
  type SalesOrder,
  type SalesOrderStatus,
} from '@/api/sales';

type OrderAction = 'confirm' | 'close' | 'cancel';

/** Allowed transitions per status (display only; server is the authority). The
 * lifecycle is intentionally minimal — fulfilment/shipment states are gated. */
const SO_ACTIONS: Record<SalesOrderStatus, OrderAction[]> = {
  DRAFT: ['confirm', 'cancel'],
  CONFIRMED: ['close', 'cancel'],
  CLOSED: [],
  CANCELLED: [],
};

/**
 * Browse sales orders and drive their status transitions. Action buttons are
 * shown contextually to a manager; the server enforces legality and audits every
 * change.
 */
export function SalesOrdersPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const collection = useCollection<SalesOrder>('/sales/orders/');
  const asyncAct = useAsyncAction();

  const canManage = hasPermission('sales.order.manage');

  const run = (id: string, act: OrderAction): Promise<boolean> =>
    asyncAct.run(`${id}:${act}`, async () => {
      await transitionSalesOrder(id, act);
      collection.reload()
    });

  const columns: Column<SalesOrder>[] = [
    { headerKey: 'sales.fields.number', render: (r) => r.number },
    {
      headerKey: 'sales.fields.status',
      render: (r) => <StatusBadge status={r.status} label={t(`sales.orderStatuses.${r.status}`)} />,
    },
    { headerKey: 'sales.fields.currency', render: (r) => r.currency },
    {
      headerKey: 'sales.fields.requested',
      render: (r) => r.requested_date ?? '—',
    },
    {
      headerKey: 'sales.fields.actions',
      align: 'center',
      render: (r) => {
        const actions = canManage ? SO_ACTIONS[r.status] : [];
        if (actions.length === 0) return '—';
        return (
          <div className="row-actions">
            {actions.map((a) => (
              a === 'cancel' ? (
                <ConfirmButton
                  key={a}
                  size="sm"
                  variant="secondary"
                  loading={asyncAct.busy === `${r.id}:${a}`}
                  confirmMessage={t('common.confirmAction')}
                  onConfirm={() => void run(r.id, a)}
                >
                  {t(`sales.actions.${a}`)}
                </ConfirmButton>
              ) : (
                <Button
                  key={a}
                  size="sm"
                  loading={asyncAct.busy === `${r.id}:${a}`}
                  onClick={() => void run(r.id, a)}
                >
                  {t(`sales.actions.${a}`)}
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
      {asyncAct.error && (
        <Alert variant="danger" title={t('common.error')}>
          <p>{asyncAct.error.message}</p>
          <Button variant="secondary" size="sm" onClick={asyncAct.clearError}>
            {t('common.close')}
          </Button>
        </Alert>
      )}
      <CollectionView
        titleKey="sales.orders.title"
        subtitleKey="sales.orders.subtitle"
        columns={columns}
        rowKey={(r) => r.id}
        collection={collection}
        onRowClick={(r) => navigate(`/sales/orders/${r.id}`)}
        headerAction={
        canManage ? (
          <Link to="/sales/orders/new">
            <Button size="sm">{t('sales.orders.new')}</Button>
          </Link>
        ) : null
      }
      />
    </div>
  );
}
