import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createToolingAsset, type ToolingType } from '@/api/tooling';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}
interface WarehouseRow extends Option {
  store_type: string;
}

const TOOLING_TYPES: ToolingType[] = ['CLICHE', 'SHEET', 'SET'];

/**
 * Tooling-asset create form (SR-03). Creates an ACTIVE cliché / sheet / set with
 * its optional usage-life limit and its dedicated cliché-store location. All
 * integrity rules (unique code per company, cliché-store type, company/customer
 * consistency of the linked product) are enforced server-side; the UI surfaces
 * the backend 400 rather than duplicating the rules. No cost fields exist (OPEN).
 */
export function ToolingAssetCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<Option[]>([]);
  const [customers, setCustomers] = useState<Option[]>([]);
  const [products, setProducts] = useState<Option[]>([]);
  const [warehouses, setWarehouses] = useState<WarehouseRow[]>([]);

  const [company, setCompany] = useState('');
  const [customer, setCustomer] = useState('');
  const [customerProduct, setCustomerProduct] = useState('');
  const [toolingType, setToolingType] = useState<ToolingType>('CLICHE');
  const [warehouse, setWarehouse] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [usageLimit, setUsageLimit] = useState('');
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
      .catch(() => {});
    load<Option>('/partners/partners/?page_size=100')
      .then((res) => !cancelled && setCustomers(res.results))
      .catch(() => {});
    load<Option>('/engineering/customer-products/?page_size=100')
      .then((res) => !cancelled && setProducts(res.results))
      .catch(() => {});
    // Only cliché stores are valid locations (server also enforces this).
    load<WarehouseRow>('/inventory/warehouses/?page_size=100&store_type=CLICHE')
      .then((res) => !cancelled && setWarehouses(res.results))
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
      await createToolingAsset({
        company,
        customer,
        customer_product: customerProduct || null,
        tooling_type: toolingType,
        warehouse: warehouse || null,
        code,
        name_fa: nameFa,
        name_en: nameEn,
        usage_life_limit: usageLimit ? Number(usageLimit) : null,
        notes,
      });
      navigate('/engineering/tooling');
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
        <h1 className="page-header__title">{t('tooling.new')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {select('masterData.fields.company', company, setCompany, companies, true)}
          {select('tooling.fields.customer', customer, setCustomer, customers, true)}
          {select(
            'tooling.fields.customerProduct',
            customerProduct,
            setCustomerProduct,
            products,
            false,
          )}

          <FormField label={t('tooling.fields.type')} required>
            {({ id }) => (
              <select
                id={id}
                className="input"
                value={toolingType}
                onChange={(e) => setToolingType(e.target.value as ToolingType)}
                disabled={submitting}
                required
              >
                {TOOLING_TYPES.map((tp) => (
                  <option key={tp} value={tp}>
                    {t(`tooling.types.${tp}`)}
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('tooling.fields.code')} required>
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

          <FormField label={t('tooling.fields.name')} required>
            {({ id }) => (
              <Input
                id={id}
                value={nameFa}
                onChange={(e) => setNameFa(e.target.value)}
                disabled={submitting}
                required
              />
            )}
          </FormField>

          <FormField label={t('masterData.fields.nameEn')}>
            {({ id }) => (
              <Input
                id={id}
                value={nameEn}
                onChange={(e) => setNameEn(e.target.value)}
                disabled={submitting}
              />
            )}
          </FormField>

          <FormField label={t('tooling.fields.usageLifeLimit')}>
            {({ id }) => (
              <Input
                id={id}
                type="number"
                min="0"
                step="1"
                value={usageLimit}
                onChange={(e) => setUsageLimit(e.target.value)}
                disabled={submitting}
              />
            )}
          </FormField>

          {select('tooling.fields.warehouse', warehouse, setWarehouse, warehouses, false)}

          <FormField label={t('tooling.fields.notes')}>
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
              onClick={() => navigate('/engineering/tooling')}
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
