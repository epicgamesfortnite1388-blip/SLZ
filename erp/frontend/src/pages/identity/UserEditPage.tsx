import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { updateUser, fetchAllCompanies, fetchAllRoles, type UserPayload } from '@/api/identity';
import { apiClient } from '@/api/client';
import { isApiError } from '@/api/types';
import type { PlatformUser } from '@/api/identity';
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

interface Option { id: string; label: string; }

export function UserEditPage(): JSX.Element {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [user, setUser] = useState<PlatformUser | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [language, setLanguage] = useState('fa');
  const [isActive, setIsActive] = useState(true);

  const [roles, setRoles] = useState<Option[]>([]);
  const [companies, setCompanies] = useState<Option[]>([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [selectedCompanyIds, setSelectedCompanyIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    Promise.all([
      apiClient.get<PlatformUser>(`/auth/users/${id}/`),
      fetchAllRoles(),
      fetchAllCompanies(),
    ]).then(([u, r, c]) => {
      if (cancelled) return;
      setUser(u);
      setEmail(u.email);
      setFullName(u.full_name);
      setLanguage(u.language);
      setIsActive(u.is_active);
      setSelectedRoleIds(u.roles);
      setSelectedCompanyIds(u.companies);
      setRoles(r.results.map((x) => ({ id: x.id, label: x.code })));
      setCompanies(c.results.map((co) => ({ id: co.id, label: co.name_en || co.code })));
    }).catch(() => {}).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [id]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setError(null);
    setSubmitting(true);
    try {
      const payload: Partial<UserPayload> = { email, full_name: fullName, language, is_active: isActive, roles: selectedRoleIds, company_ids: selectedCompanyIds };
      if (password) payload.password = password;
      await updateUser(id, payload);
      navigate('/identity/users');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="table-state"><Spinner label={t('common.loading')} /></div>;
  if (!user) return <Alert variant="danger" title={t('common.error')}>{t('common.notFound')}</Alert>;

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('users.edit', { email: user.email })}</h1>
      </div>
      <Card>
        <form className="stack" onSubmit={handleSubmit} noValidate>
          {error && <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>{error}</Alert>}

          <FormField label={t('users.fields.email')} required>
            {({ id }) => <Input id={id} type="email" value={email} onChange={(e) => setEmail(e.target.value)} disabled={submitting} required />}
          </FormField>

          <FormField label={t('users.fields.password')}>
            {({ id: id }) => <Input id={id} type="password" value={password} onChange={(e) => setPassword(e.target.value)} disabled={submitting} minLength={8} placeholder={t('users.fields.passwordHint')} />}
          </FormField>

          <FormField label={t('users.fields.fullName')}>
            {({ id: id }) => <Input id={id} value={fullName} onChange={(e) => setFullName(e.target.value)} disabled={submitting} />}
          </FormField>

          <FormField label={t('users.fields.language')}>
            {({ id: id }) => (
              <select id={id} className="input" value={language} onChange={(e) => setLanguage(e.target.value)} disabled={submitting}>
                <option value="fa">فارسی</option>
                <option value="en">English</option>
              </select>
            )}
          </FormField>

          <FormField label={t('users.fields.isActive')}>
            {({ id: id }) => (
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
      </Card>
    </div>
  );
}