import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the lowest layer (apiClient.get) so we assert the exact URL that
// fetchCount -> fetchCollection builds, and that only `count` is returned.
vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() =>
      Promise.resolve({
        count: 42,
        total_pages: 42,
        page: 1,
        page_size: 1,
        next: null,
        previous: null,
        results: [{ id: 'x' }],
      }),
    ),
  },
}));

import { apiClient } from '../client';
import { fetchCount, fetchStatusSummary } from '../dashboard';

describe('dashboard API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('requests the collection with page_size=1 and returns only the count', async () => {
    const n = await fetchCount('/partners/partners/');

    expect(n).toBe(42);
    expect(apiClient.get).toHaveBeenCalledTimes(1);
    const [url] = (apiClient.get as unknown as { mock: { calls: unknown[][] } }).mock.calls[0];
    expect(url).toBe('/partners/partners/?page_size=1');
  });

  it('does not add page or search params', async () => {
    await fetchCount('/catalog/products/');

    const [url] = (apiClient.get as unknown as { mock: { calls: unknown[][] } }).mock.calls[0];
    expect(url).not.toContain('page=');
    expect(url).not.toContain('search=');
    expect(url).toBe('/catalog/products/?page_size=1');
  });

  it('fetchStatusSummary hits the summary endpoint and returns the breakdown', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      total: 7,
      by_status: { DRAFT: 4, CONFIRMED: 3, CLOSED: 0 },
    });

    const summary = await fetchStatusSummary('/sales/orders/');

    expect(apiClient.get).toHaveBeenCalledWith('/sales/orders/summary/');
    expect(summary.total).toBe(7);
    expect(summary.by_status.CONFIRMED).toBe(3);
  });
});
