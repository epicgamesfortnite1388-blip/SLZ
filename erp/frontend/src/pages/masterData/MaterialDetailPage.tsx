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
import type { Material } from '@/api/masterData';

const ENTITY_TYPE = 'catalog.Material';

export function MaterialDetailPage(): JSX.Element {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const { hasPermission } = useAuth();
  const { data, loading, error } = useRecord<Material>(
    id ? `/catalog/materials/${id}/` : null,
  );

  const dash = (value: string | number | null): string =>
    value == null || value === '' ? '—' : String(value);

  const fields: DetailField[] = data
    ? [
        { labelKey: 'masterData.fields.code', value: data.code },
        { labelKey: 'masterData.fields.nameFa', value: dash(data.name_fa) },
        { labelKey: 'masterData.fields.nameEn', value: dash(data.name_en) },
        {
          labelKey: 'materials.subtype',
          value: t(`materials.subtypes.${data.subtype}`, { defaultValue: data.subtype }),
        },
        { labelKey: 'masterData.fields.baseUom', value: data.base_uom },
        { labelKey: 'materials.hazardous', value: <BoolCell value={data.is_hazardous} /> },
        { labelKey: 'materials.msdsRef', value: dash(data.msds_ref) },
        { labelKey: 'materials.leadTimeDays', value: dash(data.lead_time_days) },
        { labelKey: 'materials.shelfLifeDays', value: dash(data.shelf_life_days) },
        { labelKey: 'materials.reorderPoint', value: dash(data.reorder_point) },
        { labelKey: 'materials.safetyStock', value: dash(data.safety_stock) },
        { labelKey: 'materials.minStock', value: dash(data.min_stock) },
        { labelKey: 'materials.maxStock', value: dash(data.max_stock) },
        { labelKey: 'materials.createdAt', value: formatDateTime(data.created_at, i18n.language) },
        { labelKey: 'masterData.fields.active', value: <BoolCell value={data.is_active} /> },
      ]
    : [];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">
          {data ? data.name_fa || data.name_en || data.code : t('materials.detail.title')}
        </h1>
        <p className="page-header__subtitle">
          <Link to="/master-data/materials" className="link-back">
            {t('materials.detail.back')}
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
          <RecordDetail title={t('materials.detail.title')} fields={fields} />
          {hasPermission('documents.attachment.view') && id && (
            <AttachmentPanel entityType={ENTITY_TYPE} entityId={id} />
          )}
          <AuditHistoryPanel entityType={ENTITY_TYPE} entityId={id ?? ''} />
        </>
      )}

      {!loading && !error && !data && (
        <Card>
          <div className="stat-card__note">{t('materials.detail.notFound')}</div>
        </Card>
      )}
    </div>
  );
}