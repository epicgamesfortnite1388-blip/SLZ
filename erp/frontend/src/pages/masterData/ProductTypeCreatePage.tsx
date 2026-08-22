import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { createProductType } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

export function ProductTypeCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createProductType({ code, name_fa: nameFa, name_en: nameEn });
      navigate('/master-data/product-types');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header"><h1 className="page-header__title">{t('productTypes.new')}</h1></div>
      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>{error}</Alert>}
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
            <Button type="button" variant="secondary" onClick={() => navigate('/master-data/product-types')} disabled={submitting}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}