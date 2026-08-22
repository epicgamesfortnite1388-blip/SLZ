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
import type { Product } from '@/api/masterData';

const ENTITY_TYPE = 'catalog.Product';

export function ProductsDetailPage(): JSX.Element {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const { hasPermission } = useAuth();
  const { data, loading, error } = useRecord<Product>(
    id ? `/catalog/products/${id}/` : null,
  );

  const dash = (value: string | null): string => value || '—';

  const fields: DetailField[] = data
    ? [
        { labelKey: 'masterData.fields.code', value: dash(data.code) },
        { labelKey: 'masterData.fields.nameFa', value: dash(data.name_fa) },
        { labelKey: 'masterData.fields.nameEn', value: dash(data.name_en) },
        { labelKey: 'engineering.fields.productGroup', value: data.product_group ?? '—' },
        { labelKey: 'engineering.fields.family', value: data.family ?? '—' },
        { labelKey: 'masterData.fields.baseUom', value: data.base_uom },
        { labelKey: 'products.createdAt', value: formatDateTime(data.created_at, i18n.language) },
        { labelKey: 'masterData.fields.active', value: <BoolCell value={data.is_active} /> },
      ]
    : [];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">
          {data ? data.name_fa || data.name_en || data.code || t('products.detail.title') : t('products.detail.title')}
        </h1>
        <p className="page-header__subtitle">
          <Link to="/master-data/products" className="link-back">
            {t('products.detail.back')}
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
          <RecordDetail title={t('products.detail.title')} fields={fields} />
          {hasPermission('documents.attachment.view') && id && (
            <AttachmentPanel entityType={ENTITY_TYPE} entityId={id} />
          )}
          <AuditHistoryPanel entityType={ENTITY_TYPE} entityId={id ?? ''} />
        </>
      )}

      {!loading && !error && !data && (
        <Card>
          <div className="stat-card__note">{t('products.detail.notFound')}</div>
        </Card>
      )}
    </div>
  );
}