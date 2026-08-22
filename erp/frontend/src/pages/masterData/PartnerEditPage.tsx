import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '@/api/client';
import {
  updatePartner,
  type Paginated,
  type Partner,
} from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

interface CompanyOption {
  id: string;
  code: string;
  name_fa: string;
  name_en: string;
}

/**
 * Partner edit form — the reference master-data EDIT flow (PATCH). Prefills
 * from the existing retrieve endpoint; `company` and `code` stay fixed because
 * business numbers are immutable identities (server also enforces this via the
 * serializer's read-only handling of uniqueness-bearing identity fields on
 * update paths used by the UI).
 */
export function PartnerEditPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [companies, setCompanies] = useState<CompanyOption[]>([]);
  const [company, setCompany] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [isCustomer, setIsCustomer] = useState(false);
  const [isSupplier, setIsSupplier] = useState(false);
  const [isSanctioned, setIsSanctioned] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Load the record to edit + the company picker options.
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiClient.get<Partner>(`/partners/partners/${id}/`),
      apiClient.get<Paginated<CompanyOption>>('/organization/companies/?page_size=100'),
    ])
      .then(([partner, res]) => {
        if (cancelled) return;
        setCode(partner.code);
        setNameFa(partner.name_fa);
        setNameEn(partner.name_en);
        setIsCustomer(partner.is_customer);
        setIsSupplier(partner.is_supplier);
        setIsSanctioned(partner.is_sanctioned);
        setCompanies(res.results);
        setCompany(partner.company);
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
      await updatePartner(id, {
        company,
        name_fa: nameFa,
        name_en: nameEn,
        is_customer: isCustomer,
        is_supplier: isSupplier,
        is_sanctioned: isSanctioned,
      });
      navigate(`/master-data/partners/${id}`);
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
        <h1 className="page-header__title">{t('partners.edit')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <FormField label={t('masterData.fields.company')} required>
            {({ id: fieldId }) => (
              <select
                id={fieldId}
                className="input"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                disabled={submitting}
                required
              >
                {companies.length === 0 && <option value="">—</option>}
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name_fa} ({c.code})
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('masterData.fields.code')}>
            {({ id: fieldId }) => (
              <Input id={fieldId} value={code} disabled readOnly />
            )}
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

          <div className="checkbox-row">
            <label className="checkbox">
              <input
                type="checkbox"
                checked={isCustomer}
                onChange={(e) => setIsCustomer(e.target.checked)}
                disabled={submitting}
              />
              {t('partners.isCustomer')}
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={isSupplier}
                onChange={(e) => setIsSupplier(e.target.checked)}
                disabled={submitting}
              />
              {t('partners.isSupplier')}
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={isSanctioned}
                onChange={(e) => setIsSanctioned(e.target.checked)}
                disabled={submitting}
              />
              {t('partners.sanctioned')}
            </label>
          </div>

          <div className="form-actions">
            <Button type="submit" loading={submitting}>
              {t('masterData.save')}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate(`/master-data/partners/${id}`)}
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
