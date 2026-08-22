import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createPurchaseOrder } from '@/api/procurement';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}
interface SupplierRow {
  id: string;
  partner: string;
}
interface PartnerRow {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Purchase-order create form. Creates a DRAFT document (status is managed
 * server-side). The supplier list joins ``partners.Supplier`` rows to their
 * partner identity for a friendly label; ``currency`` is a plain code (no FX).
 */
export function PurchaseOrderCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<Option[]>([]);
  const [suppliers, setSuppliers] = useState<Option[]>([]);

  const [company, setCompany] = useState('');
  const [supplier, setSupplier] = useState('');
  const [number, setNumber] = useState('');
  const [currency, setCurrency] = useState('IRR');
  const [expectedDate, setExpectedDate] = useState('');
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

    // Join supplier profiles to their partner identity for readable labels.
    Promise.all([
      apiClient.get<Paginated<SupplierRow>>('/partners/suppliers/?page_size=100'),
      apiClient.get<Paginated<PartnerRow>>('/partners/partners/?page_size=100'),
    ])
      .then(([supRes, partRes]) => {
        if (cancelled) return;
        const byId = new Map(partRes.results.map((p) => [p.id, p]));
        setSuppliers(
          supRes.results.map((s) => {
            const p = byId.get(s.partner);
            return {
              id: s.id,
              code: p?.code ?? '',
              name_fa: p?.name_fa ?? s.partner,
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
      await createPurchaseOrder({
        company,
        supplier,
        number,
        currency,
        expected_date: expectedDate || null,
        notes,
      });
      navigate('/procurement/orders');
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
        <h1 className="page-header__title">{t('procurement.orders.new')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {select('masterData.fields.company', company, setCompany, companies, true)}
          {select('procurement.fields.supplier', supplier, setSupplier, suppliers, true)}

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

          <FormField label={t('procurement.fields.currency')} required>
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

          <FormField label={t('procurement.fields.expected')}>
            {({ id }) => (
              <Input
                id={id}
                type="date"
                value={expectedDate}
                onChange={(e) => setExpectedDate(e.target.value)}
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
              onClick={() => navigate('/procurement/orders')}
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
