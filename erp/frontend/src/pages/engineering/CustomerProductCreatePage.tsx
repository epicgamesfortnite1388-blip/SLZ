import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createCustomerProduct } from '@/api/engineering';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Customer-product create form — the representative write flow for Task 005.
 * Exercises the full audited service path (POST → domain event → audit). All
 * business rules (unique code per company, referential integrity) are enforced
 * server-side; the UI surfaces the backend's 400 message rather than
 * duplicating the rules on the client.
 */
export function CustomerProductCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<Option[]>([]);
  const [customers, setCustomers] = useState<Option[]>([]);
  const [groups, setGroups] = useState<Option[]>([]);
  const [families, setFamilies] = useState<Option[]>([]);
  const [uoms, setUoms] = useState<Option[]>([]);

  const [company, setCompany] = useState('');
  const [customer, setCustomer] = useState('');
  const [productGroup, setProductGroup] = useState('');
  const [family, setFamily] = useState('');
  const [baseUom, setBaseUom] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = <T extends Option>(
      path: string,
      set: (v: T[]) => void,
      pick?: (first: T) => void,
    ): void => {
      apiClient
        .get<Paginated<T>>(`${path}?page_size=100`)
        .then((res) => {
          if (cancelled) return;
          set(res.results);
          if (pick && res.results.length > 0) pick(res.results[0]);
        })
        .catch(() => {
          /* Non-fatal: the field stays empty and the user sees a validation error. */
        });
    };
    load<Option>('/organization/companies/', setCompanies, (f) => setCompany(f.id));
    load<Option>('/partners/partners/', setCustomers);
    load<Option>('/catalog/product-groups/', setGroups);
    load<Option>('/catalog/product-families/', setFamilies);
    load<Option>('/catalog/uoms/', setUoms, (f) => setBaseUom(f.id));
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createCustomerProduct({
        company,
        customer,
        code,
        name_fa: nameFa,
        name_en: nameEn,
        product_group: productGroup || null,
        family: family || null,
        base_uom: baseUom,
      });
      navigate('/engineering/customer-products');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  const selectField = (
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
              {o.name_fa} ({o.code})
            </option>
          ))}
        </select>
      )}
    </FormField>
  );

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('engineering.customerProducts.new')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {selectField('masterData.fields.company', company, setCompany, companies, true)}
          {selectField('engineering.fields.customer', customer, setCustomer, customers, true)}

          <FormField label={t('masterData.fields.code')} required>
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

          <FormField label={t('masterData.fields.nameFa')} required>
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

          {selectField('engineering.fields.productGroup', productGroup, setProductGroup, groups, false)}
          {selectField('engineering.fields.family', family, setFamily, families, false)}
          {selectField('masterData.fields.baseUom', baseUom, setBaseUom, uoms, true)}

          <div className="form-actions">
            <Button type="submit" loading={submitting}>
              {t('masterData.save')}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/engineering/customer-products')}
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
