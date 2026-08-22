import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createProductFamily } from '@/api/masterData';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

export function ProductFamilyCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [classes, setClasses] = useState<Option[]>([]);
  const [productClass, setProductClass] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient.get<Paginated<Option>>('/catalog/product-classes/?page_size=200')
      .then((res) => { if (!cancelled) { setClasses(res.results); if (res.results.length > 0) setProductClass(res.results[0].id); } })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createProductFamily({ product_class: productClass, code, name_fa: nameFa, name_en: nameEn });
      navigate('/master-data/product-families');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header"><h1 className="page-header__title">{t('productFamilies.new')}</h1></div>
      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>{error}</Alert>}
          <FormField label={t('productClasses.title')} required>
            {({ id }) => (
              <select id={id} className="input" value={productClass} onChange={(e) => setProductClass(e.target.value)} disabled={submitting} required>
                {classes.map((o) => (<option key={o.id} value={o.id}>{o.name_fa} ({o.code})</option>))}
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
            <Button type="button" variant="secondary" onClick={() => navigate('/master-data/product-families')} disabled={submitting}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}