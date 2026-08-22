import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Alert, Card, Spinner } from '@/components/ui';
import { BoolCell } from '@/components/CollectionView';
import { RecordDetail, type DetailField } from '@/components/RecordDetail';
import { AttachmentPanel } from '@/components/AttachmentPanel';
import { AuditHistoryPanel } from '@/components/AuditHistoryPanel';
import { PartnerAddressesPanel, PartnerContactsPanel } from './PartnerSubPanels';
import { useRecord } from '@/hooks/useRecord';
import type { Partner } from '@/api/masterData';

/** Backend entity label used to pin attachments to a partner record. */
const ENTITY_TYPE = 'partners.Partner';

/**
 * Read-only detail view for a single partner. Surfaces the fields already
 * returned by the existing retrieve endpoint (no new data, no business rule) and
 * embeds the reusable attachment panel so files can be managed in context. This
 * is the reference implementation of the generic detail-view + attachment
 * pattern; other modules can follow it verbatim.
 */
export function PartnerDetailPage(): JSX.Element {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const { hasPermission } = useAuth();
  const { data, loading, error } = useRecord<Partner>(
    id ? `/partners/partners/${id}/` : null,
  );

  const dash = (value: string): string => value || '—';

  const roles: string[] = [];
  if (data?.is_customer) roles.push(t('partners.role.customer'));
  if (data?.is_supplier) roles.push(t('partners.role.supplier'));

  const fields: DetailField[] = data
    ? [
        { labelKey: 'masterData.fields.code', value: data.code },
        { labelKey: 'masterData.fields.nameFa', value: dash(data.name_fa) },
        { labelKey: 'masterData.fields.nameEn', value: dash(data.name_en) },
        { labelKey: 'partners.fields.legalName', value: dash(data.legal_name) },
        { labelKey: 'partners.fields.nationalId', value: dash(data.national_id) },
        { labelKey: 'partners.fields.economicCode', value: dash(data.economic_code) },
        { labelKey: 'partners.roles', value: roles.join(' / ') || '—' },
        { labelKey: 'partners.sanctioned', value: <BoolCell value={data.is_sanctioned} /> },
        { labelKey: 'masterData.fields.active', value: <BoolCell value={data.is_active} /> },
        { labelKey: 'partners.fields.notes', value: dash(data.notes) },
      ]
    : [];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">
          {data ? data.name_fa || data.name_en || data.code : t('partners.detail.title')}
        </h1>
        <p className="page-header__subtitle">
          <Link to="/master-data/partners" className="link-back">
            {t('partners.detail.back')}
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
          <RecordDetail title={t('partners.detail.title')} fields={fields} />
          {hasPermission('documents.attachment.view') && id && (
            <AttachmentPanel entityType={ENTITY_TYPE} entityId={id} />
          )}

          {(hasPermission('partners.contact.view') || hasPermission('partners.contact.manage')) && id && (
            <PartnerContactsPanel partnerId={id} />
          )}
          {(hasPermission('partners.address.view') || hasPermission('partners.address.manage')) && id && (
            <PartnerAddressesPanel partnerId={id} />
          )}

          <AuditHistoryPanel entityType={ENTITY_TYPE} entityId={id ?? ''} />
        </>
      )}

      {!loading && !error && !data && (
        <Card>
          <div className="stat-card__note">{t('partners.detail.notFound')}</div>
        </Card>
      )}
    </div>
  );
}
