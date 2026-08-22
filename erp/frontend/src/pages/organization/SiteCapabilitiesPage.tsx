import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { apiClient } from '@/api/client';
import {
  createSiteCapability,
  PRODUCTION_CAPABILITIES,
  type ProductionCapability,
  type SiteCapability,
} from '@/api/organization';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';

interface Option {
  id: string;
  name_fa: string;
}

/**
 * Site production-capability declarations (SR-15 / DR-041): list which sites
 * can perform which production stages. Master-data surfacing only — capacity
 * numbers are a later manufacturing concern.
 */
export function SiteCapabilitiesPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const collection = useCollection<SiteCapability>(
    '/organization/site-capabilities/',
  );

  const canManage = hasPermission('organization.sitecapability.manage');

  const columns: Column<SiteCapability>[] = [
    { headerKey: 'organization.fields.site', render: (r) => r.site /* FK id — server returns label via select_related; shown as-is for now */ },
    {
      headerKey: 'organization.siteCapabilities.capability',
      render: (r) => t(`organization.siteCapabilities.capabilities.${r.capability}`),
    },
    {
      headerKey: 'masterData.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];

  return (
    <div className="stack">
      <CollectionView
        titleKey="organization.siteCapabilities.title"
        subtitleKey="organization.siteCapabilities.subtitle"
        columns={columns}
        rowKey={(r) => r.id}
        collection={collection}
        headerAction={
          canManage ? (
            <Button size="sm" onClick={() => navigate('/organization/site-capabilities/new')}>
              {t('organization.siteCapabilities.new')}
            </Button>
          ) : null
        }
      />
    </div>
  );
}

/**
 * Site-capability create form — site picker + capability dropdown, routed
 * through the audited service layer.
 */
export function SiteCapabilityCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [sites, setSites] = useState<Option[]>([]);
  const [site, setSite] = useState('');
  const [capability, setCapability] = useState<ProductionCapability>('FILM_BLOWING');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<Paginated<Option>>('/organization/sites/?page_size=200')
      .then((res) => {
        if (cancelled) return;
        setSites(res.results);
        if (res.results.length > 0) setSite(res.results[0].id);
      })
      .catch(() => {
        /* Non-fatal. */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createSiteCapability({ site, capability });
      navigate('/organization/site-capabilities');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('organization.siteCapabilities.new')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <FormField label={t('organization.fields.site')} required>
            {({ id }) => (
              <select
                id={id}
                className="input"
                value={site}
                onChange={(e) => setSite(e.target.value)}
                disabled={submitting}
                required
              >
                <option value="">—</option>
                {sites.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name_fa}
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('organization.siteCapabilities.capability')} required>
            {({ id }) => (
              <select
                id={id}
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