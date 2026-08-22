import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createPartner, type Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface CompanyOption {
  id: string;
  code: string;
  name_fa: string;
  name_en: string;
}

/**
 * Partner create form — the representative write flow for Task 004 master
 * data. Exercises the full audited service path (POST → domain event → audit).
 * The role rule (customer or supplier) is enforced server-side; we surface the
 * backend's 400 message rather than duplicating the rule on the client.
 */
export function PartnerCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<CompanyOption[]>([]);
  const [company, setCompany] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [isCustomer, setIsCustomer] = useState(true);
  const [isSupplier, setIsSupplier] = useState(false);
  const [isSanctioned, setIsSanctioned] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<Paginated<CompanyOption>>('/organization/companies/?page_size=100')
      .then((res) => {
        if (cancelled) return;
        setCompanies(res.results);
        if (res.results.length > 0) setCompany(res.results[0].id);
      })
      .catch(() => {
        /* Non-fatal: the field simply stays empty and the user sees a validation error. */
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
      await createPartner({
        company,
        code,
        name_fa: nameFa,
        name_en: nameEn,
        is_customer: isCustomer,
        is_supplier: isSupplier,
        is_sanctioned: isSanctioned,
      });
      navigate('/master-data/partners');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('partners.new')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <FormField label={t('masterData.fields.company')} required>
            {({ id }) => (
              <select
                id={id}
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

          <FormField label={t('masterData.fields.code')} required>
            {({ id }) => (
              <Input
                id={id}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                disabled={submitting}
                required
              />
            )}
          </FormField>

          <FormField label={t('masterData.fields.nameFa')} required>
            {({ id }) => (
              <Input
                id={id}
                value={nameFa}
                onChange={(e) => setNameFa(e.target.value)}
                disabled={submitting}
                required
              />
            )}
          </FormField>

          <FormField label={t('masterData.fields.nameEn')}>
            {({ id }) => (
              <Input
                id={id}
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
              onClick={() => navigate('/master-data/partners')}
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
