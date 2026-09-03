import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import { apiClient } from '@/api/client';
import type { Paginated } from '@/api/masterData';
import {
  addAffectedUnit,
  fetchRecall,
  fetchRecallAffectedUnits,
  fetchRecallExposure,
  transitionRecall,
  type AffectedUnit,
  type Exposure,
  type Recall,
  type RecallStatus,
} from '@/api/recall';
import { isApiError } from '@/api/types';
import { useAuth } from '@/auth/AuthContext';
import { Alert, Button, Card, FormField, Input, Spinner, StatusBadge } from '@/components/ui';

/** Which statuses may be reached from each state (backend enforces the same). */
const NEXT: Partial<Record<RecallStatus, RecallStatus[]>> = {
  DRAFT: ['OPEN', 'CANCELLED'],
  OPEN: ['INVESTIGATING', 'ACTION_REQUIRED', 'CLOSED', 'CANCELLED'],
  INVESTIGATING: ['ACTION_REQUIRED', 'OPEN', 'CLOSED'],
  ACTION_REQUIRED: ['CLOSED', 'INVESTIGATING', 'OPEN'],
};

interface UnitOption {
  id: string;
  identifier: string;
  unit_type: string;
}

const day = (iso: string | null): string => (iso ? iso.slice(0, 10) : '—');

/**
 * Recall detail: record facts, the audited status transition controls, the
 * user-curated affected traceability units, and the on-demand exposure
 * computation (genealogy -> production orders -> shipments/customers).
 * Exposure is read-only: creating/computing a recall never mutates stock.
 */
