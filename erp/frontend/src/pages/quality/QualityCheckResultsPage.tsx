import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { apiClient } from '@/api/client';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner, StatusBadge } from '@/components/ui';
import type { Paginated } from '@/api/inventory';

interface QcResult {
  id: string;
  plan_item: string;
  traceability_unit: string;
  measured_value: string;
  disposition: string;
  checked_at: string;
  checked_by: string | null;
  notes: string;
  created_at: string;
}

export function QualityCheckResultsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canView = hasPermission('quality.results.view');
  const canManage = hasPermission('quality.results.manage');
  const [results, setResults] = useState<QcResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [planItem, setPlanItem] = useState('');
  const [unit, setUnit] = useState('');
  const [value, setValue] = useState('');
  const [disposition, setDisposition] = useState('PASS');
  const [checkedAt, setCheckedAt] = useState(new Date().toISOString().slice(0, 16));

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const page = await apiClient.get<Paginated<QcResult>>('/quality/check-results/?page_size=100');
      setResults(page.results);
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally { setLoading(false); }
  };

  useEffect(() => { if (canView) void load(); }, [canView]); // eslint-disable-line react-hooks/exhaustive-deps

  const postResult = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await apiClient.post<QcResult>('/quality/check-results/', {
        plan_item: planItem,
        traceability_unit: unit,
        measured_value: value,
        disposition,
        checked_at: new Date(checkedAt).toISOString(),
      });
      setValue('');
      await load();
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally { setBusy(false); }
  };

  if (!canView) return <></>;
  if (loading) {
    return (
      <div className="stack">
        <div className="page-header">
          <h1 className="page-header__title">{t('quality.checkResults.title')}</h1>
        </div>
        <Card><Spinner /></Card>
      </div>
    );
  }

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('quality.checkResults.title')}</h1>
      </div>

      <Card>
        {error && <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>{error}</Alert>}

        {canManage && (
          <form className="stack" onSubmit={(e) => void postResult(e)} style={{ marginBottom: 'var(--space-5)' }}>
            <h3>{t('quality.results.post')}</h3>
            <div className="form-grid">
              <FormField label={t('quality.fields.planItem')} required>
                {({ id }) => <Input id={id} value={planItem} onChange={(e) => setPlanItem(e.target.value)} required disabled={busy} placeholder="UUID" />}
              </FormField>
              <FormField label={t('quality.fields.unit')} required>
                {({ id }) => <Input id={id} value={unit} onChange={(e) => setUnit(e.target.value)} required disabled={busy} placeholder="UUID" />}
              </FormField>
              <FormField label={t('quality.fields.value')} required>
                {({ id }) => <Input id={id} value={value} onChange={(e) => setValue(e.target.value)} required disabled={busy} />}
              </FormField>
              <FormField label={t('quality.fields.disposition')} required>
                {({ id }) => (
                  <select className="input" id={id} value={disposition} onChange={(e) => setDisposition(e.target.value)} required disabled={busy}>
                    <option value="PASS">{t('quality.datatypes.BOOL')} PASS</option>
                    <option value="FAIL">FAIL</option>
                    <option value="HOLD">HOLD</option>
                  </select>
                )}
              </FormField>
              <FormField label={t('quality.fields.checkedAt')} required>
                {({ id }) => <Input id={id} type="datetime-local" value={checkedAt} onChange={(e) => setCheckedAt(e.target.value)} required disabled={busy} />}
              </FormField>
            </div>
            <Button type="submit" loading={busy}>{t('masterData.save')}</Button>
          </form>
        )}

        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('quality.fields.unit')}</th>
                <th>{t('quality.fields.value')}</th>
                <th>{t('quality.fields.disposition')}</th>
                <th>{t('quality.fields.checkedAt')}</th>
              </tr>
            </thead>
            <tbody>
              {results.length === 0 ? (
                <tr><td colSpan={4}>{t('masterData.empty')}</td></tr>
              ) : results.map((r) => (
                <tr key={r.id}>
                  <td>{r.traceability_unit}</td>
                  <td>{r.measured_value}</td>
                  <td><StatusBadge status={r.disposition} /></td>
                  <td>{r.checked_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}