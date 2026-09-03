/**
 * Planning (Task 014) API layer: reorder policies + the read-only planning run.
 *
 * Types mirror the backend DRF serializers in ``apps.planning``. The engine
 * (``/planning/policies/run/``) only *suggests* replenishment — it never
 * creates purchase or production orders; humans review the rows and use the
 * existing order workflows.
 */
import { apiClient } from './client';

/** One reorder policy: exactly one of material / customer_product is set. */
export interface PlanningPolicy {
  id: string;
  company: string;
  warehouse: string;
  material: string | null;
  customer_product: string | null;
  item_code: string;
  item_name_fa: string;
  item_type: 'MATERIAL' | 'PRODUCT';
  reorder_point: string;
  target_level: string;
  safety_stock: string | null;
  preferred_supplier: string | null;
  lead_time_days: number | null;
  is_active: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface PlanningPolicyPayload {
  company: string;
  warehouse: string;
  material?: string | null;
  customer_product?: string | null;
  reorder_point: string;
  target_level: string;
  safety_stock?: string | null;
  preferred_supplier?: string | null;
  lead_time_days?: number | null;
  is_active?: boolean;
  notes?: string;
}

/** One suggestion row produced by the planning engine. */
export interface PlanningRow {
  policy_id: number;
  item_code: string;
  item_name_fa: string;
  item_type: 'MATERIAL' | 'PRODUCT';
  warehouse_id: string | null;
  on_hand: string;
  allocated: string;
  incoming_purchase: string;
  open_production: string;
  open_demand: string;
  projected: string;
  reorder_point: string;
  target_level: string;
  safety_stock: string | null;
  lead_time_days: number | null;
  suggested_qty: string;
  action: 'NONE' | 'PURCHASE' | 'MANUFACTURE';
  reason: string;
}

export interface PlanningRun {
  rows: PlanningRow[];
  summary: {
    total_policies: number;
    action_required: number;
    to_purchase: number;
    to_manufacture: number;
    low_stock_items: number;
  };
}

export function createPlanningPolicy(
  payload: PlanningPolicyPayload,
): Promise<PlanningPolicy> {
  return apiClient.post<PlanningPolicy>('/planning/policies/', payload);
}

/** Run the read-only engine for the active company (optional warehouse). */
export function runPlanning(warehouse?: string): Promise<PlanningRun> {
  const qs = warehouse ? `?warehouse=${encodeURIComponent(warehouse)}` : '';
  return apiClient.get<PlanningRun>(`/planning/policies/run/${qs}`);
}
