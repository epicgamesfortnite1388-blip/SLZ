/**
 * Product Engineering (Task 005) API layer: typed entity shapes for the
 * versioned technical specification, plus the two write flows the UI exercises
 * (create a customer product; activate a draft specification revision).
 *
 * Types mirror the backend DRF serializers in ``apps.engineering``. The
 * versioning lifecycle (draft → activate → supersede) is enforced server-side;
 * the UI only surfaces state and triggers the activate transition — it never
 * duplicates the rule.
 */
import { apiClient } from './client';
import type { Paginated } from './masterData';

/** Revision status, mirrors ``apps.core.versioning.RevisionStatus``. */
export type RevisionStatus = 'DRAFT' | 'ACTIVE' | 'SUPERSEDED' | 'ARCHIVED';

/** A customer product is the versioned ROOT that specifications hang off of. */
export interface CustomerProduct {
  id: string;
  company: string;
  customer: string;
  code: string;
  name_fa: string;
  name_en: string;
  product_group: string | null;
  family: string | null;
  base_uom: string;
  is_active: boolean;
}

/** One immutable-once-active revision of a customer product's spec. */
export interface SpecificationRevision {
  id: string;
  root: string;
  revision_number: number;
  status: RevisionStatus;
  effective_from: string | null;
  effective_to: string | null;
  change_reason: string;
  spec_format: string;
  bag_type: string;
  width_mm: string | null;
  width_tol_low: string | null;
  width_tol_high: string | null;
  length_mm: string | null;
  length_tol_low: string | null;
  length_tol_high: string | null;
  gusset_mm: string | null;
  print_process: string;
  number_of_colors: number;
  has_lamination: boolean;
  has_cold_seal: boolean;
  surface_finish: string;
}

/** Create a customer product (representative audited write path). */
export function createCustomerProduct(
  payload: Partial<CustomerProduct>,
): Promise<CustomerProduct> {
  return apiClient.post<CustomerProduct>('/engineering/customer-products/', payload);
}

/**
 * Activate a DRAFT specification revision. This supersedes the prior ACTIVE
 * revision of the same root and stamps effective dates — all server-side and
 * atomic. Returns the freshly-activated revision.
 */
export function activateSpecification(id: string): Promise<SpecificationRevision> {
  return apiClient.post<SpecificationRevision>(
    `/engineering/specifications/${id}/activate/`,
    {},
  );
}

/** Retrieve one customer product by id (detail-page header). */
export function fetchCustomerProduct(id: string): Promise<CustomerProduct> {
  return apiClient.get<CustomerProduct>(`/engineering/customer-products/${id}/`);
}

/** Retrieve one specification revision by id. */
export function fetchSpecification(id: string): Promise<SpecificationRevision> {
  return apiClient.get<SpecificationRevision>(`/engineering/specifications/${id}/`);
}

/**
 * All revisions of one specification root, newest first — the version history
 * of the product's technical spec (backend filters `?root=<id>`).
 */
export async function listSpecificationRevisions(
  rootId: string,
): Promise<SpecificationRevision[]> {
  const page = await apiClient.get<Paginated<SpecificationRevision>>(
    `/engineering/specifications/?root=${encodeURIComponent(rootId)}&page_size=100`,
  );
  return [...page.results].sort((a, b) => b.revision_number - a.revision_number);
}

/** One film/structure layer of a revision (mirrors ``SpecLayerSerializer``). */
export interface SpecLayer {
  id: string;
  revision: string;
  sequence: number;
  material: string;
  function: string;
  micron: string | null;
  micron_tol_low: string | null;
  micron_tol_high: string | null;
}

/** One printed color of a revision (mirrors ``SpecColorSerializer``). */
export interface SpecColor {
  id: string;
  revision: string;
  sequence: number;
  color_name: string;
  ink: string | null;
  alternative_ink: string | null;
  coverage_pct: string | null;
  delta_e_tol: string | null;
}

/** One free-form technical parameter of a revision (mirrors ``SpecParameterSerializer``). */
export interface SpecParameter {
  id: string;
  revision: string;
  key: string;
  datatype: string;
  value_text: string;
  value_number: string | null;
  value_bool: boolean | null;
  unit: string;
  tol_low: string | null;
  tol_high: string | null;
}

/** Layers of one revision (`?revision=<id>`, ordered by sequence). */
export async function listSpecLayers(revisionId: string): Promise<SpecLayer[]> {
  const page = await apiClient.get<Paginated<SpecLayer>>(
    `/engineering/spec-layers/?revision=${encodeURIComponent(revisionId)}&page_size=100`,
  );
  return [...page.results].sort((a, b) => a.sequence - b.sequence);
}

/** Printed colors of one revision (`?revision=<id>`, ordered by sequence). */
export async function listSpecColors(revisionId: string): Promise<SpecColor[]> {
  const page = await apiClient.get<Paginated<SpecColor>>(
    `/engineering/spec-colors/?revision=${encodeURIComponent(revisionId)}&page_size=100`,
  );
  return [...page.results].sort((a, b) => a.sequence - b.sequence);
}

/** Parameters of one revision (`?revision=<id>`, ordered by key for stable display). */
export async function listSpecParameters(revisionId: string): Promise<SpecParameter[]> {
  const page = await apiClient.get<Paginated<SpecParameter>>(
    `/engineering/spec-parameters/?revision=${encodeURIComponent(revisionId)}&page_size=100`,
  );
  return [...page.results].sort((a, b) => a.key.localeCompare(b.key));
}
