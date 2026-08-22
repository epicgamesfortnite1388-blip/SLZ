import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import {
  fetchPurchaseRequisition,
  fetchPurchaseRequisitionLines,
  type PurchaseRequisitionLine,
} from '@/api/procurement';
import { isApiError } from '@/api/types';
import { formatDateTime } from '@/i18n/dates';
import { AuditHistoryPanel } from '@/components/AuditHistoryPanel';
import { RecordDetail, type DetailField } from '@/components/RecordDetail';
import { Alert, Button, Card, Spinner } from '@/components/ui';


/** Read-only detail of one requisition: header, lines, audit history. */
export function PurchaseRequisitionDetailPage(): JSX.Element {
  const { t, i18n } = useTranslation();

  /** Locale-aware timestamp rendering (Jalali for fa). */
  const when = (iso: string | null): string => formatDateTime(iso, i18n.language);
  const { id = '' } = useParams();
  const [doc, setDoc] = useState<Awaited<ReturnType<typeof fetchPurchaseRequisition>> | null>(null);
  const [lines, setLines] = useState<PurchaseRequisitionLine[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setError(null);
    Promise.all([fetchPurchaseRequisition(id), fetchPurchaseRequisitionLines(id)])
      .then(([d, ls]) => {
        if (active) {
          setDoc(d);
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

  if (!doc) {
    return (
      <div className="table-state">
        <Spinner label={t('common.loading')} />
      </div>
    );
  }

  const fields: DetailField[] = [
    { labelKey: 'procurement.fields.number', value: doc.number },
    {
      labelKey: 'procurement.fields.status',
      value: t(`procurement.reqStatuses.${doc.status}`),
    },
    { labelKey: 'procurement.fields.requestedBy', value: doc.requested_by ?? '—' },
    { labelKey: 'procurement.fields.needBy', value: when(doc.need_by_date) },
    { labelKey: 'procurement.fields.notes', value: doc.notes || '—' },
  ];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('procurement.detail.title', { number: doc.number })}</h1>
        <p className="page-header__subtitle">{t('procurement.detail.subtitle')}</p>
      </div>

      <RecordDetail title={t('procurement.detail.headerTitle')} fields={fields} />

      <Card title={t('procurement.detail.linesTitle')}>
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
                  <th>{t('procurement.fields.lineSequence')}</th>
                  <th>{t('procurement.fields.lineMaterial')}</th>
                  <th>{t('procurement.fields.lineQuantity')}</th>
                  <th>{t('procurement.fields.lineUom')}</th>
                </tr>
              </thead>
              <tbody>
                {lines.map((line) => (
                  <tr key={line.id}>
                    <td>{line.sequence}</td>
                    <td>{line.material}</td>
                    <td>{line.quantity}</td>
                    <td>{line.uom}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <AuditHistoryPanel entityType="procurement.PurchaseRequisition" entityId={doc.id} />

      <div className="form-actions">
        <a className="link-back" onClick={() => window.history.back()} href="#back">
          ← {t('common.back')}
        </a>
      </div>
    </div>
  );
}
