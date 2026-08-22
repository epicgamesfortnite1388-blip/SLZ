import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { useAsyncAction } from '@/hooks/useAsyncAction';
import { Alert, Button } from '@/components/ui';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import {
  transitionProductionOrder,
  type ProductionOrder,
  type ProductionOrderStatus,
} from '@/api/production';

type OrderAction = 'release' | 'complete' | 'close' | 'cancel';

/** Allowed transitions per status (display only; server is the authority). The
 * lifecycle is intentionally minimal — execution states (issue/confirmation)
 * are gated on the traceability + stock layer (Q-046). */
const PO_ACTIONS: Record<ProductionOrderStatus, OrderAction[]> = {
  DRAFT: ['release', 'cancel'],
  RELEASED: ['complete', 'cancel'],
  COMPLETED: ['close', 'cancel'],
  CLOSED: [],
  CANCELLED: [],
};

/**
 * Browse production (work) orders and drive their status transitions. Action
 * buttons are shown contextually to a manager; the server enforces legality and
 * audits every change.
 */
export function ProductionOrdersPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const collection = useCollection<ProductionOrder>('/production/orders/');
  const asyncAct = useAsyncAction();

  const canManage = hasPermission('production.order.manage');

  const run = (id: string, act: OrderAction): Promise<boolean> =>
    asyncAct.run(`${id}:${act}`, async () => {
      await transitionProductionOrder(id, act);
      collection.reload()
    });

  const columns: Column<ProductionOrder>[] = [
    { headerKey: 'production.fields.number', render: (r) => r.number },
    {
      headerKey: 'production.fields.status',
      render: (r) => t(`production.orderStatuses.${r.status}`),
    },
    {
      headerKey: 'production.fields.quantity',
      align: 'end',
      render: (r) => r.planned_quantity,
    },
    {
      headerKey: 'production.fields.scheduledStart',
      render: (r) => r.scheduled_start ?? '—',
    },
    {
      headerKey: 'production.fields.actions',
      align: 'center',
      render: (r) => {
        const actions = canManage ? PO_ACTIONS[r.status] : [];
        if (actions.length === 0) return '—';
        return (
          <div className="row-actions">
            {actions.map((a) => (
              <Button
                key={a}
                size="sm"
                variant={a === 'cancel' ? 'secondary' : 'primary'}
                loading={asyncAct.busy === `${r.id}:${a}`}
                onClick={() => void run(r.id, a)}
              >
                {t(`production.actions.${a}`)}
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
        titleKey="production.orders.title"
        subtitleKey="production.orders.subtitle"
        columns={columns}
        rowKey={(r) => r.id}
        collection={collection}
        onRowClick={(r) => navigate('/production/orders/' + r.id)}
        headerAction={
        canManage ? (
          <Link to="/production/orders/new">
            <Button size="sm">{t('production.orders.new')}</Button>
          </Link>
        ) : null
      }
      />
    </div>
  );
}
