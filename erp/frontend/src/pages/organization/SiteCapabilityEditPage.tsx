import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '@/api/client';
import {
  PRODUCTION_CAPABILITIES,
  updateSiteCapability,
  type ProductionCapability,
  type SiteCapability,
} from '@/api/organization';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Site-capability edit form — PartnerEditPage PATCH flow for SR-15
 * capability declarations. Site stays selectable; capability, active flag,
 * and notes are editable.
 */
export function SiteCapabilityEditPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [sites, setSites] = useState<Option[]>([]);
  const [site, setSite] = useState('');
  const [capability, setCapability] = useState<ProductionCapability>('FILM_BLOWING');
  const [notes, setNotes] = useState('');
  const [isActive, setIsActive] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiClient.get<SiteCapability>(`/organization/site-capabilities/${id}/`),
      apiClient.get<Paginated<Option>>('/organization/sites/?page_size=200'),
    ])
      .then(([cap, si]) => {
        if (cancelled) return;
        setSite(cap.site);
        setCapability(cap.capability);
        setNotes(cap.notes ?? '');
        setIsActive(cap.is_active);
        setSites(si.results);
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
      await updateSiteCapability(id, {
        site,
        capability,
        notes,
        is_active: isActive,
      });
      navigate('/organization/site-capabilities');
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
        <h1 className="page-header__title">{t('organization.siteCapabilities.edit')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <FormField label={t('organization.fields.site')} required>
            {({ id: fieldId }) => (
              <select
                id={fieldId}
                className="input"
                value={site}
                onChange={(e) => setSite(e.target.value)}
                disabled={submitting}
                required
              >
                <option value="">—</option>
                {sites.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name_fa} ({s.code})
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('organization.siteCapabilities.capability')} required>
            {({ id: fieldId }) => (
              <select
                id={fieldId}
                className="input"
                value={capability}
                onChange={(e) => setCapability(e.target.value as ProductionCapability)}
                disabled={submitting}
                required
              >
                {PRODUCTION_CAPABILITIES.map((c) => (
                  <option key={c} value={c}>
                    {t(`organization.siteCapabilities.capabilities.${c}`)}
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('inventory.fields.notes')}>
            {({ id: fieldId }) => (
              <Input
                id={fieldId}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                disabled={submitting}
              />
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
              onClick={() => navigate('/organization/site-capabilities')}
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
