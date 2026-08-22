import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import {
  createQualityCharacteristic,
  CHARACTERISTIC_DATATYPES,
  type CharacteristicDatatype,
} from '@/api/quality';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Quality-characteristic create form — the representative audited write flow for
 * Task 008 (POST → domain event → audit). Business rules (unique code per
 * company, referential integrity, valid datatype) are enforced server-side; the
 * UI surfaces the backend's 400 rather than duplicating the rule. ``method`` is
 * free text because SLZ's test methods/standards are OPEN (Q-039).
 */
export function CharacteristicCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<Option[]>([]);

  const [company, setCompany] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [datatype, setDatatype] = useState<CharacteristicDatatype>('NUMBER');
  const [method, setMethod] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<Paginated<Option>>('/organization/companies/?page_size=100')
      .then((res) => {
        if (cancelled) return;
        setCompanies(res.results);
        if (res.results.length > 0) setCompany(res.results[0].id);
      })
      .catch(() => {
        /* Non-fatal: field stays empty and the user sees a validation error. */
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
      await createQualityCharacteristic({
        company,
        code,
        name_fa: nameFa,
        name_en: nameEn,
        datatype,
        method,
      });
      navigate('/quality/characteristics');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('quality.characteristics.new')}</h1>
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
                <option value="">—</option>
                {companies.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name_fa} ({o.code})
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

          <FormField label={t('quality.fields.datatype')} required>
            {({ id }) => (
              <select
                id={id}
                className="input"
                value={datatype}
                onChange={(e) => setDatatype(e.target.value as CharacteristicDatatype)}
                disabled={submitting}
                required
              >
                {CHARACTERISTIC_DATATYPES.map((d) => (
                  <option key={d} value={d}>
                    {t(`quality.datatypes.${d}`)}
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('quality.fields.method')}>
            {({ id }) => (
              <Input
                id={id}
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                disabled={submitting}
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
              onClick={() => navigate('/quality/characteristics')}
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
