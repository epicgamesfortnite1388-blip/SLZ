/**
 * Quality (Task 008) API layer: typed entity shapes for the CONFIRMED
 * definition slice — the company-scoped QualityCharacteristic catalogue and the
 * versioned QualityPlan (bound to a specification revision) with its immutable
 * revisions and plan items.
 *
 * Types mirror the backend DRF serializers in ``apps.quality``. NO check
 * execution / result / NCR / QC_HOLD / scrap / COA shape is declared here
 * because that append-only, traceability-bound layer is gated (Q-046 roll
 * serialization and related open decisions) and is not implemented server-side.
 * The versioning lifecycle (draft → activate → supersede) is enforced
 * server-side; the UI only surfaces state and triggers the activate transition.
 */
import { apiClient } from './client';
import type { RevisionStatus } from './engineering';

export type { RevisionStatus };

/** How a characteristic is measured (generic; the concrete method is data). */
export type CharacteristicDatatype = 'NUMBER' | 'TEXT' | 'BOOL';

/** Ordered list of datatypes for select inputs (labels come from i18n). */
export const CHARACTERISTIC_DATATYPES: CharacteristicDatatype[] = [
  'NUMBER',
  'TEXT',
  'BOOL',
];

/** A measurable quality attribute in the company catalogue. */
export interface QualityCharacteristic {
  id: string;
  company: string;
  code: string;
  name_fa: string;
  name_en: string;
  datatype: CharacteristicDatatype;
  method: string;
  default_uom: string | null;
  is_active: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
}

/** A versioned quality plan root, bound to one specification revision. */
export interface QualityPlan {
  id: string;
  spec_revision: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** One immutable-once-active quality plan revision. */
export interface QualityPlanRevision {
  id: string;
  root: string;
  revision_number: number;
  status: RevisionStatus;
  effective_from: string | null;
  effective_to: string | null;
  change_reason: string;
}

/** Create a quality characteristic (representative audited write path). */
export function createQualityCharacteristic(
  payload: Partial<QualityCharacteristic>,
): Promise<QualityCharacteristic> {
  return apiClient.post<QualityCharacteristic>(
    '/quality/characteristics/',
    payload,
  );
}

/** Activate a DRAFT quality-plan revision (supersedes the prior ACTIVE one). */
export function activateQualityPlanRevision(
  id: string,
): Promise<QualityPlanRevision> {
  return apiClient.post<QualityPlanRevision>(
    `/quality/plan-revisions/${id}/activate/`,
    {},
  );
}

/** Create a quality plan root (audited write path). */
export function createQualityPlan(
  payload: Partial<QualityPlan>,
): Promise<QualityPlan> {
  return apiClient.post<QualityPlan>('/quality/plans/', payload);
}
