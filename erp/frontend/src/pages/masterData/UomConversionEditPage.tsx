import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '@/api/client';
import type { Paginated, UomConversion } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

interface UomOption {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * UoM-conversion edit form — PartnerEditPage PATCH flow. From/to units and
 * the factor are editable; same-dimension and positive-factor rules are
 * enforced server-side and surfaced as the backend's 400.
 */
export function UomConversionEditPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [uoms, setUoms] = useState<UomOption[]>([]);
  const [fromUom, setFromUom] = useState('');
  const [toUom, setToUom] = useState('');
  const [factor, setFactor] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiClient.get<UomConversion>(`/catalog/uom-conversions/${id}/`),
      apiClient.get<Paginated<UomOption>>('/catalog/uoms/?page_size=200'),
    ])
      .then(([conversion, uo]) => {
        if (cancelled) return;
        setFromUom(conversion.from_uom);
        setToUom(conversion.to_uom);
        setFactor(conversion.factor);
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
      await apiClient.patch<UomConversion>(`/catalog/uom-conversions/${id}/`, {
        from_uom: fromUom,
        to_uom: toUom,
        factor,
      });
      navigate('/master-data/uom-conversions');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  const uomSelect = (
    labelKey: string,
    value: string,
    onChange: (v: string) => void,
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
          {uoms.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name_fa} ({u.code})
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
        <h1 className="page-header__title">{t('uomConversions.edit')}</h1>
      </div>
      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {uomSelect('uomConversions.from', fromUom, setFromUom, true)}
          {uomSelect('uomConversions.to', toUom, setToUom, true)}

          <FormField label={t('uomConversions.factor')} required>
            {({ id: fieldId }) => (
              <Input
                id={fieldId}
                type="number"
                step="any"
                min="0"
                value={factor}
                onChange={(e) => setFactor(e.target.value)}
                disabled={submitting}
                required
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
              onClick={() => navigate('/master-data/uom-conversions')}
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
