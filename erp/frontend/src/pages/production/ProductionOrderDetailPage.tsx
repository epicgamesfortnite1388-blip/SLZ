import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import { fetchProductionOrder } from '@/api/production';
import { isApiError } from '@/api/types';
import { formatDateTime } from '@/i18n/dates';
import { AttachmentPanel } from '@/components/AttachmentPanel';
import { AuditHistoryPanel } from '@/components/AuditHistoryPanel';
import { RecordDetail, type DetailField } from '@/components/RecordDetail';
import { StatusBadge, Alert, Button, Spinner } from '@/components/ui';
import { useAuth } from '@/auth/AuthContext';
import { ProductionExecutionPanel } from './ProductionExecutionPanel';


/**
 * Read-only detail of one production order. The document is header-only by
 * design (Task 011): it pins WHAT to make and to WHICH frozen definition —
 * execution records are shown in the permission-gated traceability panel below.
 * What/how-much references and the audit history remain visible on the header.
 */
export function ProductionOrderDetailPage(): JSX.Element {
  const { t, i18n } = useTranslation();
  const { hasPermission } = useAuth();

  /** Locale-aware timestamp rendering (Jalali for fa). */
  const when = (iso: string | null): string => formatDateTime(iso, i18n.language);
  const { id = '' } = useParams();
  const [order, setOrder] = useState<Awaited<ReturnType<typeof fetchProductionOrder>> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setError(null);
    fetchProductionOrder(id)
      .then((o) => {
        if (active) setOrder(o);
      })
      .catch((err: unknown) => {
        if (active) setError(isApiError(err) ? err.message : t('common.error'));
      });
    return () => {
      active = false;
    };
  }, [id, t]);

  if (error) {
    return (
      <div className="stack">
        <Alert variant="danger" title={t('common.error')}>
          <p>{error}</p>
          <Button variant="secondary" size="sm" onClick={() => window.history.back()}>
            {t('common.back')}
          </Button>
        </Alert>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="table-state">
        <Spinner label={t('common.loading')} />
      </div>
    );
  }

  const fields: DetailField[] = [
    { labelKey: 'production.fields.number', value: order.number },
    { labelKey: 'production.fields.status', value: <StatusBadge status={order.status} label={t(`production.orderStatuses.${order.status}`)} /> },
    { labelKey: 'production.fields.customerProduct', value: order.customer_product },
    { labelKey: 'production.fields.specRevision', value: order.spec_revision },
    { labelKey: 'production.fields.bomRevision', value: order.bom_revision ?? '—' },
    { labelKey: 'production.fields.routingRevision', value: order.routing_revision ?? '—' },
    { labelKey: 'production.fields.salesOrderLine', value: order.sales_order_line ?? '—' },
    {
      labelKey: 'production.fields.plannedQuantity',
      value: `${order.planned_quantity} ${order.uom}`,
    },
    { labelKey: 'production.fields.scheduledStart', value: when(order.scheduled_start) },
    { labelKey: 'production.fields.scheduledEnd', value: when(order.scheduled_end) },
    { labelKey: 'production.fields.notes', value: order.notes || '—' },
  ];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('production.detail.title', { number: order.number })}</h1>
        <p className="page-header__subtitle">{t('production.detail.subtitle')}</p>
      </div>

      <RecordDetail title={t('production.detail.headerTitle')} fields={fields} />

      <ProductionExecutionPanel
        orderId={order.id}
        companyId={order.company}
        customerProductId={order.customer_product}
        uomId={order.uom}
      />

      <AuditHistoryPanel entityType="production.ProductionOrder" entityId={order.id} />

      {hasPermission('documents.attachment.view') && (
        <AttachmentPanel entityType="production.ProductionOrder" entityId={order.id} />
      )}

      <div className="form-actions">
        <Link to="/production/orders" className="link-back">
          ← {t('common.back')}
        </Link>
      </div>
    </div>
  );
}
