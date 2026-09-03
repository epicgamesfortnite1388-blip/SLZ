/**
 * Recall (Task 015) API layer: recall records, affected traceability units,
 * status transitions, and the read-only exposure computation.
 *
 * Creating a recall NEVER mutates inventory/shipments: exposure is computed on
 * demand from the genealogy + shipment records via ``/recalls/{id}/exposure/``.
 */
import { apiClient } from './client';
import type { Paginated } from './masterData';

export type RecallStatus =
  | 'DRAFT'
  | 'OPEN'
  | 'INVESTIGATING'
  | 'ACTION_REQUIRED'
  | 'CLOSED'
  | 'CANCELLED';

export type RecallSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Recall {
  id: string;
  company: string;
  code: string;
  reason: string;
  severity: RecallSeverity;
  severity_label: string;
  status: RecallStatus;
  status_label: string;
  initiated_at: string | null;
  initiated_by: string | null;
  notes: string;
  affected_count: number;
  created_at: string;
  updated_at: string;
}

export interface RecallPayload {
  company: string;
  code: string;
  reason: string;
  severity?: RecallSeverity;
  notes?: string;
}

export interface AffectedUnit {
  id: string;
  recall: string;
  traceability_unit: string;
  unit_identifier: string;
  unit_type: string;
  unit_company: string;
  note: string;
  created_at: string;
}

export interface AffectedUnitPayload {
  recall: string;
  traceability_unit: string;
  note?: string;
}

export interface ExposureUnit {
  id: string;
  identifier: string;
  unit_type: string;
  material_id: string | null;
  customer_product_id: string | null;
}

export interface Exposure {
  seed_units: number;
  upstream_units: number;
  downstream_units: number;
  affected_units: ExposureUnit[];
  production_orders: { id: string; number: string; status: string }[];
  shipments: { id: string; number: string; shipped_at: string; customer_id: string }[];
  customers: { id: string; name_fa: string; name_en: string; code: string }[];
}

export function createRecall(payload: RecallPayload): Promise<Recall> {
  return apiClient.post<Recall>('/recall/recalls/', payload);
}

export function fetchRecall(id: string): Promise<Recall> {
  return apiClient.get<Recall>(`/recall/recalls/${id}/`);
}

/** Affected traceability units of one recall (newest last via default order). */
export function fetchRecallAffectedUnits(
  recallId: string,
): Promise<Paginated<AffectedUnit>> {
  return apiClient.get<Paginated<AffectedUnit>>(
    `/recall/affected-units/?recall=${encodeURIComponent(recallId)}&page_size=100`,
  );
}

export function transitionRecall(id: string, status: RecallStatus): Promise<Recall> {
  return apiClient.post<Recall>(`/recall/recalls/${id}/transition/`, { status });
}

export function fetchRecallExposure(id: string): Promise<Exposure> {
  return apiClient.get<Exposure>(`/recall/recalls/${id}/exposure/`);
}

export function addAffectedUnit(payload: AffectedUnitPayload): Promise<AffectedUnit> {
  return apiClient.post<AffectedUnit>('/recall/affected-units/', payload);
}
