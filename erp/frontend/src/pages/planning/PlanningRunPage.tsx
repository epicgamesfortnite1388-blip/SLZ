import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { runPlanning, type PlanningRow } from '@/api/planning';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, Spinner, StatusBadge } from '@/components/ui';

/**
 * Read-only planning run: projects on-hand + open supply against demand for
 * every active reorder policy and suggests replenishment. Suggestions are
 * advisory — the purchase/manufacture order workflows are the only writers.
 */
export function PlanningRunPage(): JSX.Element {
  const { t } = useTranslation();
  const [rows, setRows] = useState<PlanningRow[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const run = await runPlanning();
      setRows(run.rows);
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
      setRows(null);
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    void load();
  }, [load]);

  const actionBadge = (r: PlanningRow): JSX.Element => {
    if (r.action === 'NONE') return <StatusBadge status="CLOSED" label={t('planning.actions.NONE')} />;
    if (r.action === 'PURCHASE') return <StatusBadge status="SUBMITTED" label={t('planning.actions.PURCHASE')} variant="warning" />;
    return <StatusBadge status="RELEASED" label={t('planning.actions.MANUFACTURE')} variant="info" />;
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('planning.run.title')}</h1>
        <p className="page-header__subtitle">{t('planning.run.subtitle')}</p>
      </div>

      <Card>
        <div className="table-toolbar">
          <span>
            {rows !== null && (
              <>
                {t('planning.summary.actionRequired')}: {rows.filter((r) => r.action !== 'NONE').length}
                {' · '}
                {t('planning.summary.totalPolicies')}: {rows.length}
              </>
            )}
          </span>
          <div className="table-toolbar__actions">
            <Button size="sm" variant="secondary" onClick={() => void load()} loading={loading}>
              {t('common.retry')}
            </Button>
          </div>
        </div>

        {loading && (
          <div className="table-state">
            <Spinner label={t('common.loading')} />
          </div>
        )}

        {!loading && error && (
          <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {!loading && !error && rows && rows.length === 0 && (
          <div className="empty-state">
            <div className="empty-state__title">{t('planning.run.empty')}</div>
          </div>
        )}

        {!loading && !error && rows && rows.length > 0 && (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('masterData.fields.code')}</th>
                  <th>{t('masterData.fields.nameFa')}</th>
                  <th>{t('planning.fields.itemType')}</th>
                  <th>{t('planning.fields.onHand')}</th>
                  <th>{t('planning.fields.incoming')}</th>
                  <th>{t('planning.fields.openProduction')}</th>
                  <th>{t('planning.fields.allocated')}</th>
                  <th>{t('planning.fields.openDemand')}</th>
                  <th>{t('planning.fields.projected')}</th>
                  <th>{t('planning.fields.reorderPoint')}</th>
                  <th>{t('planning.fields.suggestedQty')}</th>
                  <th>{t('planning.fields.suggestedAction')}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={`${r.policy_id}-${r.item_code}`}>
                    <td>{r.item_code}</td>
                    <td>{r.item_name_fa}</td>
                    <td>{t(`planning.itemTypes.${r.item_type}`)}</td>
                    <td>{r.on_hand}</td>
                    <td>{r.incoming_purchase}</td>
                    <td>{r.open_production}</td>
                    <td>{r.allocated}</td>
                    <td>{r.open_demand}</td>
                    <td><strong>{r.projected}</strong></td>
                    <td>{r.reorder_point}</td>
                    <td>{r.action !== 'NONE' ? r.suggested_qty : '—'}</td>
                    <td>{actionBadge(r)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
