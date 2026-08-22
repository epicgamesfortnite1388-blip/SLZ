import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';
import { LanguageSwitcher } from '@/components/layout/LanguageSwitcher';

interface LocationState {
  from?: { pathname?: string };
}

/** Public sign-in page. Redirects to the intended route once authenticated. */
export function LoginPage(): JSX.Element {
  const { t } = useTranslation();
  const { login, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const redirectTo =
    (location.state as LocationState | null)?.from?.pathname ?? '/';

  if (!loading && isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      if (isApiError(err)) {
        setError(err.message);
      } else {
        setError(t('login.error'));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="center-screen">
      <div className="login">
        <div className="login__header">
          <div className="login__mark" aria-hidden="true">
            SLZ
          </div>
          <h1 className="login__title">{t('login.title')}</h1>
          <p className="login__subtitle">{t('login.subtitle')}</p>
        </div>

        <Card>
          <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
            {error && (
              <Alert variant="danger" onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            <FormField label={t('login.email')} required>
              {({ id, describedBy }) => (
                <Input
                  id={id}
                  aria-describedby={describedBy}
                  type="email"
                  name="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t('login.emailPlaceholder')}
                  required
                  disabled={submitting}
                />
              )}
            </FormField>

            <FormField label={t('login.password')} required>
              {({ id, describedBy }) => (
                <Input
                  id={id}
                  aria-describedby={describedBy}
                  type="password"
                  name="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t('login.passwordPlaceholder')}
                  required
                  disabled={submitting}
                />
              )}
            </FormField>

            <Button type="submit" fullWidth loading={submitting}>
              {submitting ? t('login.submitting') : t('login.submit')}
            </Button>
          </form>
        </Card>

        <div style={{ display: 'flex', justifyContent: 'center', marginTop: 'var(--space-4)' }}>
          <LanguageSwitcher />
        </div>
      </div>
    </div>
  );
}
