/**
 * Costing API layer — dated weighted-average cost layers.
 */
import { apiClient } from './client';
import type { Paginated } from './inventory';

export type CostLayerType = 'RECEIPT' | 'ISSUE' | 'PRODUCTION_OUTPUT' | 'ADJUSTMENT';

export interface CostLayer {
  id: string;
  company: string;
  material: string;
  date: string;
  quantity: string;
  unit_cost: string;
  total_cost: string;
  layer_type: CostLayerType;
  reference_type: string;
  reference_id: string | null;
  po_line_id: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface WaCostResponse {
  material_id: string;
  wa_unit_cost: string;
  as_of: string | null;
}

export interface CostSummaryItem {
  material_id: string;
  wa_unit_cost: string;
  on_hand_qty: string;
  on_hand_cost: string;
}

export function fetchCostLayers(query = '?page_size=100'): Promise<Paginated<CostLayer>> {
  return apiClient.get<Paginated<CostLayer>>(`/costing/cost-layers/${query}`);
}

export function fetchWaCost(materialId: string, asOf?: string): Promise<WaCostResponse> {
  const params = new URLSearchParams({ material: materialId });
  if (asOf) params.set('as_of', asOf);
  return apiClient.get<WaCostResponse>(`/costing/cost-layers/wa-cost/?${params.toString()}`);
}

export function fetchCostSummary(asOf?: string): Promise<CostSummaryItem[]> {
  const params = asOf ? `?as_of=${encodeURIComponent(asOf)}` : '';
  return apiClient.get<CostSummaryItem[]>(`/costing/cost-layers/summary/${params}`);
}