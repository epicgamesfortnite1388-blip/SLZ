/**
 * Notifications API layer.
 *
 * The in-app notification channel is the confirmed default; email / SMS / push
 * are deferred interfaces (DR-008, do-not-build-yet #30) and are not surfaced
 * here. The backend viewset is self-authorizing — every endpoint scopes to the
 * requesting user — so no module permission is required to read or clear one's
 * own notifications.
 */
import { apiClient } from './client';

/** Event taxonomy (mirrors ``NotificationType``). */
export type NotificationType =
  | 'APPROVAL_REQUIRED'
  | 'APPROVAL_COMPLETED'
  | 'TASK_ASSIGNED'
  | 'STATUS_CHANGED'
  | 'DEADLINE_APPROACHING'
  | 'SYSTEM_ALERT';

/** One in-app notification addressed to the current user. */
export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  entity_type: string;
  entity_id: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

/** Mark a single notification read. */
export function markNotificationRead(id: string): Promise<Notification> {
  return apiClient.post<Notification>(`/notifications/${id}/read/`, {});
}

/** Mark every unread notification read; returns how many were updated. */
export function markAllNotificationsRead(): Promise<{ updated: number }> {
  return apiClient.post<{ updated: number }>('/notifications/read-all/', {});
}

/** Current unread count (for the header badge). */
export function fetchUnreadCount(): Promise<{ unread: number }> {
  return apiClient.get<{ unread: number }>('/notifications/unread-count/');
}
