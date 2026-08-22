import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ id: 'a-1' })),
  },
}));

import { apiClient } from '../client';
import { fetchAuditEntry, fetchEntityHistory } from '../audit';

describe('audit API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('retrieves a single audit entry from the logs detail endpoint', async () => {
    await fetchAuditEntry('a-1');
    expect(apiClient.get).toHaveBeenCalledWith('/audit/logs/a-1/');
  });

  it('filters the trail to one record for in-context history', async () => {
    await fetchEntityHistory('sales.SalesOrder', 'so-9');

    expect(apiClient.get).toHaveBeenCalledWith(
      '/audit/logs/?entity_type=sales.SalesOrder&entity_id=so-9&page_size=20',
    );
  });
});
