import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createSalesOrder } from '@/api/sales';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}
interface CustomerRow {
  id: string;
  partner: string;
}
interface PartnerRow {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Sales-order create form. Creates a DRAFT document (status is managed
 * server-side). The customer list joins ``partners.Customer`` rows to their
 * partner identity for a friendly label; ``requested_date`` records only what the
 * customer asked for (NOT a promised/ATP date); ``currency`` is a plain code.
 */
export function SalesOrderCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<Option[]>([]);
  const [customers, setCustomers] = useState<Option[]>([]);

  const [company, setCompany] = useState('');
  const [customer, setCustomer] = useState('');
  const [number, setNumber] = useState('');
  const [currency, setCurrency] = useState('IRR');
  const [requestedDate, setRequestedDate] = useState('');
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
        /* Non-fatal. */
      });

    // Join customer profiles to their partner identity for readable labels.
    Promise.all([
      apiClient.get<Paginated<CustomerRow>>('/partners/customers/?page_size=100'),
      apiClient.get<Paginated<PartnerRow>>('/partners/partners/?page_size=100'),
    ])
      .then(([custRes, partRes]) => {
        if (cancelled) return;
        const byId = new Map(partRes.results.map((p) => [p.id, p]));
        setCustomers(
          custRes.results.map((c) => {
            const p = byId.get(c.partner);
            return {
              id: c.id,
              code: p?.code ?? '',
              name_fa: p?.name_fa ?? c.partner,
            };
          }),
        );
      })
      .catch(() => {
        /* Non-fatal. */
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
      await createSalesOrder({
        company,
        customer,
        number,
        currency,
        requested_date: requestedDate || null,
        notes,
      });
      navigate('/sales/orders');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  const select = (
    labelKey: string,
    value: string,
    onChange: (v: string) => void,
    options: Option[],
    required: boolean,
  ): JSX.Element => (
    <FormField label={t(labelKey)} required={required}>
      {({ id }) => (
        <select
          id={id}
          className="input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={submitting}
          required={required}
        >
          <option value="">—</option>
          {options.map((o) => (
            <option key={o.id} value={o.id}>
              {o.name_fa}
              {o.code ? ` (${o.code})` : ''}
            </option>
          ))}
        </select>
      )}
    </FormField>
  );

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('sales.orders.new')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {select('masterData.fields.company', company, setCompany, companies, true)}
          {select('sales.fields.customer', customer, setCustomer, customers, true)}

          <FormField label={t('sales.fields.number')} required>
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

          <FormField label={t('sales.fields.currency')} required>
            {({ id }) => (
              <Input
                id={id}
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                disabled={submitting}
                required
              />
            )}
          </FormField>

          <FormField label={t('sales.fields.requested')}>
            {({ id }) => (
              <Input
                id={id}
                type="date"
                value={requestedDate}
                onChange={(e) => setRequestedDate(e.target.value)}
                disabled={submitting}
              />
            )}
          </FormField>

          <FormField label={t('sales.fields.notes')}>
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
              onClick={() => navigate('/sales/orders')}
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
