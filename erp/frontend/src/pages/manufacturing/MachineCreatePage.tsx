import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createMachine } from '@/api/manufacturing';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Machine create form — exercises the full audited service path for adding a
 * physical resource with a data-driven capability profile. Company, site, and
 * work-center are select-pickers backed by the live organization/manufacturing
 * endpoints. The capability profile is left blank (constraint #9: no hard-coded
 * machine logic).
 */
export function MachineCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<Option[]>([]);
  const [sites, setSites] = useState<Option[]>([]);
  const [workCenters, setWorkCenters] = useState<Option[]>([]);

  const [company, setCompany] = useState('');
  const [site, setSite] = useState('');
  const [workCenter, setWorkCenter] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = (path: string, set: (v: Option[]) => void, pick?: (f: Option) => void): void => {
      apiClient
        .get<Paginated<Option>>(`${path}?page_size=200`)
        .then((res) => {
          if (cancelled) return;
          set(res.results);
          if (pick && res.results.length > 0) pick(res.results[0]);
        })
        .catch(() => {
          /* Non-fatal: field stays empty and the user sees a validation error. */
        });
    };
    load('/organization/companies/', setCompanies, (f) => setCompany(f.id));
    load('/organization/sites/', setSites);
    load('/manufacturing/work-centers/', setWorkCenters, (f) => setWorkCenter(f.id));
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createMachine({
        company,
        site: site || undefined,
        work_center: workCenter || undefined,
        code,
        name_fa: nameFa,
        name_en: nameEn,
      });
      navigate('/manufacturing/machines');
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
    options: Option[],
    required: boolean,
  ): JSX.Element => (
    <FormField label={t(labelKey)} required={required}>
      {({ id }) => (
        <select
          id={id}
          className="input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={submitting}
          required={required}
        >
          <option value="">—</option>
          {options.map((o) => (
            <option key={o.id} value={o.id}>
              {o.name_fa} ({o.code})
            </option>
          ))}
        </select>
      )}
    </FormField>
  );

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('manufacturing.machines.new')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {selectField('masterData.fields.company', company, setCompany, companies, true)}
          {selectField('manufacturing.fields.site', site, setSite, sites, false)}
          {selectField('manufacturing.workCenters.title', workCenter, setWorkCenter, workCenters, false)}

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

          <div className="form-actions">
            <Button type="submit" loading={submitting}>
              {t('masterData.save')}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/manufacturing/machines')}
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