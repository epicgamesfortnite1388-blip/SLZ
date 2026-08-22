import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createProductionOrder } from '@/api/production';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}
interface SpecRow {
  id: string;
  root: string;
  revision_number: number;
  status: string;
}

/**
 * Production-order create form. Creates a DRAFT document (status is managed
 * server-side). It pins WHAT to make (``customer_product``), the FROZEN
 * engineering definition it is built to (``spec_revision``) and HOW MUCH
 * (``planned_quantity`` + ``uom``). Scheduled dates are plain, non-promised
 * fields (no ATP/capacity is computed — gated). BOM/routing revision, sales-line
 * provenance and site are optional and omitted from this minimal foundation form.
 */
export function ProductionOrderCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<Option[]>([]);
  const [products, setProducts] = useState<Option[]>([]);
  const [specs, setSpecs] = useState<Option[]>([]);
  const [uoms, setUoms] = useState<Option[]>([]);

  const [company, setCompany] = useState('');
  const [customerProduct, setCustomerProduct] = useState('');
  const [specRevision, setSpecRevision] = useState('');
  const [uom, setUom] = useState('');
  const [number, setNumber] = useState('');
  const [quantity, setQuantity] = useState('');
  const [scheduledStart, setScheduledStart] = useState('');
  const [scheduledEnd, setScheduledEnd] = useState('');
  const [notes, setNotes] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = <T,>(path: string): Promise<Paginated<T>> =>
      apiClient.get<Paginated<T>>(path);

    load<Option>('/organization/companies/?page_size=100')
      .then((res) => {
        if (cancelled) return;
        setCompanies(res.results);
        if (res.results.length > 0) setCompany(res.results[0].id);
      })
      .catch(() => {
        /* Non-fatal. */
      });

    load<Option>('/engineering/customer-products/?page_size=100')
      .then((res) => {
        if (!cancelled) setProducts(res.results);
      })
      .catch(() => {
        /* Non-fatal. */
      });

    load<Option>('/catalog/uoms/?page_size=100')
      .then((res) => {
        if (!cancelled) setUoms(res.results);
      })
      .catch(() => {
        /* Non-fatal. */
      });

    // Join spec revisions to their customer-product for a readable label.
    Promise.all([
      load<SpecRow>('/engineering/specifications/?page_size=100'),
      load<Option>('/engineering/customer-products/?page_size=100'),
    ])
      .then(([specRes, prodRes]) => {
        if (cancelled) return;
        const byId = new Map(prodRes.results.map((p) => [p.id, p]));
        setSpecs(
          specRes.results.map((s) => {
            const p = byId.get(s.root);
            return {
              id: s.id,
              code: `v${s.revision_number} · ${s.status}`,
              name_fa: p?.name_fa ?? s.root,
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
      await createProductionOrder({
        company,
        customer_product: customerProduct,
        spec_revision: specRevision,
        uom,
        number,
        planned_quantity: quantity,
        scheduled_start: scheduledStart || null,
        scheduled_end: scheduledEnd || null,
        notes,
      });
      navigate('/production/orders');
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
        <h1 className="page-header__title">{t('production.orders.new')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {select('masterData.fields.company', company, setCompany, companies, true)}
          {select(
            'production.fields.customerProduct',
            customerProduct,
            setCustomerProduct,
            products,
            true,
          )}
          {select(
            'production.fields.specRevision',
            specRevision,
            setSpecRevision,
            specs,
            true,
          )}

          <FormField label={t('production.fields.number')} required>
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

          <FormField label={t('production.fields.quantity')} required>
            {({ id }) => (
              <Input
                id={id}
                type="number"
                step="0.000001"
                min="0"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                disabled={submitting}
                required
              />
            )}
          </FormField>

          {select('production.fields.uom', uom, setUom, uoms, true)}

          <FormField label={t('production.fields.scheduledStart')}>
            {({ id }) => (
              <Input
                id={id}
                type="date"
                value={scheduledStart}
                onChange={(e) => setScheduledStart(e.target.value)}
                disabled={submitting}
              />
            )}
          </FormField>

          <FormField label={t('production.fields.scheduledEnd')}>
            {({ id }) => (
              <Input
                id={id}
                type="date"
                value={scheduledEnd}
                onChange={(e) => setScheduledEnd(e.target.value)}
                disabled={submitting}
              />
            )}
          </FormField>

          <FormField label={t('production.fields.notes')}>
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
              onClick={() => navigate('/production/orders')}
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