export function RecallDetailPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const { id = '' } = useParams();

  const [recall, setRecall] = useState<Recall | null>(null);
  const [units, setUnits] = useState<AffectedUnit[]>([]);
  const [unitOptions, setUnitOptions] = useState<UnitOption[]>([]);
  const [selectedUnit, setSelectedUnit] = useState('');
  const [unitNote, setUnitNote] = useState('');
  const [exposure, setExposure] = useState<Exposure | null>(null);
  const [exposureLoading, setExposureLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const canManage = hasPermission('recall.recall.manage');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [r, affected, opts] = await Promise.all([
        fetchRecall(id),
        fetchRecallAffectedUnits(id),
        apiClient.get<Paginated<UnitOption>>('/inventory/traceability-units/?page_size=200'),
      ]);
      setRecall(r);
      setUnits(affected.results);
      setUnitOptions(opts.results);
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setLoading(false);
    }
  }, [id, t]);

  useEffect(() => {
    void load();
  }, [load]);

  const transition = async (to: RecallStatus): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const updated = await transitionRecall(id, to);
      setRecall(updated);
      setNotice(t('recall.transitions.done', { status: to }));
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setBusy(false);
    }
  };

  const addUnit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    if (!selectedUnit) return;
    setBusy(true);
    setError(null);
    try {
      await addAffectedUnit({ recall: id, traceability_unit: selectedUnit, note: unitNote });
      setSelectedUnit('');
      setUnitNote('');
      const affected = await fetchRecallAffectedUnits(id);
      setUnits(affected.results);
      const r = await fetchRecall(id);
      setRecall(r);
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setBusy(false);
    }
  };

  const computeExposure = async (): Promise<void> => {
    setExposureLoading(true);
    setError(null);
    try {
      setExposure(await fetchRecallExposure(id));
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setExposureLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="stack">
        <div className="page-header">
          <h1 className="page-header__title">{t('recall.recalls.detail')}</h1>
        </div>
        <Card>
          <Spinner label={t('common.loading')} />
        </Card>
      </div>
    );
  }

  if (!recall) {
    return (
      <div className="stack">
        <div className="page-header">
          <h1 className="page-header__title">{t('recall.recalls.detail')}</h1>
        </div>
        <Card>
          {error && <Alert variant="danger" title={t('common.error')}>{error}</Alert>}
        </Card>
      </div>
    );
  }

  const nextStates = NEXT[recall.status] ?? [];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">
          {recall.code} <StatusBadge status={recall.status} label={recall.status_label} />
        </h1>
        <p className="page-header__subtitle">
          {t('recall.fields.severity')}: {t(`recall.severities.${recall.severity}`)} ·{' '}
          {t('recall.fields.initiatedAt')}: {day(recall.initiated_at)}
        </p>
        <p>
          <Link to="/recall/recalls">{t('common.back')}</Link>
        </p>
      </div>

      {notice && (
        <Alert variant="success" onClose={() => setNotice(null)}>
          {notice}
        </Alert>
      )}
      {error && (
        <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Card title={t('recall.fields.reason')}>
        <p>{recall.reason}</p>
        {recall.notes && <p>{recall.notes}</p>}
        {canManage && nextStates.length > 0 && (
          <div className="form-actions" style={{ marginTop: 'var(--space-4)' }}>
            {nextStates.map((st) => (
              <Button
                key={st}
                size="sm"
                variant={st === 'CLOSED' ? 'secondary' : st === 'CANCELLED' ? 'danger' : 'primary'}
                loading={busy}
                onClick={() => void transition(st)}
              >
                {t(`recall.transitions.to.${st}`)}
              </Button>
            ))}
          </div>
        )}
      </Card>

      <Card title={t('recall.fields.affectedUnits')}>
        {canManage && (
          <form className="stack" onSubmit={(e) => void addUnit(e)}>
            <div className="field-row">
              <FormField label={t('recall.fields.traceabilityUnit')} required>
                {({ id }) => (
                  <select
                    id={id}
                    className="input"
                    value={selectedUnit}
                    onChange={(e) => setSelectedUnit(e.target.value)}
                    disabled={busy}
                    required
                  >
                    <option value="">—</option>
                    {unitOptions.map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.identifier} ({o.unit_type})
                      </option>
                    ))}
                  </select>
                )}
              </FormField>
              <FormField label={t('recall.fields.note')}>
                {({ id }) => (
                  <Input
                    id={id}
                    value={unitNote}
                    onChange={(e) => setUnitNote(e.target.value)}
                    disabled={busy}
                  />
                )}
              </FormField>
              <Button type="submit" size="sm" loading={busy}>
                {t('recall.recalls.addUnit')}
              </Button>
            </div>
          </form>
        )}
        {units.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state__title">{t('recall.recalls.noUnits')}</div>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('recall.fields.traceabilityUnit')}</th>
                  <th>{t('recall.fields.unitType')}</th>
                  <th>{t('recall.fields.note')}</th>
                </tr>
              </thead>
              <tbody>
                {units.map((u) => (
                  <tr key={u.id}>
                    <td>{u.unit_identifier}</td>
                    <td>{u.unit_type}</td>
                    <td>{u.note || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card title={t('recall.exposure.title')}>
        <p>{t('recall.exposure.subtitle')}</p>
        <div className="form-actions" style={{ marginTop: 'var(--space-3)' }}>
          <Button size="sm" variant="secondary" loading={exposureLoading} onClick={() => void computeExposure()}>
            {t('recall.exposure.compute')}
          </Button>
        </div>
        {exposure && (
          <div className="stack" style={{ marginTop: 'var(--space-4)' }}>
            <p>
              {t('recall.exposure.seedUnits')}: <strong>{exposure.seed_units}</strong> ·{' '}
              {t('recall.exposure.upstream')}: <strong>{exposure.upstream_units}</strong> ·{' '}
              {t('recall.exposure.downstream')}: <strong>{exposure.downstream_units}</strong> ·{' '}
              {t('recall.exposure.productionOrders')}: <strong>{exposure.production_orders.length}</strong> ·{' '}
              {t('recall.exposure.shipments')}: <strong>{exposure.shipments.length}</strong> ·{' '}
              {t('recall.exposure.customers')}: <strong>{exposure.customers.length}</strong>
            </p>
            {exposure.customers.length > 0 && (
              <div>
                <strong>{t('recall.exposure.customers')}:</strong>{' '}
                {exposure.customers.map((c) => c.name_fa).join('، ')}
              </div>
            )}
            {exposure.shipments.length > 0 && (
              <div>
                <strong>{t('recall.exposure.shipments')}:</strong>{' '}
                {exposure.shipments.map((s) => s.number).join(', ')}
              </div>
            )}
            {exposure.production_orders.length > 0 && (
              <div>
                <strong>{t('recall.exposure.productionOrders')}:</strong>{' '}
                {exposure.production_orders.map((o) => o.number).join(', ')}
              </div>
            )}
            {exposure.affected_units.length > 0 && (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>{t('recall.fields.traceabilityUnit')}</th>
                      <th>{t('recall.fields.unitType')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {exposure.affected_units.map((u) => (
                      <tr key={u.id}>
                        <td>{u.identifier}</td>
                        <td>{u.unit_type}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
