import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createProduct } from '@/api/masterData';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Product create form — company-wide finished-goods identity with a
 * multi-level taxonomy (group/type/class/family) and base unit of measure.
 */
export function ProductCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<Option[]>([]);
  const [families, setFamilies] = useState<Option[]>([]);
  const [uoms, setUoms] = useState<Option[]>([]);

  const [company, setCompany] = useState('');
  const [family, setFamily] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [baseUom, setBaseUom] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient.get<Paginated<Option>>('/organization/companies/?page_size=200')
      .then((res) => { if (!cancelled) { setCompanies(res.results); if (res.results.length > 0) setCompany(res.results[0].id); } })
      .catch(() => {});
    apiClient.get<Paginated<Option>>('/catalog/product-families/?page_size=200')
      .then((res) => { if (!cancelled) setFamilies(res.results); })
      .catch(() => {});
    apiClient.get<Paginated<Option>>('/catalog/uoms/?page_size=200')
      .then((res) => { if (!cancelled) setUoms(res.results); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createProduct({
        company,
        family: family || undefined,
        code,
        name_fa: nameFa,
        name_en: nameEn,
        base_uom: baseUom || undefined,
      });
      navigate('/master-data/products');
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
        <h1 className="page-header__title">{t('products.new')}</h1>
      </div>
      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {selectField('masterData.fields.company', company, setCompany, companies, true)}
          {selectField('engineering.fields.family', family, setFamily, families, false)}

          <FormField label={t('masterData.fields.code')} required>
            {({ id }) => (
              <Input id={id} value={code} onChange={(e) => setCode(e.target.value)} disabled={submitting} required />
            )}
          </FormField>

          <FormField label={t('masterData.fields.nameFa')} required>
            {({ id }) => (
              <Input id={id} value={nameFa} onChange={(e) => setNameFa(e.target.value)} disabled={submitting} required />
            )}
          </FormField>

          <FormField label={t('masterData.fields.nameEn')}>
            {({ id }) => (
              <Input id={id} value={nameEn} onChange={(e) => setNameEn(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          {selectField('masterData.fields.baseUom', baseUom, setBaseUom, uoms, false)}

          <div className="form-actions">
            <Button type="submit" loading={submitting}>{t('masterData.save')}</Button>
            <Button type="button" variant="secondary" onClick={() => navigate('/master-data/products')} disabled={submitting}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}