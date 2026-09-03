import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import type { Paginated } from '@/api/masterData';
import { createRecall, type RecallSeverity } from '@/api/recall';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface IdName {
  id: string;
  code: string;
  name_fa: string;
}

const SEVERITIES: RecallSeverity[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

/**
 * Create a DRAFT recall. The record is a pure quality-event declaration — it
 * never mutates stock or shipments; affected inventory/customers are computed
 * later from genealogy via the detail page's exposure view.
 */
export function RecallCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<IdName[]>([]);
  const [company, setCompany] = useState('');
  const [code, setCode] = useState('');
  const [reason, setReason] = useState('');
  const [severity, setSeverity] = useState<RecallSeverity>('MEDIUM');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<Paginated<IdName>>('/organization/companies/?page_size=200')
      .then((res) => {
        if (cancelled) return;
        setCompanies(res.results);
        if (res.results.length > 0) setCompany(res.results[0].id);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createRecall({ company, code, reason, severity, notes });
      navigate('/recall/recalls');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('recall.recalls.new')}</h1>
      </div>
      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <FormField label={t('masterData.fields.company')} required>
            {({ id }) => (
              <select
                id={id}
                className="input"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                disabled={submitting}
                required
              >
                <option value="">—</option>
                {companies.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name_fa} ({o.code})
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('recall.fields.code')} required>
            {({ id }) => (
              <Input
                id={id}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                disabled={submitting}
                required
              />
            )}
          </FormField>

          <FormField label={t('recall.fields.reason')} required>
            {({ id }) => (
              <textarea
                id={id}
                className="input"
                rows={3}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                disabled={submitting}
                required
              />
            )}
          </FormField>

          <FormField label={t('recall.fields.severity')} required>
            {({ id }) => (
              <select
                id={id}
                className="input"
                value={severity}
                onChange={(e) => setSeverity(e.target.value as RecallSeverity)}
                disabled={submitting}
                required
              >
                {SEVERITIES.map((s) => (
                  <option key={s} value={s}>
                    {t(`recall.severities.${s}`)}
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('recall.fields.notes')}>
            {({ id }) => (
              <textarea
                id={id}
                className="input"
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                disabled={submitting}
              />
            )}
          </FormField>

          <div className="form-actions">
            <Button type="submit" loading={submitting}>
              {t('masterData.save')}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/recall/recalls')}
              disabled={submitting}
            >
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
