import { useEffect, useState } from 'react';
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
import { fetchWorkCenter, type Machine } from '@/api/manufacturing';

const ENTITY_TYPE = 'manufacturing.Machine';

function capabilitySummary(profile: Record<string, unknown>): string {
  const keys = Object.keys(profile);
  if (keys.length === 0) return '—';
  return keys.map((k) => `${k}: ${String(profile[k])}`).join(', ');
}

export function MachineDetailPage(): JSX.Element {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const { hasPermission } = useAuth();
  const { data, loading, error } = useRecord<Machine>(
    id ? `/manufacturing/machines/${id}/` : null,
  );

  const [wcLabel, setWcLabel] = useState<string | null>(null);

  // Resolve work_center UUID to readable name.
  useEffect(() => {
    if (!data?.work_center) return;
    let active = true;
    fetchWorkCenter(data.work_center)
      .then((wc) => { if (active) setWcLabel(wc.name_fa || wc.code); })
      .catch(() => { if (active) setWcLabel(data.work_center); });
    return () => { active = false; };
  }, [data]);

  const dash = (value: string | null): string => value || '—';

  const fields: DetailField[] = data
    ? [
        { labelKey: 'masterData.fields.code', value: data.code },
        { labelKey: 'masterData.fields.nameFa', value: dash(data.name_fa) },
        { labelKey: 'masterData.fields.nameEn', value: dash(data.name_en) },
        { labelKey: 'manufacturing.fields.opWorkCenter', value: wcLabel ?? '…' },
        { labelKey: 'manufacturing.fields.site', value: data.site ?? '—' },
        { labelKey: 'manufacturing.fields.capabilities', value: capabilitySummary(data.capability_profile) },
        { labelKey: 'products.createdAt', value: formatDateTime(data.created_at, i18n.language) },
        { labelKey: 'masterData.fields.active', value: <BoolCell value={data.is_active} /> },
      ]
    : [];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">
          {data ? data.name_fa || data.name_en || data.code : t('manufacturing.detail.machineTitle')}
        </h1>
        <p className="page-header__subtitle">
          <Link to="/manufacturing/machines" className="link-back">
            {t('manufacturing.detail.back')}
          </Link>
        </p>
      </div>

      {loading && <Spinner />}
      {error && <Alert variant="danger" title={t('common.error')}>{error.message}</Alert>}

      {data && (
        <>
          <RecordDetail title={t('manufacturing.detail.machineTitle')} fields={fields} />
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