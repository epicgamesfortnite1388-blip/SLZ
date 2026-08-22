import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createSalesOrder, type SalesOrder } from '@/api/sales';
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

/** One unpersisted line in the inline editor. */
interface DraftLine {
  /** Local-only key for React identity. */
  _key: number;
  customer_product: string;
  quantity: string;
  uom: string;
  unit_price: string;
  notes: string;
}

let _nextLineKey = 0;
function freshLine(): DraftLine {
  return { _key: ++_nextLineKey, customer_product: '', quantity: '', uom: '', unit_price: '', notes: '' };
}

export function SalesOrderCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<Option[]>([]);
  const [customers, setCustomers] = useState<Option[]>([]);
  const [products, setProducts] = useState<Option[]>([]);
  const [uoms, setUoms] = useState<Option[]>([]);

  const [company, setCompany] = useState('');
  const [customer, setCustomer] = useState('');
  const [number, setNumber] = useState('');
  const [currency, setCurrency] = useState('IRR');
  const [requestedDate, setRequestedDate] = useState('');
  const [notes, setNotes] = useState('');

  const [lines, setLines] = useState<DraftLine[]>([freshLine()]);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<Paginated<Option>>('/organization/companies/?page_size=200')
      .then((res) => { if (!cancelled) { setCompanies(res.results); if (res.results.length > 0) setCompany(res.results[0].id); } })
      .catch(() => {});

    Promise.all([
      apiClient.get<Paginated<CustomerRow>>('/partners/customers/?page_size=200'),
      apiClient.get<Paginated<PartnerRow>>('/partners/partners/?page_size=200'),
    ])
      .then(([custRes, partRes]) => {
        if (cancelled) return;
        const byId = new Map(partRes.results.map((p) => [p.id, p]));
        setCustomers(custRes.results.map((c) => {
          const p = byId.get(c.partner);
          return { id: c.id, code: p?.code ?? '', name_fa: p?.name_fa ?? c.partner };
        }));
      })
      .catch(() => {});

    apiClient.get<Paginated<Option>>('/engineering/customer-products/?page_size=200')
      .then((res) => { if (!cancelled) setProducts(res.results); })
      .catch(() => {});

    apiClient.get<Paginated<Option>>('/catalog/uoms/?page_size=200')
      .then((res) => { if (!cancelled) setUoms(res.results); })
      .catch(() => {});

    return () => { cancelled = true; };
  }, []);

  const setLine = (ix: number, patch: Partial<DraftLine>): void =>
    setLines((prev) => prev.map((l, i) => (i === ix ? { ...l, ...patch } : l)));

  const removeLine = (ix: number): void =>
    setLines((prev) => (prev.length <= 1 ? prev : prev.filter((_, i) => i !== ix)));

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const order: SalesOrder = await createSalesOrder({
        company,
        customer,
        number,
        currency,
        requested_date: requestedDate || null,
        notes,
      });

      const activeLines = lines.filter((l) => l.customer_product);
      for (let i = 0; i < activeLines.length; i++) {
        const l = activeLines[i];
        await apiClient.post('/sales/order-lines/', {
          order: order.id,
          sequence: i + 1,
          customer_product: l.customer_product,
          quantity: l.quantity,
          uom: l.uom,
          unit_price: l.unit_price || null,
          notes: l.notes,
        });
      }

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
    inline?: boolean,
  ): JSX.Element => (
    <FormField label={inline ? undefined : t(labelKey)} required={required}>
      {({ id }) => (
        <select
          id={id}
          className="input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={submitting}
          required={required}
          title={inline ? t(labelKey) : undefined}
        >
          <option value="">—</option>
          {options.map((o) => (
            <option key={o.id} value={o.id}>{o.name_fa}{o.code ? ` (${o.code})` : ''}</option>
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
          {error && <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>{error}</Alert>}

          {select('masterData.fields.company', company, setCompany, companies, true)}
          {select('sales.fields.customer', customer, setCustomer, customers, true)}

          <FormField label={t('sales.fields.number')} required>
            {({ id }) => <Input id={id} value={number} onChange={(e) => setNumber(e.target.value)} disabled={submitting} required />}
          </FormField>

          <FormField label={t('sales.fields.currency')} required>
            {({ id }) => <Input id={id} value={currency} onChange={(e) => setCurrency(e.target.value)} disabled={submitting} required />}
          </FormField>

          <FormField label={t('sales.fields.requested')}>
            {({ id }) => <Input id={id} type="date" value={requestedDate} onChange={(e) => setRequestedDate(e.target.value)} disabled={submitting} />}
          </FormField>

          <FormField label={t('sales.fields.notes')}>
            {({ id }) => <Input id={id} value={notes} onChange={(e) => setNotes(e.target.value)} disabled={submitting} />}
          </FormField>

          {/* ── Inline lines editor ── */}
          <Card title={t('sales.detail.linesTitle')}>
            {lines.map((line, ix) => (
              <div key={line._key} className="inline-line-row" style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
                <div style={{ minWidth: 180 }}>
                  {select('sales.fields.lineProduct', line.customer_product, (v) => setLine(ix, { customer_product: v }), products, true, true)}
                </div>
                <div style={{ width: 100 }}>
                  <FormField label={t('sales.fields.lineQuantity')} required>
                    {({ id }) => <Input id={id} type="number" step="any" min="0" value={line.quantity} onChange={(e) => setLine(ix, { quantity: e.target.value })} disabled={submitting} required />}
                  </FormField>
                </div>
                <div style={{ width: 120 }}>
                  {select('sales.fields.lineUom', line.uom, (v) => setLine(ix, { uom: v }), uoms, true, true)}
                </div>
                <div style={{ width: 110 }}>
                  <FormField label={t('sales.fields.lineUnitPrice')}>
                    {({ id }) => <Input id={id} type="number" step="any" min="0" value={line.unit_price} onChange={(e) => setLine(ix, { unit_price: e.target.value })} disabled={submitting} />}
                  </FormField>
                </div>
                <div style={{ width: 140 }}>
                  <FormField label={t('sales.fields.lineNotes')}>
                    {({ id }) => <Input id={id} value={line.notes} onChange={(e) => setLine(ix, { notes: e.target.value })} disabled={submitting} />}
                  </FormField>
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <Button type="button" variant="secondary" size="sm" onClick={() => removeLine(ix)} disabled={submitting || lines.length <= 1}>
                    ✕
                  </Button>
                </div>
              </div>
            ))}
            <Button type="button" variant="secondary" size="sm" onClick={() => setLines((prev) => [...prev, freshLine()])} disabled={submitting}>
              + {t('common.addLine')}
            </Button>
          </Card>

          <div className="form-actions">
            <Button type="submit" loading={submitting}>{t('masterData.save')}</Button>
            <Button type="button" variant="secondary" onClick={() => navigate('/sales/orders')} disabled={submitting}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}