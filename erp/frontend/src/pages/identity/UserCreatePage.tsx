import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { createUser, fetchAllCompanies, fetchAllRoles, type UserPayload } from '@/api/identity';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

interface Option { id: string; label: string; }

export function UserCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [language, setLanguage] = useState('fa');
  const [isActive, setIsActive] = useState(true);

  const [roles, setRoles] = useState<Option[]>([]);
  const [companies, setCompanies] = useState<Option[]>([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [selectedCompanyIds, setSelectedCompanyIds] = useState<string[]>([]);
  const [loadingRefs, setLoadingRefs] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchAllRoles(), fetchAllCompanies()])
      .then(([r, c]) => {
        if (cancelled) return;
        setRoles(r.results.map((x) => ({ id: x.id, label: x.code })));
        setCompanies(
          c.results.map((co) => ({
            id: co.id,
            label: co.name_en || co.code,
          })),
        );
      })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoadingRefs(false); });
    return () => { cancelled = true; };
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payload: UserPayload = { email, password, full_name: fullName, language, is_active: isActive, roles: selectedRoleIds, company_ids: selectedCompanyIds };
      await createUser(payload);
      navigate('/identity/users');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('users.new')}</h1>
      </div>
      <Card>
        {loadingRefs && <Spinner label={t('common.loading')} />}
        {!loadingRefs && (
          <form className="stack" onSubmit={handleSubmit} noValidate>
            {error && <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>{error}</Alert>}

            <FormField label={t('users.fields.email')} required>
              {({ id }) => <Input id={id} type="email" value={email} onChange={(e) => setEmail(e.target.value)} disabled={submitting} required />}
            </FormField>

            <FormField label={t('users.fields.password')} required>
              {({ id }) => <Input id={id} type="password" value={password} onChange={(e) => setPassword(e.target.value)} disabled={submitting} required minLength={8} />}
            </FormField>

            <FormField label={t('users.fields.fullName')}>
              {({ id }) => <Input id={id} value={fullName} onChange={(e) => setFullName(e.target.value)} disabled={submitting} />}
            </FormField>

            <FormField label={t('users.fields.language')}>
              {({ id }) => (
                <select id={id} className="input" value={language} onChange={(e) => setLanguage(e.target.value)} disabled={submitting}>
                  <option value="fa">فارسی</option>
                  <option value="en">English</option>
                </select>
              )}
            </FormField>

            <FormField label={t('users.fields.isActive')}>
              {({ id }) => (
                <input id={id} type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} disabled={submitting} />
              )}
            </FormField>

            <FormField label={t('roles.title')}>
              {() => (
                <select multiple className="input" value={selectedRoleIds} onChange={(e) => setSelectedRoleIds(Array.from(e.target.selectedOptions, (o) => o.value))} disabled={submitting} style={{ height: 120 }}>
                  {roles.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
                </select>
              )}
            </FormField>

            <FormField label={t('organization.companies.title')}>
              {() => (
                <select multiple className="input" value={selectedCompanyIds} onChange={(e) => setSelectedCompanyIds(Array.from(e.target.selectedOptions, (o) => o.value))} disabled={submitting} style={{ height: 120 }}>
                  {companies.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
                </select>
              )}
            </FormField>

            <div className="form-actions">
              <Button type="submit" loading={submitting}>{t('masterData.save')}</Button>
              <Button type="button" variant="secondary" onClick={() => navigate('/identity/users')} disabled={submitting}>{t('common.cancel')}</Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}