import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchEntityHistory, type AuditLogEntry } from '@/api/audit';
import { isApiError } from '@/api/types';
import { formatDateTime } from '@/i18n/dates';
import { Card, Spinner } from '@/components/ui';
import { useAuth } from '@/auth/AuthContext';
import { AuditEntryDetail } from '@/pages/audit/AuditEntryDetail';

interface AuditHistoryPanelProps {
  /** Backend entity label, e.g. `sales.SalesOrder`. */
  entityType: string;
  /** Target record id. */
  entityId: string;
}

/**
 * In-context history for a single record: the most recent entries of the
 * append-only audit trail filtered to (`entityType`, `entityId`). Clicking an
 * entry opens the same read-only before/after detail used by the audit viewer.
 *
 * The trail is read-only everywhere; this panel only consumes the existing
 * `audit.log.view`-gated endpoints. Rendered only when the signed-in user can
 * view the audit log — history is a compliance surface, not decoration.
 */
export function AuditHistoryPanel({ entityType, entityId }: AuditHistoryPanelProps): JSX.Element {
  const { t, i18n } = useTranslation();
  const { hasPermission } = useAuth();
  const [entries, setEntries] = useState<AuditLogEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setError(null);
    fetchEntityHistory(entityType, entityId)
      .then((page) => {
        if (active) setEntries(page.results);
      })
      .catch((err: unknown) => {
        if (active) {
          setEntries([]);
          setError(isApiError(err) ? err.message : t('common.error'));
        }
      });
    return () => {
      active = false;
    };
  }, [entityType, entityId, t]);

  if (!hasPermission('audit.log.view')) return <></>;

  // Locale-neutral timestamp trim, matching the audit viewer list.
  const when = (iso: string): string => formatDateTime(iso, i18n.language);

  return (
    <>
      <Card title={t('audit.history.title')}>
        {error && <p>{error}</p>}
        {!error && entries === null && (
          <div className="table-state">
            <Spinner label={t('common.loading')} />
          </div>
        )}
        {!error && entries !== null && entries.length === 0 && (
          <p>{t('audit.history.empty')}</p>
        )}
        {!error && entries !== null && entries.length > 0 && (
          <ul className="history-list">
            {entries.map((entry) => (
              <li key={entry.id} className="history-list__item">
                <button
                  type="button"
                  className="link-inline history-list__open"
                  onClick={() => setSelectedId(entry.id)}
                >
                  {when(entry.timestamp)} — {t(`audit.actions.${entry.action}`)}
                  {entry.actor_label ? ` — ${entry.actor_label}` : ''}
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>
      <AuditEntryDetail entryId={selectedId} onClose={() => setSelectedId(null)} />
    </>
  );
}
