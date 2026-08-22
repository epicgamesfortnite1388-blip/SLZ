import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
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
  const [busy, setBusy] = useState<string | null>(null);

  const canManage = hasPermission('sales.order.manage');

  const run = async (id: string, action: OrderAction): Promise<void> => {
    setBusy(`${id}:${action}`);
    try {
      await transitionSalesOrder(id, action);
      collection.reload();
    } finally {
      setBusy(null);
    }
  };

  const columns: Column<SalesOrder>[] = [
    { headerKey: 'sales.fields.number', render: (r) => r.number },
    {
      headerKey: 'sales.fields.status',
      render: (r) => t(`sales.orderStatuses.${r.status}`),
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
              <Button
                key={a}
                size="sm"
                variant={a === 'cancel' ? 'secondary' : 'primary'}
                loading={busy === `${r.id}:${a}`}
                onClick={() => void run(r.id, a)}
              >
                {t(`sales.actions.${a}`)}
              </Button>
            ))}
          </div>
        );
      },
    },
  ];

  return (
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
  );
}
