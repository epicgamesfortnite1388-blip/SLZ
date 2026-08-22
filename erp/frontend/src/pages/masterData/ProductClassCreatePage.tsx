import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createProductClass } from '@/api/masterData';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

export function ProductClassCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [types, setTypes] = useState<Option[]>([]);
  const [productType, setProductType] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient.get<Paginated<Option>>('/catalog/product-types/?page_size=200')
      .then((res) => { if (!cancelled) { setTypes(res.results); if (res.results.length > 0) setProductType(res.results[0].id); } })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createProductClass({ product_type: productType, code, name_fa: nameFa, name_en: nameEn });
      navigate('/master-data/product-classes');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header"><h1 className="page-header__title">{t('productClasses.new')}</h1></div>
      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>{error}</Alert>}
          <FormField label={t('productTypes.title')} required>
            {({ id }) => (
              <select id={id} className="input" value={productType} onChange={(e) => setProductType(e.target.value)} disabled={submitting} required>
                {types.map((o) => (<option key={o.id} value={o.id}>{o.name_fa} ({o.code})</option>))}
              </select>
            )}
          </FormField>
          <FormField label={t('masterData.fields.code')} required>
            {({ id }) => <Input id={id} value={code} onChange={(e) => setCode(e.target.value)} disabled={submitting} required />}
          </FormField>
          <FormField label={t('masterData.fields.nameFa')} required>
            {({ id }) => <Input id={id} value={nameFa} onChange={(e) => setNameFa(e.target.value)} disabled={submitting} required />}
          </FormField>
          <FormField label={t('masterData.fields.nameEn')}>
            {({ id }) => <Input id={id} value={nameEn} onChange={(e) => setNameEn(e.target.value)} disabled={submitting} />}
          </FormField>
          <div className="form-actions">
            <Button type="submit" loading={submitting}>{t('masterData.save')}</Button>
            <Button type="button" variant="secondary" onClick={() => navigate('/master-data/product-classes')} disabled={submitting}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}