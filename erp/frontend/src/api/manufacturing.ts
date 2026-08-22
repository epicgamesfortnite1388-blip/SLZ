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
import type { Paginated } from './masterData';
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
  created_at: string;
  updated_at: string;
}

/** Fetch one work center by id. */
export function fetchWorkCenter(id: string): Promise<WorkCenter> {
  return apiClient.get<WorkCenter>(`/manufacturing/work-centers/${id}/`);
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
  created_at: string;
  updated_at: string;
}

/** Fetch one machine by id. */
export function fetchMachine(id: string): Promise<Machine> {
  return apiClient.get<Machine>(`/manufacturing/machines/${id}/`);
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

/** Create a machine (audited write path). */
export function createMachine(
  payload: Partial<Machine>,
): Promise<Machine> {
  return apiClient.post<Machine>('/manufacturing/machines/', payload);
}

/** A BOM root — the durable identity of a versioned bill of materials. */
export interface BillOfMaterials {
  id: string;
  spec_revision: string;
  output_material: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Create a BOM root (audited write path). */
export function createBomRoot(
  payload: Partial<BillOfMaterials>,
): Promise<BillOfMaterials> {
  return apiClient.post<BillOfMaterials>('/manufacturing/boms/', payload);
}

/** A routing root — the durable identity of a versioned set of operations. */
export interface Routing {
  id: string;
  spec_revision: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Create a routing root (audited write path). */
export function createRoutingRoot(
  payload: Partial<Routing>,
): Promise<Routing> {
  return apiClient.post<Routing>('/manufacturing/routings/', payload);
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

/** Retrieve one BOM root by id. */
export function fetchBom(id: string): Promise<BillOfMaterials> {
  return apiClient.get<BillOfMaterials>(`/manufacturing/boms/${id}/`);
}

/**
 * All revisions of one BOM root, newest first — its version history
 * (backend filters `?root=<id>`).
 */
export async function listBomRevisions(rootId: string): Promise<StructureRevision[]> {
  const page = await apiClient.get<Paginated<StructureRevision>>(
    `/manufacturing/bom-revisions/?root=${encodeURIComponent(rootId)}&page_size=100`,
  );
  return [...page.results].sort((a, b) => b.revision_number - a.revision_number);
}

/** One consumed material of a BOM revision (mirrors ``BomLineSerializer``). */
export interface BomLine {
  id: string;
  revision: string;
  sequence: number;
  material: string;
  quantity_per_output: string;
  uom: string;
  /** Free text — the canonical basis set is OPEN (Q-027). */
  consumption_basis: string;
  scrap_pct: string | null;
  notes: string;
}

/** Lines of one BOM revision (`?revision=<id>`, ordered by sequence). */
export async function listBomLines(revisionId: string): Promise<BomLine[]> {
  const page = await apiClient.get<Paginated<BomLine>>(
    `/manufacturing/bom-lines/?revision=${encodeURIComponent(revisionId)}&page_size=100`,
  );
  return [...page.results].sort((a, b) => a.sequence - b.sequence);
}

/** Retrieve one routing root by id. */
export function fetchRouting(id: string): Promise<Routing> {
  return apiClient.get<Routing>(`/manufacturing/routings/${id}/`);
}

/** All revisions of one routing root, newest first. */
export async function listRoutingRevisions(rootId: string): Promise<StructureRevision[]> {
  const page = await apiClient.get<Paginated<StructureRevision>>(
    `/manufacturing/routing-revisions/?root=${encodeURIComponent(rootId)}&page_size=100`,
  );
  return [...page.results].sort((a, b) => b.revision_number - a.revision_number);
}

/** One operation of a routing revision (mirrors ``RoutingOperationSerializer``). */
export interface RoutingOperation {
  id: string;
  revision: string;
  sequence: number;
  work_center: string;
  operation_name: string;
  output_material: string | null;
  setup_time_minutes: string | null;
  run_rate: string | null;
  /** Free text — standard templates are OPEN (Q-029). */
  run_rate_basis: string;
  notes: string;
}

/** Operations of one routing revision (`?revision=<id>`, ordered by sequence). */
export async function listRoutingOperations(
  revisionId: string,
): Promise<RoutingOperation[]> {
  const page = await apiClient.get<Paginated<RoutingOperation>>(
    `/manufacturing/routing-operations/?revision=${encodeURIComponent(revisionId)}&page_size=100`,
  );
  return [...page.results].sort((a, b) => a.sequence - b.sequence);
}
