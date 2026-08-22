import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Card, Spinner } from '@/components/ui';
import { fetchCount, fetchStatusSummary, type StatusSummary } from '@/api/dashboard';
import type { PermissionCode } from '@/api/types';

/** One live-count tile: which endpoint to count, and where the tile links. */
interface StatDef {
  key: string;
  labelKey: string;
  path: string;
  permission: PermissionCode;
  to: string;
}

/**
 * The tiles a user *could* see. Each is gated by the same view permission as its
 * module, so the dashboard never counts data the user cannot browse. Counts come
 * from the modules' real list endpoints — nothing is fabricated.
 */
const STAT_DEFS: StatDef[] = [
  { key: 'partners', labelKey: 'dashboard.stats.partners', path: '/partners/partners/', permission: 'partners.partner.view', to: '/master-data/partners' },
  { key: 'products', labelKey: 'dashboard.stats.products', path: '/catalog/products/', permission: 'catalog.product.view', to: '/master-data/products' },
  { key: 'materials', labelKey: 'dashboard.stats.materials', path: '/catalog/materials/', permission: 'catalog.material.view', to: '/master-data/materials' },
  { key: 'customerProducts', labelKey: 'dashboard.stats.customerProducts', path: '/engineering/customer-products/', permission: 'engineering.customerproduct.view', to: '/engineering/customer-products' },
  { key: 'salesOrders', labelKey: 'dashboard.stats.salesOrders', path: '/sales/orders/', permission: 'sales.order.view', to: '/sales/orders' },
  { key: 'purchaseOrders', labelKey: 'dashboard.stats.purchaseOrders', path: '/procurement/orders/', permission: 'procurement.order.view', to: '/procurement/orders' },
  { key: 'productionOrders', labelKey: 'dashboard.stats.productionOrders', path: '/production/orders/', permission: 'production.order.view', to: '/production/orders' },
  { key: 'warehouses', labelKey: 'dashboard.stats.warehouses', path: '/inventory/warehouses/', permission: 'inventory.warehouse.view', to: '/inventory/warehouses' },
];

/** One order-book row: which document collection to summarize, and its i18n
 * status-label prefix (e.g. `sales.orderStatuses.CONFIRMED`). */
interface OrderBookDef {
  key: string;
  labelKey: string;
  path: string;
  statusKeyPrefix: string;
  permission: PermissionCode;
  to: string;
}

const ORDER_BOOK_DEFS: OrderBookDef[] = [
  {
    key: 'sales',
    labelKey: 'dashboard.orderBook.salesOrders',
    path: '/sales/orders/',
    statusKeyPrefix: 'sales.orderStatuses',
    permission: 'sales.order.view',
    to: '/sales/orders',
  },
  {
    key: 'purchase',
    labelKey: 'dashboard.orderBook.purchaseOrders',
    path: '/procurement/orders/',
    statusKeyPrefix: 'procurement.orderStatuses',
    permission: 'procurement.order.view',
    to: '/procurement/orders',
  },
  {
    key: 'production',
    labelKey: 'dashboard.orderBook.productionOrders',
    path: '/production/orders/',
    statusKeyPrefix: 'production.orderStatuses',
    permission: 'production.order.view',
    to: '/production/orders',
  },
];

/**
 * One live-count tile that fetches its own count and links to the module.
 */
function StatCard({ def }: { def: StatDef }): JSX.Element {
  const { t } = useTranslation();
  const [count, setCount] = useState<number | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    fetchCount(def.path)
      .then((n) => {
        if (active) setCount(n);
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
    };
  }, [def.path]);

  return (
    <Link to={def.to} className="stat-card-link">
      <Card>
        <div className="stat-card__label">{t(def.labelKey)}</div>
        <div className="stat-card__value">
          {failed ? t('dashboard.stats.error') : count === null ? <Spinner size="sm" inline /> : count}
        </div>
      </Card>
    </Link>
  );
}

/**
 * One order-book row: total + per-status chips for a document collection.
 * Only non-zero statuses render chips; an all-zero collection shows the
 * empty note. Counts come from the server-side `summary/` endpoint.
 */
function OrderBookRow({ def }: { def: OrderBookDef }): JSX.Element {
  const { t } = useTranslation();
  const [summary, setSummary] = useState<StatusSummary | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    fetchStatusSummary(def.path)
      .then((s) => {
        if (active) setSummary(s);
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
    };
  }, [def.path]);

  const entries = Object.entries(summary?.by_status ?? {});
  const nonZero = entries.filter(([, n]) => n > 0);

  return (
    <div className="order-book__row">
      <Link to={def.to} className="order-book__label link-inline">
        {t(def.labelKey)}
      </Link>
      <span className="order-book__total">
        {failed ? t('dashboard.stats.error') : summary === null ? <Spinner size="sm" inline /> : summary.total}
      </span>
      <span className="order-book__chips">
        {!failed &&
          summary !== null &&
          (nonZero.length === 0 ? (
            <span className="stat-card__note">{t('dashboard.orderBook.empty')}</span>
          ) : (
            nonZero.map(([status, n]) => (
              <span key={status} className="order-book__chip">
                {t(`${def.statusKeyPrefix}.${status}`)}: {n}
              </span>
            ))
          ))}
      </span>
    </div>
  );
}

/**
 * Home dashboard: live record counts for every module the signed-in user has
 * view access to, plus the order book (per-status document breakdowns). If the
 * user can see nothing, an empty-state note is shown instead of fabricated
 * tiles. No metric is fabricated — every number comes from a real endpoint.
 */
export function DashboardPage(): JSX.Element {
  const { t } = useTranslation();
  const { user, hasPermission } = useAuth();

  const welcome = user?.full_name
    ? t('dashboard.welcome', { name: user.full_name })
    : t('dashboard.welcomeGeneric');

  const visible = STAT_DEFS.filter((def) => hasPermission(def.permission));
  const bookVisible = ORDER_BOOK_DEFS.filter((def) => hasPermission(def.permission));

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('dashboard.title')}</h1>
        <p className="page-header__subtitle">{welcome}</p>
      </div>

      {visible.length === 0 ? (
        <Card>
          <div className="stat-card__note">{t('dashboard.stats.noAccess')}</div>
        </Card>
      ) : (
        <div className="stat-grid">
          {visible.map((def) => (
            <StatCard key={def.key} def={def} />
          ))}
        </div>
      )}

      {bookVisible.length > 0 && (
        <Card title={t('dashboard.orderBook.title')}>
          <div className="order-book">
            {bookVisible.map((def) => (
              <OrderBookRow key={def.key} def={def} />
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
