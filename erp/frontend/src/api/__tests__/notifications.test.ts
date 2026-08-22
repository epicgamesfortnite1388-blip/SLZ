import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ unread: 0 })),
    post: vi.fn(() => Promise.resolve({ updated: 0 })),
  },
}));

import { apiClient } from '../client';
import {
  markNotificationRead,
  markAllNotificationsRead,
  fetchUnreadCount,
} from '../notifications';

describe('notifications API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('marks a single notification read via the detail read endpoint', async () => {
    await markNotificationRead('n-1');
    expect(apiClient.post).toHaveBeenCalledWith('/notifications/n-1/read/', {});
  });

  it('marks all notifications read via the read-all endpoint', async () => {
    await markAllNotificationsRead();
    expect(apiClient.post).toHaveBeenCalledWith('/notifications/read-all/', {});
  });

  it('fetches the unread count via the unread-count endpoint', async () => {
    await fetchUnreadCount();
    expect(apiClient.get).toHaveBeenCalledWith('/notifications/unread-count/');
  });
});
