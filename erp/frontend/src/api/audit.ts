/**
 * Audit log API layer.
 *
 * The audit trail is append-only and read-only over the wire: the backend
 * (`apps.audit`) exposes list + retrieve only, gated by `audit.log.view`. Every
 * audited write across the platform lands here via the domain-event subscriber
 * or an explicit `record_audit` call, so this is the single compliance /
 * traceability surface — a foundation concern SLZ cares about deeply. No write
 * path exists (and none should): entries are never created or edited from the UI.
 */
import { apiClient } from './client';
import type { Paginated } from './masterData';

/** Mirrors `apps.audit.models.AuditAction`. */
export type AuditAction =
  | 'CREATE'
  | 'UPDATE'
  | 'DELETE'
  | 'APPROVE'
  | 'REJECT'
  | 'CANCEL'
  | 'LOGIN'
  | 'LOGOUT';

/** One immutable audit entry. Subject is referenced generically by type + id. */
export interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor: string | null;
  actor_label: string;
  action: AuditAction;
  entity_type: string;
  entity_id: string;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  correlation_id: string;
  metadata: Record<string, unknown>;
}

/**
 * Retrieve a single audit entry, including its full before/after JSON — used to
 * inspect exactly what changed. The list view (via `useCollection`) shows the
 * summary; this is the detail path.
 */
export function fetchAuditEntry(id: string): Promise<AuditLogEntry> {
  return apiClient.get<AuditLogEntry>(`/audit/logs/${id}/`);
}

/**
 * Recent history for ONE record: the trail filtered to its generic entity
 * reference (`entity_type` + `entity_id`). Powers the in-context history panel
 * on detail screens. Requires `audit.log.view`, like every audit read.
 */
export async function fetchEntityHistory(
  entityType: string,
  entityId: string,
  pageSize = 20,
): Promise<Paginated<AuditLogEntry>> {
  const qs = `entity_type=${encodeURIComponent(entityType)}&entity_id=${encodeURIComponent(entityId)}&page_size=${pageSize}`;
  return apiClient.get<Paginated<AuditLogEntry>>(`/audit/logs/?${qs}`);
}
