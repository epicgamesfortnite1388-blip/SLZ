import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Alert, Card, Spinner } from '@/components/ui';
import { BoolCell } from '@/components/CollectionView';
import { RecordDetail, type DetailField } from '@/components/RecordDetail';
import { AttachmentPanel } from '@/components/AttachmentPanel';
import { AuditHistoryPanel } from '@/components/AuditHistoryPanel';
import { useRecord } from '@/hooks/useRecord';
import type { Employee } from '@/api/masterData';

const ENTITY_TYPE = 'hr.Employee';

export function EmployeeDetailPage(): JSX.Element {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const { hasPermission } = useAuth();
  const { data, loading, error } = useRecord<Employee>(
    id ? `/hr/employees/${id}/` : null,
  );

  const dash = (value: string | null): string => value || '—';

  const fields: DetailField[] = data
    ? [
        { labelKey: 'employees.code', value: data.employee_code },
        {
          labelKey: 'masterData.fields.nameFa',
          value: `${dash(data.first_name_fa)} ${dash(data.last_name_fa)}`.trim() || '—',
        },
        {
          labelKey: 'masterData.fields.nameEn',
          value: `${dash(data.first_name_en)} ${dash(data.last_name_en)}`.trim() || '—',
        },
        { labelKey: 'employees.jobTitle', value: dash(data.job_title) },
        { labelKey: 'masterData.fields.active', value: <BoolCell value={data.is_active} /> },
      ]
    : [];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">
          {data
            ? `${data.first_name_fa || data.first_name_en || ''} ${data.last_name_fa || data.last_name_en || ''}`.trim()
            : t('employees.detail.title')}
        </h1>
        <p className="page-header__subtitle">
          <Link to="/master-data/employees" className="link-back">
            {t('employees.detail.back')}
          </Link>
        </p>
      </div>

      {loading && <Spinner />}

      {error && (
        <Alert variant="danger" title={t('common.error')}>
          {error.message}
        </Alert>
      )}

      {data && (
        <>
          <RecordDetail title={t('employees.detail.title')} fields={fields} />
          {hasPermission('documents.attachment.view') && id && (
            <AttachmentPanel entityType={ENTITY_TYPE} entityId={id} />
          )}
          <AuditHistoryPanel entityType={ENTITY_TYPE} entityId={id ?? ''} />
        </>
      )}

      {!loading && !error && !data && (
        <Card>
          <div className="stat-card__note">{t('employees.detail.notFound')}</div>
        </Card>
      )}
    </div>
  );
}