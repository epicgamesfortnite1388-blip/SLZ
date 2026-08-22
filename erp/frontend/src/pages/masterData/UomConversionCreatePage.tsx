import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createUomConversion } from '@/api/masterData';
import type { Paginated, UnitOfMeasure } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

export function UomConversionCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [uoms, setUoms] = useState<UnitOfMeasure[]>([]);
  const [fromUom, setFromUom] = useState('');
  const [toUom, setToUom] = useState('');
  const [factor, setFactor] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient.get<Paginated<UnitOfMeasure>>('/catalog/uoms/?page_size=200')
      .then((res) => { if (!cancelled) setUoms(res.results); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createUomConversion({ from_uom: fromUom, to_uom: toUom, factor });
      navigate('/master-data/uom-conversions');
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
    options: UnitOfMeasure[],
    required: boolean,
  ): JSX.Element => (
    <FormField label={t(labelKey)} required={required}>
      {({ id }) => (
        <select id={id} className="input" value={value} onChange={(e) => onChange(e.target.value)} disabled={submitting} required={required}>
          <option value="">—</option>
          {options.map((o) => (
            <option key={o.id} value={o.id}>{o.name_fa || o.code} ({o.code})</option>
          ))}
        </select>
      )}
    </FormField>
  );

  return (
    <div className="stack">
      <div className="page-header"><h1 className="page-header__title">{t('uomConversions.new')}</h1></div>
      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>{error}</Alert>}
          {selectField('uoms.fromUom', fromUom, setFromUom, uoms, true)}
          {selectField('uoms.toUom', toUom, setToUom, uoms, true)}
          <FormField label={t('uoms.factor')} required>
            {({ id }) => (
              <Input id={id} type="number" step="any" value={factor} onChange={(e) => setFactor(e.target.value)} disabled={submitting} required />
            )}
          </FormField>
          <div className="form-actions">
            <Button type="submit" loading={submitting}>{t('masterData.save')}</Button>
            <Button type="button" variant="secondary" onClick={() => navigate('/master-data/uom-conversions')} disabled={submitting}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}