import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Alert, Card, Spinner } from '@/components/ui';
import { BoolCell } from '@/components/CollectionView';
import { RecordDetail, type DetailField } from '@/components/RecordDetail';
import { AttachmentPanel } from '@/components/AttachmentPanel';
import { AuditHistoryPanel } from '@/components/AuditHistoryPanel';
import { useRecord } from '@/hooks/useRecord';
import { formatDateTime } from '@/i18n/dates';
import type { WorkCenter } from '@/api/manufacturing';

const ENTITY_TYPE = 'manufacturing.WorkCenter';

export function WorkCenterDetailPage(): JSX.Element {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const { hasPermission } = useAuth();
  const { data, loading, error } = useRecord<WorkCenter>(
    id ? `/manufacturing/work-centers/${id}/` : null,
  );

  const dash = (value: string | null): string => value || '—';

  const fields: DetailField[] = data
    ? [
        { labelKey: 'masterData.fields.code', value: data.code },
        { labelKey: 'masterData.fields.nameFa', value: dash(data.name_fa) },
        { labelKey: 'masterData.fields.nameEn', value: dash(data.name_en) },
        { labelKey: 'manufacturing.fields.sequenceHint', value: String(data.sequence_hint) },
        { labelKey: 'manufacturing.fields.site', value: data.site ?? '—' },
        { labelKey: 'products.createdAt', value: formatDateTime(data.created_at, i18n.language) },
        { labelKey: 'masterData.fields.active', value: <BoolCell value={data.is_active} /> },
      ]
    : [];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">
          {data ? data.name_fa || data.name_en || data.code : t('manufacturing.detail.workCenterTitle')}
        </h1>
        <p className="page-header__subtitle">
          <Link to="/manufacturing/work-centers" className="link-back">
            {t('manufacturing.detail.back')}
          </Link>
        </p>
      </div>

      {loading && <Spinner />}

      {error && <Alert variant="danger" title={t('common.error')}>{error.message}</Alert>}

      {data && (
        <>
          <RecordDetail title={t('manufacturing.detail.workCenterTitle')} fields={fields} />
          {hasPermission('documents.attachment.view') && id && (
            <AttachmentPanel entityType={ENTITY_TYPE} entityId={id} />
          )}
          <AuditHistoryPanel entityType={ENTITY_TYPE} entityId={id ?? ''} />
        </>
      )}

      {!loading && !error && !data && (
        <Card><div className="stat-card__note">{t('masterData.empty')}</div></Card>
      )}
    </div>
  );
}