import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { createWorkflowDefinition, type ApprovalMode } from '@/api/workflow';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

/**
 * Create an approval-workflow definition — an audited write (`code` unique,
 * enforced server-side). Captures only the approval *shape* (mode + labels);
 * approver assignment and any routing policy stay server-side configuration
 * (do-not-build-yet #7), so this form deliberately exposes no rule matrix.
 */
export function WorkflowDefinitionCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [approvalMode, setApprovalMode] = useState<ApprovalMode>('SEQUENTIAL');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createWorkflowDefinition({
        code,
        name_fa: nameFa,
        name_en: nameEn,
        approval_mode: approvalMode,
      });
      navigate('/workflow/definitions');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('workflow.definitions.new')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

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

          <FormField label={t('workflow.definitions.mode')}>
            {({ id }) => (
              <select
                id={id}
                className="input"
                value={approvalMode}
                onChange={(e) => setApprovalMode(e.target.value as ApprovalMode)}
                disabled={submitting}
              >
                <option value="SEQUENTIAL">{t('workflow.modes.SEQUENTIAL')}</option>
                <option value="PARALLEL">{t('workflow.modes.PARALLEL')}</option>
              </select>
            )}
          </FormField>

          <div className="form-actions">
            <Button type="submit" loading={submitting}>
              {t('masterData.save')}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/workflow/definitions')}
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
