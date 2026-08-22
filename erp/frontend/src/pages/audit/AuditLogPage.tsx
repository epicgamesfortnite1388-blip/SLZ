import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import { formatDateTime } from '@/i18n/dates';
import type { AuditLogEntry } from '@/api/audit';
import { AuditEntryDetail } from './AuditEntryDetail';

/**
 * Read-only audit trail viewer. The audit log is append-only — this page never
 * mutates it. Access is gated by `audit.log.view` at the route. The search box
 * maps to the backend `search_fields` (entity_type, entity_id, actor_label), so
 * an operator can trace every action on a given record. Clicking a row opens
 * the entry detail (who / what / when plus the before → after state diff).
 */
export function AuditLogPage(): JSX.Element {
  const { t, i18n } = useTranslation();
  const collection = useCollection<AuditLogEntry>('/audit/logs/');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Locale-neutral, dependency-free timestamp trim: "2026-08-21 19:47:38".
  const when = (iso: string): string => formatDateTime(iso, i18n.language);

  const columns: Column<AuditLogEntry>[] = [
    { headerKey: 'audit.fields.timestamp', render: (r) => when(r.timestamp) },
    { headerKey: 'audit.fields.actor', render: (r) => r.actor_label || '—' },
    {
      headerKey: 'audit.fields.action',
      render: (r) => t(`audit.actions.${r.action}`),
    },
    {
      headerKey: 'audit.fields.entity',
      render: (r) => `${r.entity_type} #${r.entity_id}`,
    },
    {
      headerKey: 'audit.fields.correlation',
      render: (r) => r.correlation_id || '—',
    },
  ];

  return (
    <>
      <CollectionView
        titleKey="audit.title"
        subtitleKey="audit.subtitle"
        columns={columns}
        rowKey={(r) => r.id}
        collection={collection}
        onRowClick={(r) => setSelectedId(r.id)}
      />
      <AuditEntryDetail entryId={selectedId} onClose={() => setSelectedId(null)} />
    </>
  );
}
