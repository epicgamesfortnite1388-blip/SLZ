import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { apiClient } from '@/api/client';
import { createDepartment, type Department } from '@/api/organization';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';

interface Option {
  id: string;
  name_fa: string;
}

/**
 * Departments: site-scoped organizational units with an optional parent for
 * hierarchy. List and create are on the same page (master-data browse pattern).
 */
export function DepartmentsPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const collection = useCollection<Department>('/organization/departments/');

  const canManage = hasPermission('organization.department.manage');

  const columns: Column<Department>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    { headerKey: 'masterData.fields.nameEn', render: (r) => r.name_en || '—' },
    {
      headerKey: 'masterData.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];

  return (
    <div className="stack">
      <CollectionView
        titleKey="organization.departments.title"
        subtitleKey="organization.departments.subtitle"
        columns={columns}
        rowKey={(r) => r.id}
        collection={collection}
        headerAction={
          canManage ? (
            <Button size="sm" onClick={() => navigate('/organization/departments/new')}>
              {t('organization.departments.new')}
            </Button>
          ) : null
        }
      />
    </div>
  );
}

/**
 * Department create form — follows the established master-data create pattern
 * with site picker, code, and bilingual name fields.
 */
export function DepartmentCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [sites, setSites] = useState<Option[]>([]);
  const [departments, setDepartments] = useState<Option[]>([]);

  const [site, setSite] = useState('');
  const [parent, setParent] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = (path: string, set: (v: Option[]) => void): void => {
      apiClient
        .get<Paginated<Option>>(`${path}?page_size=200`)
        .then((res) => {
          if (cancelled) return;
          set(res.results);
        })
        .catch(() => {
          /* Non-fatal. */
        });
    };
    load('/organization/sites/', setSites);
    load('/organization/departments/', setDepartments);
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createDepartment({
        site,
        parent: parent || null,
        code,
        name_fa: nameFa,
        name_en: nameEn,
      });
      navigate('/organization/departments');
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
              {o.name_fa}
            </option>
          ))}
        </select>
      )}
    </FormField>
  );

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('organization.departments.new')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {selectField('organization.fields.site', site, setSite, sites, true)}
          {selectField('organization.departments.parent', parent, setParent, departments, false)}

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
              onClick={() => navigate('/organization/departments')}
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