import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createPurchaseRequisition } from '@/api/procurement';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Purchase-requisition create form. Creates a DRAFT document (status is managed
 * server-side); business rules (unique number per company, referential
 * integrity) are enforced server-side and surfaced as the backend's 400.
 */
export function PurchaseRequisitionCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<Option[]>([]);
  const [company, setCompany] = useState('');
  const [number, setNumber] = useState('');
  const [needByDate, setNeedByDate] = useState('');
  const [notes, setNotes] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<Paginated<Option>>('/organization/companies/?page_size=100')
      .then((res) => {
        if (cancelled) return;
        setCompanies(res.results);
        if (res.results.length > 0) setCompany(res.results[0].id);
      })
      .catch(() => {
        /* Non-fatal: field stays empty and the user sees a validation error. */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createPurchaseRequisition({
        company,
        number,
        need_by_date: needByDate || null,
        notes,
      });
      navigate('/procurement/requisitions');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('procurement.requisitions.new')}</h1>
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

          <FormField label={t('procurement.fields.number')} required>
            {({ id }) => (
              <Input
                id={id}
                value={number}
                onChange={(e) => setNumber(e.target.value)}
                disabled={submitting}
                required
              />
            )}
          </FormField>

          <FormField label={t('procurement.fields.needBy')}>
            {({ id }) => (
              <Input
                id={id}
                type="date"
                value={needByDate}
                onChange={(e) => setNeedByDate(e.target.value)}
                disabled={submitting}
              />
            )}
          </FormField>

          <FormField label={t('procurement.fields.notes')}>
            {({ id }) => (
              <Input
                id={id}
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
              onClick={() => navigate('/procurement/requisitions')}
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
