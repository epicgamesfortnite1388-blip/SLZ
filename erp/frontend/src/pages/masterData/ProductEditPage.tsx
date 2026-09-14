import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '@/api/client';
import {
  updateProduct,
  type Paginated,
  type Product,
} from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Product edit form — replicates the PartnerEditPage PATCH flow for the
 * catalog Product master. `code` stays fixed (business numbers are immutable
 * identities); taxonomy and naming are editable and audited server-side.
 */
export function ProductEditPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [companies, setCompanies] = useState<Option[]>([]);
  const [groups, setGroups] = useState<Option[]>([]);
  const [families, setFamilies] = useState<Option[]>([]);
  const [uoms, setUoms] = useState<Option[]>([]);

  const [company, setCompany] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [productGroup, setProductGroup] = useState('');
  const [family, setFamily] = useState('');
  const [baseUom, setBaseUom] = useState('');
  const [isActive, setIsActive] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiClient.get<Product>(`/catalog/products/${id}/`),
      apiClient.get<Paginated<Option>>('/organization/companies/?page_size=200'),
      apiClient.get<Paginated<Option>>('/catalog/product-groups/?page_size=200'),
      apiClient.get<Paginated<Option>>('/catalog/product-families/?page_size=200'),
      apiClient.get<Paginated<Option>>('/catalog/uoms/?page_size=200'),
    ])
      .then(([product, co, gr, fa, uo]) => {
        if (cancelled) return;
        setCode(product.code);
        setNameFa(product.name_fa);
        setNameEn(product.name_en);
        setCompany(product.company);
        setProductGroup(product.product_group ?? '');
        setFamily(product.family ?? '');
        setBaseUom(product.base_uom ?? '');
        setIsActive(product.is_active);
        setCompanies(co.results);
        setGroups(gr.results);
        setFamilies(fa.results);
        setUoms(uo.results);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setLoadError(isApiError(err) ? err.message : t('common.error'));
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id, t]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await updateProduct(id, {
        company,
        name_fa: nameFa,
        name_en: nameEn,
        product_group: productGroup || null,
        family: family || null,
        base_uom: baseUom || undefined,
        is_active: isActive,
      });
      navigate(`/master-data/products/${id}`);
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
      {({ id: fieldId }) => (
        <select
          id={fieldId}
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

  if (loading) {
    return (
      <div className="table-state">
        <Spinner label={t('common.loading')} />
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="stack">
        <Alert variant="danger" title={t('common.error')}>
          <p>{loadError}</p>
          <Button variant="secondary" size="sm" onClick={() => window.history.back()}>
            {t('common.back')}
          </Button>
        </Alert>
      </div>
    );
  }

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('products.edit')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {selectField('masterData.fields.company', company, setCompany, companies, true)}

          <FormField label={t('masterData.fields.code')}>
            {({ id: fieldId }) => <Input id={fieldId} value={code} disabled readOnly />}
          </FormField>

          <FormField label={t('masterData.fields.nameFa')} required>
            {({ id: fieldId }) => (
              <Input
                id={fieldId}
                value={nameFa}
                onChange={(e) => setNameFa(e.target.value)}
                disabled={submitting}
                required
              />
            )}
          </FormField>

          <FormField label={t('masterData.fields.nameEn')}>
            {({ id: fieldId }) => (
              <Input
                id={fieldId}
                value={nameEn}
                onChange={(e) => setNameEn(e.target.value)}
                disabled={submitting}
              />
            )}
          </FormField>

          {selectField('productGroups.title', productGroup, setProductGroup, groups, false)}
          {selectField('productFamilies.title', family, setFamily, families, false)}
          {selectField('masterData.fields.baseUom', baseUom, setBaseUom, uoms, false)}

          <label className="checkbox">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              disabled={submitting}
            />
            {t('masterData.fields.active')}
          </label>

          <div className="form-actions">
            <Button type="submit" loading={submitting}>
              {t('masterData.save')}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate(`/master-data/products/${id}`)}
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
