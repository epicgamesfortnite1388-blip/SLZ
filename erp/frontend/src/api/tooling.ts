/**
 * Engineering tooling (SR-03) API layer: typed shapes for the **cliché / sheet
 * / set** printing-tooling asset and its lifecycle endpoints.
 *
 * Mirrors the backend DRF serializer in ``apps.engineering``. This is the
 * CONFIRMED identity + usage-life slice only: there is NO tooling cost model
 * (OPEN, Q-004/036) and no automatic usage capture (gated Q-046). ``status`` is
 * managed server-side through the retire/reactivate actions.
 */
import { apiClient } from './client';
import type { Paginated } from './masterData';

/** Tooling grain (mirrors ``ToolingType``). */
export type ToolingType = 'CLICHE' | 'SHEET' | 'SET';

/** Tooling lifecycle (mirrors ``ToolingStatus``). */
export type ToolingStatus = 'ACTIVE' | 'RETIRED';

/** A cliché / sheet / set printing-tooling asset with usage-life counters. */
export interface ToolingAsset {
  id: string;
  company: string;
  customer: string;
  customer_product: string | null;
  code: string;
  name_fa: string;
  name_en: string;
  tooling_type: ToolingType;
  status: ToolingStatus;
  usage_life_limit: number | null;
  usage_count: number;
  warehouse: string | null;
  notes: string;
  is_life_exceeded: boolean;
  created_at: string;
  updated_at: string;
}

/** Create a tooling asset (audited write path; starts ACTIVE). */
export function createToolingAsset(
  payload: Partial<ToolingAsset>,
): Promise<ToolingAsset> {
  return apiClient.post<ToolingAsset>('/engineering/tooling-assets/', payload);
}

/** Tooling assets linked to one customer product (`?customer_product=<id>`). */
export async function listToolingAssetsByCustomerProduct(
  productId: string,
): Promise<ToolingAsset[]> {
  const page = await apiClient.get<Paginated<ToolingAsset>>(
    `/engineering/tooling-assets/?customer_product=${encodeURIComponent(productId)}&page_size=100`,
  );
  return page.results;
}

/** Tooling status transition by action name (server enforces legality). */
export function transitionToolingAsset(
  id: string,
  action: 'retire' | 'reactivate',
): Promise<ToolingAsset> {
  return apiClient.post<ToolingAsset>(
    `/engineering/tooling-assets/${id}/${action}/`,
    {},
  );
}
