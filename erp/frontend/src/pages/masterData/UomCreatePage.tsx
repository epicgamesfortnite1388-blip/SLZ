import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { createUom } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

/** UoM dimensions (mirrors ``Dimension`` choices). */
const DIMENSIONS = ['MASS', 'LENGTH', 'AREA', 'VOLUME', 'COUNT', 'TIME'] as const;

/**
 * Unit of measure create form — lightweight reference data (no audit trail).
 */
export function UomCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [dimension, setDimension] = useState('COUNT');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createUom({ code, name_fa: nameFa, name_en: nameEn, dimension });
      navigate('/master-data/uoms');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('uoms.new')}</h1>
      </div>
      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

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

          <FormField label={t('uoms.dimension')} required>
            {({ id }) => (
              <select
                id={id}
                className="input"
                value={dimension}
                onChange={(e) => setDimension(e.target.value)}
                disabled={submitting}
                required
              >
                {DIMENSIONS.map((d) => (
                  <option key={d} value={d}>
                    {t(`uoms.dimensions.${d}`)}
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <div className="form-actions">
            <Button type="submit" loading={submitting}>{t('masterData.save')}</Button>
            <Button type="button" variant="secondary" onClick={() => navigate('/master-data/uoms')} disabled={submitting}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}