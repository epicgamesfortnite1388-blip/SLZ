import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { updateEmployee, type Employee, type Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Employee edit form — replicates the PartnerEditPage PATCH flow for the HR
 * Employee master. `employee_code` stays fixed (business numbers are immutable
 * identities); scoping, naming, and job title are editable and audited
 * server-side.
 */
export function EmployeeEditPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

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
  const [isActive, setIsActive] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiClient.get<Employee>(`/hr/employees/${id}/`),
      apiClient.get<Paginated<Option>>('/organization/companies/?page_size=200'),
      apiClient.get<Paginated<Option>>('/organization/sites/?page_size=200'),
      apiClient.get<Paginated<Option>>('/organization/departments/?page_size=200'),
    ])
      .then(([employee, co, si, de]) => {
        if (cancelled) return;
        setCompany(employee.company);
        setSite(employee.site ?? '');
        setDepartment(employee.department ?? '');
        setCode(employee.employee_code);
        setFirstNameFa(employee.first_name_fa);
        setLastNameFa(employee.last_name_fa);
        setFirstNameEn(employee.first_name_en ?? '');
        setLastNameEn(employee.last_name_en ?? '');
        setJobTitle(employee.job_title ?? '');
        setIsActive(employee.is_active);
        setCompanies(co.results);
        setSites(si.results);
        setDepartments(de.results);
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
      await updateEmployee(id, {
        company,
        site: site || null,
        department: department || null,
        first_name_fa: firstNameFa,
        last_name_fa: lastNameFa,
        first_name_en: firstNameEn,
        last_name_en: lastNameEn,
        job_title: jobTitle,
        is_active: isActive,
      });
      navigate(`/master-data/employees/${id}`);
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
          {options.map((o) => (
            <option key={o.id} value={o.id}>
              {o.name_fa} ({o.code})
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
        <h1 className="page-header__title">{t('employees.edit')}</h1>
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

          <FormField label={t('employees.code')}>
            {({ id: fieldId }) => <Input id={fieldId} value={code} disabled readOnly />}
          </FormField>

          <div className="field-row">
            <FormField label={t('masterData.fields.nameFa') + ' — ' + t('employees.firstName')} required>
              {({ id: fieldId }) => (
                <Input
                  id={fieldId}
                  value={firstNameFa}
                  onChange={(e) => setFirstNameFa(e.target.value)}
                  disabled={submitting}
                  required
                />
              )}
            </FormField>
            <FormField label={t('masterData.fields.nameFa') + ' — ' + t('employees.lastName')} required>
              {({ id: fieldId }) => (
                <Input
                  id={fieldId}
                  value={lastNameFa}
                  onChange={(e) => setLastNameFa(e.target.value)}
                  disabled={submitting}
                  required
                />
              )}
            </FormField>
          </div>

          <div className="field-row">
            <FormField label={t('masterData.fields.nameEn') + ' — ' + t('employees.firstName')}>
              {({ id: fieldId }) => (
                <Input
                  id={fieldId}
                  value={firstNameEn}
                  onChange={(e) => setFirstNameEn(e.target.value)}
                  disabled={submitting}
                />
              )}
            </FormField>
            <FormField label={t('masterData.fields.nameEn') + ' — ' + t('employees.lastName')}>
              {({ id: fieldId }) => (
                <Input
                  id={fieldId}
                  value={lastNameEn}
                  onChange={(e) => setLastNameEn(e.target.value)}
                  disabled={submitting}
                />
              )}
            </FormField>
          </div>

          <FormField label={t('employees.jobTitle')}>
            {({ id: fieldId }) => (
              <Input
                id={fieldId}
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
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
              onClick={() => navigate(`/master-data/employees/${id}`)}
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
