import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createRoutingRoot } from '@/api/manufacturing';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField } from '@/components/ui';

interface Option {
  id: string;
  name_fa: string;
}

/**
 * Routing root create form — binds a new routing root to a specification
 * revision. A DRAFT revision is automatically created server-side.
 */
export function RoutingRootCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [specRevisions, setSpecRevisions] = useState<Option[]>([]);
  const [specRevision, setSpecRevision] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient.get<Paginated<Option>>('/engineering/specifications/?page_size=200')
      .then((res) => { if (!cancelled) { setSpecRevisions(res.results); if (res.results.length > 0) setSpecRevision(res.results[0].id); } })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createRoutingRoot({ spec_revision: specRevision });
      navigate('/manufacturing/routings');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('manufacturing.routingRoots.new')}</h1>
      </div>
      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          <FormField label={t('manufacturing.fields.specRevision')} required>
            {({ id }) => (
              <select
                id={id}
                className="input"
                value={specRevision}
                onChange={(e) => setSpecRevision(e.target.value)}
                disabled={submitting}
                required
              >
                <option value="">—</option>
                {specRevisions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name_fa ?? s.id}
                  </option>
                ))}
              </select>
            )}
          </FormField>
          <div className="form-actions">
            <Button type="submit" loading={submitting}>{t('masterData.save')}</Button>
            <Button type="button" variant="secondary" onClick={() => navigate('/manufacturing/routings')} disabled={submitting}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}