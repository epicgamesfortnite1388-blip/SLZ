import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '@/api/client';
import type { UnitOfMeasure } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

/** UoM dimensions (mirrors ``UomDimension`` choices). */
const DIMENSIONS = ['MASS', 'LENGTH', 'AREA', 'VOLUME', 'COUNT', 'TIME'] as const;

/**
 * Unit-of-measure edit form — PartnerEditPage PATCH flow for reference data.
 * `code` stays fixed (identities are immutable); naming, dimension, and the
 * active flag are editable.
 */
export function UomEditPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [dimension, setDimension] = useState('COUNT');
  const [isActive, setIsActive] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<UnitOfMeasure>(`/catalog/uoms/${id}/`)
      .then((uom) => {
        if (cancelled) return;
        setCode(uom.code);
        setNameFa(uom.name_fa);
        setNameEn(uom.name_en ?? '');
        setDimension(uom.dimension);
        setIsActive(uom.is_active);
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
      await apiClient.patch<UnitOfMeasure>(`/catalog/uoms/${id}/`, {
        name_fa: nameFa,
        name_en: nameEn,
        dimension,
        is_active: isActive,
      });
      navigate('/master-data/uoms');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

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
        <h1 className="page-header__title">{t('uoms.edit')}</h1>
      </div>
      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

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

          <FormField label={t('uoms.dimension')} required>
            {({ id: fieldId }) => (
              <select
                id={fieldId}
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
              onClick={() => navigate('/master-data/uoms')}
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
