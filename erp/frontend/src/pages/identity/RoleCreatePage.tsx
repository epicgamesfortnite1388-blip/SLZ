import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { createRole } from '@/api/roles';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

/**
 * Create a platform role. Permission assignment is deliberately not part of
 * this form: the catalogue shape (which permissions exist, which bundles make
 * sense) is Q-053 territory — only the container is created here.
 */
export function RoleCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [code, setCode] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [description, setDescription] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createRole({
        code,
        name_en: nameEn || undefined,
        name_fa: nameFa || undefined,
        description: description || undefined,
      });
      navigate('/identity/roles');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('roles.new')}</h1>
      </div>
      <Card>
        <form
          className="stack"
          onSubmit={(e) => {
            e.preventDefault();
            void handleSubmit(e);
          }}
          noValidate
        >
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <FormField label={t('masterData.fields.code')} required>
            {({ id }) => (
              <Input id={id} value={code} onChange={(e) => setCode(e.target.value)} disabled={submitting} required />
            )}
          </FormField>

          <FormField label={t('roles.fields.nameEn')}>
            {({ id }) => (
              <Input id={id} value={nameEn} onChange={(e) => setNameEn(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('roles.fields.nameFa')}>
            {({ id }) => (
              <Input id={id} value={nameFa} onChange={(e) => setNameFa(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('roles.fields.description')}>
            {({ id }) => (
              <Input id={id} value={description} onChange={(e) => setDescription(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <div className="form-actions">
            <Button type="submit" loading={submitting}>
              {t('masterData.save')}
            </Button>
            <Button type="button" variant="secondary" onClick={() => navigate('/identity/roles')} disabled={submitting}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
