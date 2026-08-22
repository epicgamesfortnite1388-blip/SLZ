import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchAuditEntry, type AuditLogEntry } from '@/api/audit';
import { isApiError } from '@/api/types';
import { formatDateTime } from '@/i18n/dates';
import { Alert, Button, Card, Spinner } from '@/components/ui';

interface AuditEntryDetailProps {
  /** Entry to inspect, or null when the detail view is closed. */
  entryId: string | null;
  onClose: () => void;
}

interface DiffRow {
  field: string;
  before: string | null;
  after: string | null;
  changed: boolean;
}

/** JSON-stable rendering of one state value; null marks an absent side. */
function formatValue(state: Record<string, unknown> | null, field: string): string | null {
  if (!state || !(field in state)) return null;
  const value = state[field];
  if (typeof value === 'string') return value === '' ? "''" : value;
  return JSON.stringify(value);
}

/** Field-level before → after rows across the union of both state snapshots. */
function buildDiffRows(entry: AuditLogEntry): DiffRow[] {
  const before = entry.before_state ?? null;
  const after = entry.after_state ?? null;
  const fields = Array.from(
    new Set([...Object.keys(before ?? {}), ...Object.keys(after ?? {})]),
  ).sort();
  return fields.map((field) => {
    const b = formatValue(before, field);
    const a = formatValue(after, field);
    return { field, before: b, after: a, changed: b !== a };
  });
}

/**
 * Read-only detail of a single audit entry: who / what / when plus the
 * recorded state snapshots. Fetches through `fetchAuditEntry` (the same
 * `audit.log.view`-gated retrieve endpoint); nothing here can mutate the trail.
 */
export function AuditEntryDetail({ entryId, onClose }: AuditEntryDetailProps): JSX.Element | null {
  const { t, i18n } = useTranslation();
  const [entry, setEntry] = useState<AuditLogEntry | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setEntry(null);
    setError(null);
    if (!entryId) return;
    let active = true;
    fetchAuditEntry(entryId)
      .then((row) => {
        if (active) setEntry(row);
      })
      .catch((err: unknown) => {
        if (active) setError(isApiError(err) ? err.message : t('common.error'));
      });
    return () => {
      active = false;
    };
  }, [entryId, t]);

  if (!entryId) return null;

  // Locale-neutral timestamp trim, matching the list page.
  const when = entry ? formatDateTime(entry.timestamp, i18n.language) : "";
  const rows = entry ? buildDiffRows(entry) : [];

  return (
    <div className="modal-backdrop" onClick={onClose} role="presentation">
      {/* stopPropagation keeps clicks inside the dialog from dismissing it. */}
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={t('audit.detail.title')}
        onClick={(e) => e.stopPropagation()}
      >
        <Card title={t('audit.detail.title')}>
          {!entry && !error && (
            <div className="table-state">
              <Spinner label={t('common.loading')} />
            </div>
          )}
          {error && (
            <Alert variant="danger" title={t('common.error')}>
              <p>{error}</p>
              <Button variant="secondary" size="sm" onClick={onClose}>
                {t('common.close')}
              </Button>
            </Alert>
          )}
          {entry && (
            <div className="stack">
              <dl className="detail-grid">
                <div className="detail-grid__row">
                  <dt className="detail-grid__label">{t('audit.fields.timestamp')}</dt>
                  <dd className="detail-grid__value">{when}</dd>
                </div>
                <div className="detail-grid__row">
                  <dt className="detail-grid__label">{t('audit.fields.actor')}</dt>
                  <dd className="detail-grid__value">{entry.actor_label || '—'}</dd>
                </div>
                <div className="detail-grid__row">
                  <dt className="detail-grid__label">{t('audit.fields.action')}</dt>
                  <dd className="detail-grid__value">{t(`audit.actions.${entry.action}`)}</dd>
                </div>
                <div className="detail-grid__row">
                  <dt className="detail-grid__label">{t('audit.fields.entity')}</dt>
                  <dd className="detail-grid__value">
                    {entry.entity_type} #{entry.entity_id}
                  </dd>
                </div>
              </dl>

              {rows.length === 0 ? (
                <p>{t('audit.detail.empty')}</p>
              ) : (
                <div className="table-scroll">
                  <table className="data-table diff-table">
                    <thead>
                      <tr>
                        <th>{t('audit.detail.field')}</th>
                        <th>{t('audit.detail.before')}</th>
                        <th>{t('audit.detail.after')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((row) => (
                        <tr
                          key={row.field}
                          className={row.changed ? 'diff-table__row--changed' : undefined}
                        >
                          <td>{row.field}</td>
                          <td>{row.before ?? '—'}</td>
                          <td>{row.after ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="form-actions">
                <Button variant="secondary" size="sm" onClick={onClose}>
                  {t('common.close')}
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
