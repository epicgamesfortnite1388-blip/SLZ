import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import { fetchSalesOrder, fetchSalesOrderLines, type SalesOrderLine } from '@/api/sales';
import { isApiError } from '@/api/types';
import { formatDateTime } from '@/i18n/dates';
import { AttachmentPanel } from '@/components/AttachmentPanel';
import { AuditHistoryPanel } from '@/components/AuditHistoryPanel';
import { RecordDetail, type DetailField } from '@/components/RecordDetail';
import { Alert, Button, Card, Spinner } from '@/components/ui';
import { useAuth } from '@/auth/AuthContext';

/** Locale-neutral timestamp trim (matches the audit viewer). */

/**
 * Read-only detail of one sales order: header summary, its lines, and the
 * record's audit history. Status transitions stay on the list page; this view
 * is the "what exactly is this document" surface. All data comes from the
 * existing `sales.order.view`-gated endpoints — nothing is fabricated.
 */
export function SalesOrderDetailPage(): JSX.Element {
  const { t, i18n } = useTranslation();
  const { hasPermission } = useAuth();

  /** Locale-aware timestamp rendering (Jalali for fa). */
  const when = (iso: string | null): string => formatDateTime(iso, i18n.language);
  const { id = '' } = useParams();
  const [order, setOrder] = useState<Awaited<ReturnType<typeof fetchSalesOrder>> | null>(null);
  const [lines, setLines] = useState<SalesOrderLine[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setError(null);
    Promise.all([fetchSalesOrder(id), fetchSalesOrderLines(id)])
      .then(([o, ls]) => {
        if (active) {
          setOrder(o);
          setLines(ls);
        }
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
    { labelKey: 'sales.fields.number', value: order.number },
    { labelKey: 'sales.fields.status', value: t(`sales.orderStatuses.${order.status}`) },
    { labelKey: 'sales.fields.currency', value: order.currency },
    { labelKey: 'sales.fields.customer', value: order.customer },
    { labelKey: 'sales.fields.orderDate', value: when(order.order_date) },
    { labelKey: 'sales.fields.requestedDate', value: when(order.requested_date) },
    { labelKey: 'sales.fields.notes', value: order.notes || '—' },
  ];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">
          {t('sales.detail.title', { number: order.number })}
        </h1>
        <p className="page-header__subtitle">{t('sales.detail.subtitle')}</p>
      </div>

      <RecordDetail title={t('sales.detail.headerTitle')} fields={fields} />

      <Card title={t('sales.detail.linesTitle')}>
        {!lines && (
          <div className="table-state">
            <Spinner label={t('common.loading')} />
          </div>
        )}
        {lines && lines.length === 0 && <p>{t('masterData.empty')}</p>}
        {lines && lines.length > 0 && (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('sales.fields.lineSequence')}</th>
                  <th>{t('sales.fields.lineProduct')}</th>
                  <th>{t('sales.fields.lineQuantity')}</th>
                  <th>{t('sales.fields.lineUom')}</th>
                  <th>{t('sales.fields.lineUnitPrice')}</th>
                </tr>
              </thead>
              <tbody>
                {lines.map((line) => (
                  <tr key={line.id}>
                    <td>{line.sequence}</td>
                    <td>{line.customer_product}</td>
                    <td>{line.quantity}</td>
                    <td>{line.uom}</td>
                    <td>{line.unit_price ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <AuditHistoryPanel entityType="sales.SalesOrder" entityId={order.id} />

      {hasPermission('documents.attachment.view') && (
        <AttachmentPanel entityType="sales.SalesOrder" entityId={order.id} />
      )}

      <div className="form-actions">
        <Link to="/sales/orders" className="link-back">
          ← {t('common.back')}
        </Link>
      </div>
    </div>
  );
}
