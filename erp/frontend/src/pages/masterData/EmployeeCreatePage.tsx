import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createEmployee } from '@/api/masterData';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Employee create form — minimal HR master with company/site/department scoping.
 */
export function EmployeeCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<Option[]>([]);
  const [sites, setSites] = useState<Option[]>([]);
  const [departments, setDepartments] = useState<Option[]>([]);

  const [company, setCompany] = useState('');
  const [site, setSite] = useState('');
  const [department, setDepartment] = useState('');
  const [code, setCode] = useState('');
  const [firstNameFa, setFirstNameFa] = useState('');
  const [lastNameFa, setLastNameFa] = useState('');
  const [firstNameEn, setFirstNameEn] = useState('');
  const [lastNameEn, setLastNameEn] = useState('');
  const [jobTitle, setJobTitle] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient.get<Paginated<Option>>('/organization/companies/?page_size=200')
      .then((res) => { if (!cancelled) { setCompanies(res.results); if (res.results.length > 0) setCompany(res.results[0].id); } })
      .catch(() => {});
    apiClient.get<Paginated<Option>>('/organization/sites/?page_size=200')
      .then((res) => { if (!cancelled) setSites(res.results); })
      .catch(() => {});
    apiClient.get<Paginated<Option>>('/organization/departments/?page_size=200')
      .then((res) => { if (!cancelled) setDepartments(res.results); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createEmployee({
        company,
        site: site || undefined,
        department: department || undefined,
        employee_code: code,
        first_name_fa: firstNameFa,
        last_name_fa: lastNameFa,
        first_name_en: firstNameEn,
        last_name_en: lastNameEn,
        job_title: jobTitle,
      });
      navigate('/master-data/employees');
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
        <h1 className="page-header__title">{t('employees.new')}</h1>
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
          {selectField('organization.departments.title', department, setDepartment, departments, false)}

          <FormField label={t('employees.code')} required>
            {({ id }) => (
              <Input id={id} value={code} onChange={(e) => setCode(e.target.value)} disabled={submitting} required />
            )}
          </FormField>

          <div className="field-row">
            <FormField label={t('masterData.fields.nameFa') + ' — ' + t('employees.firstName')} required>
              {({ id }) => (
                <Input id={id} value={firstNameFa} onChange={(e) => setFirstNameFa(e.target.value)} disabled={submitting} required />
              )}
            </FormField>
            <FormField label={t('masterData.fields.nameFa') + ' — ' + t('employees.lastName')} required>
              {({ id }) => (
                <Input id={id} value={lastNameFa} onChange={(e) => setLastNameFa(e.target.value)} disabled={submitting} required />
              )}
            </FormField>
          </div>

          <div className="field-row">
            <FormField label={t('masterData.fields.nameEn') + ' — ' + t('employees.firstName')}>
              {({ id }) => (
                <Input id={id} value={firstNameEn} onChange={(e) => setFirstNameEn(e.target.value)} disabled={submitting} />
              )}
            </FormField>
            <FormField label={t('masterData.fields.nameEn') + ' — ' + t('employees.lastName')}>
              {({ id }) => (
                <Input id={id} value={lastNameEn} onChange={(e) => setLastNameEn(e.target.value)} disabled={submitting} />
              )}
            </FormField>
          </div>

          <FormField label={t('employees.jobTitle')}>
            {({ id }) => (
              <Input id={id} value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <div className="form-actions">
            <Button type="submit" loading={submitting}>{t('masterData.save')}</Button>
            <Button type="button" variant="secondary" onClick={() => navigate('/master-data/employees')} disabled={submitting}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}