/**
 * Documents / attachments API layer.
 *
 * The backend attachment store is a **generic**, entity-keyed register: every
 * row is pinned to a target by (`entity_type`, `entity_id`) and carries the
 * file's provenance (original name, content type, size, SHA-256 checksum). It
 * encodes no business rule about *what* may be attached to *what* — that stays
 * with the owning module — so this layer is a thin, reusable surface over
 * `/documents/attachments/`.
 *
 * Downloads are authenticated: an anchor `href` cannot carry the Bearer token,
 * so {@link downloadAttachment} pulls the bytes via `apiClient.getBlob` and
 * hands the browser an object URL to save under the original filename.
 */
import { apiClient } from './client';
import type { Paginated } from './masterData';

/** One stored file, mirroring the backend ``AttachmentSerializer``. */
export interface Attachment {
  id: string;
  entity_type: string;
  entity_id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  checksum_sha256: string;
  description: string;
  /** Server-relative download path (auth still required to fetch it). */
  download_url: string;
  created_at: string;
  created_by: string | null;
}

/**
 * Upload a file against a target entity. Sends multipart form data; the browser
 * sets the boundary itself, so we never set `Content-Type` by hand.
 */
export function uploadAttachment(
  entityType: string,
  entityId: string,
  file: File,
  description = '',
): Promise<Attachment> {
  const form = new FormData();
  form.append('entity_type', entityType);
  form.append('entity_id', entityId);
  form.append('file', file);
  if (description) form.append('description', description);
  return apiClient.postForm<Attachment>('/documents/attachments/upload/', form);
}

/** Delete an attachment (soft delete server-side; requires delete permission). */
export function deleteAttachment(id: string): Promise<void> {
  return apiClient.delete<void>(`/documents/attachments/${id}/`);
}

/**
 * List the attachments pinned to one target entity, using the backend's
 * `entity_type` / `entity_id` filter. Returns the raw rows (detail panels show
 * every file for a record, so a generous page size avoids a second round-trip).
 */
export async function listAttachments(
  entityType: string,
  entityId: string,
): Promise<Attachment[]> {
  const params = new URLSearchParams({
    entity_type: entityType,
    entity_id: entityId,
    page_size: '200',
  });
  const page = await apiClient.get<Paginated<Attachment>>(
    `/documents/attachments/?${params.toString()}`,
  );
  return page.results;
}

/**
 * Fetch an attachment's bytes with the Bearer token and trigger a browser
 * download under the original filename. Resolves once the save has been
 * initiated. Throws {@link import('./types').ApiError} on a non-2xx response.
 */
export async function downloadAttachment(att: Attachment): Promise<void> {
  const blob = await apiClient.getBlob(
    `/documents/attachments/${att.id}/download/`,
  );
  const url = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = att.original_filename || 'download';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    // Release the object URL on the next tick so the click has been handled.
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
}

/** Human-readable byte size (e.g. `1.4 MB`). */
export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const exponent = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );
  const value = bytes / 1024 ** exponent;
  const rounded = exponent === 0 ? value : Math.round(value * 10) / 10;
  return `${rounded} ${units[exponent]}`;
}
