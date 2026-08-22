/**
 * Manufacturing (Task 006) API layer: typed entity shapes for the master
 * resources (work centers, machines) and the two versioned engineering
 * structures — Bill of Materials and Routing — bound to a specification
 * revision.
 *
 * Types mirror the backend DRF serializers in ``apps.manufacturing``. The
 * versioning lifecycle (draft → activate → supersede) is enforced server-side
 * and is IDENTICAL for BOM and Routing revisions; the UI only surfaces state
 * and triggers the activate transition — it never duplicates the rule.
 */
import { apiClient } from './client';
import type { RevisionStatus } from './engineering';

export type { RevisionStatus };

/** A logical production stage grouping interchangeable machines. */
export interface WorkCenter {
  id: string;
  company: string;
  site: string | null;
  code: string;
  name_fa: string;
  name_en: string;
  sequence_hint: number;
  is_active: boolean;
}

/** A physical resource; ``capability_profile`` is free-form data (no code). */
export interface Machine {
  id: string;
  company: string;
  site: string | null;
  work_center: string;
  code: string;
  name_fa: string;
  name_en: string;
  capability_profile: Record<string, unknown>;
  is_active: boolean;
}

/** One immutable-once-active revision (shared shape for BOM and Routing). */
export interface StructureRevision {
  id: string;
  root: string;
  revision_number: number;
  status: RevisionStatus;
  effective_from: string | null;
  effective_to: string | null;
  change_reason: string;
}

/** Create a work center (representative audited write path). */
export function createWorkCenter(
  payload: Partial<WorkCenter>,
): Promise<WorkCenter> {
  return apiClient.post<WorkCenter>('/manufacturing/work-centers/', payload);
}

/** Activate a DRAFT BOM revision (supersedes the prior ACTIVE one, atomic). */
export function activateBomRevision(id: string): Promise<StructureRevision> {
  return apiClient.post<StructureRevision>(
    `/manufacturing/bom-revisions/${id}/activate/`,
    {},
  );
}

/** Activate a DRAFT routing revision (supersedes the prior ACTIVE one, atomic). */
export function activateRoutingRevision(id: string): Promise<StructureRevision> {
  return apiClient.post<StructureRevision>(
    `/manufacturing/routing-revisions/${id}/activate/`,
    {},
  );
}
