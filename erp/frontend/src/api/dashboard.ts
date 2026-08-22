/**
 * Dashboard API layer.
 *
 * The dashboard shows **live record counts** for the modules a user can see.
 * Every list endpoint returns the standard paginated envelope, so a single
 * `page_size=1` request is enough to read the authoritative `count` without
 * transferring any rows. No metric is fabricated: each number comes straight
 * from an existing, permission-gated endpoint.
 */
import { apiClient } from './client';
import { fetchCollection } from './masterData';

/** Fetch just the total record count for a collection endpoint. */
export async function fetchCount(path: string): Promise<number> {
  const page = await fetchCollection<unknown>(path, { pageSize: 1 });
  return page.count;
}

/**
 * Per-status document counts from a module's `summary/` endpoint (e.g.
 * `/sales/orders/summary/`). The server aggregates the same filtered,
 * permission-gated queryset as the list and zero-fills every declared status,
 * so this is a pure order-book breakdown — no metric is invented client-side.
 */
export interface StatusSummary {
  total: number;
  by_status: Record<string, number>;
}

export async function fetchStatusSummary(path: string): Promise<StatusSummary> {
  return apiClient.get<StatusSummary>(`${path}summary/`);
}
