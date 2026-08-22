import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { fetchToolingAsset } from '@/api/tooling';
import { isApiError } from '@/api/types';
import { AttachmentPanel } from '@/components/AttachmentPanel';
import { AuditHistoryPanel } from '@/components/AuditHistoryPanel';
import { BoolCell } from '@/components/CollectionView';
import { RecordDetail, type DetailField } from '@/components/RecordDetail';
import { Alert, Button, Spinner } from '@/components/ui';
import { useAuth } from '@/auth/AuthContext';

/**
 * Detail of one tooling asset: identity, lifecycle status, usage-life counters
 * and audit history. The cost model (Q-004/036) and automatic usage capture
 * (Q-046) are gated — this page only presents the CONFIRMED identity slice.
 */
export function ToolingAssetDetailPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const { id = '' } = useParams();
  const [asset, setAsset] = useState<Awaited<ReturnType<typeof fetchToolingAsset>> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setError(null);
    fetchToolingAsset(id)
      .then((a) => {
        if (active) setAsset(a);
      })
      .catch((err: unknown) => {
        if (active) setError(isApiError(err) ? err.message : t('common.error'));
      });
    return () => {
      active = false;
    };
  }, [id, t]);

  if (error) {
    return (
      <div className="stack">
        <Alert variant="danger" title={t('common.error')}>
          <p>{error}</p>
          <Button variant="secondary" size="sm" onClick={() => window.history.back()}>
            {t('common.back')}
          </Button>
        </Alert>
      </div>
    );
  }

  if (!asset) {
    return (
      <div className="table-state">
        <Spinner label={t('common.loading')} />
      </div>
    );
  }

  const fields: DetailField[] = [
    { labelKey: 'tooling.fields.code', value: asset.code },
    { labelKey: 'tooling.fields.name', value: asset.name_fa },
    { labelKey: 'tooling.fields.type', value: t(`tooling.types.${asset.tooling_type}`) },
    { labelKey: 'tooling.fields.status', value: t(`tooling.statuses.${asset.status}`) },
    { labelKey: 'tooling.fields.customer', value: asset.customer },
    {
      labelKey: 'tooling.fields.customerProduct',
      value: asset.customer_product ?? '—',
    },
    { labelKey: 'tooling.fields.warehouse', value: asset.warehouse ?? '—' },
    { labelKey: 'tooling.fields.usage', value: `${asset.usage_count} / ${asset.usage_life_limit ?? '—'}` },
    { labelKey: 'tooling.fields.lifeExceeded', value: <BoolCell value={asset.is_life_exceeded} /> },
    { labelKey: 'tooling.fields.notes', value: asset.notes || '—' },
  ];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{asset.code}</h1>
        <p className="page-header__subtitle">{t('tooling.detail.subtitle')}</p>
      </div>

      <RecordDetail title={t('tooling.detail.headerTitle')} fields={fields} />

      <AuditHistoryPanel entityType="engineering.ToolingAsset" entityId={asset.id} />

      {hasPermission('documents.attachment.view') && (
        <AttachmentPanel entityType="engineering.ToolingAsset" entityId={asset.id} />
      )}

      <div className="form-actions">
        <a className="link-back" onClick={() => window.history.back()} href="#back">
          ← {t('common.back')}
        </a>
      </div>
    </div>
  );
}
