/**
 * Organization structural master (Company → Site) API layer.
 *
 * These are the roots of the platform's company/site scoping (DR-040): almost
 * every business entity references a `company`, and sites carry timezone and
 * production-capability context. The backend viewsets route writes through the
 * audited service layer (`apps.core.service`), so a create here lands in the
 * audit trail exactly like any other master-data write. Types mirror the DRF
 * serializers in `apps.organization`.
 */
import { apiClient } from './client';

/** A legal entity / company — the top of the organization tree. */
export interface Company {
  id: string;
  code: string;
  name_en: string;
  name_fa: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** A physical facility / plant belonging to a company. */
export interface Site {
  id: string;
  company: string;
  code: string;
  name_en: string;
  name_fa: string;
  timezone: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Create a company (audited write path; `code` is unique). */
export function createCompany(payload: Partial<Company>): Promise<Company> {
  return apiClient.post<Company>('/organization/companies/', payload);
}

/** Create a site (audited write path; `code` is unique per company). */
export function createSite(payload: Partial<Site>): Promise<Site> {
  return apiClient.post<Site>('/organization/sites/', payload);
}

/** A site-scoped department (mirrors ``DepartmentSerializer``). */
export interface Department {
  id: string;
  site: string;
  code: string;
  name_en: string;
  name_fa: string;
  parent: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Create a department (audited write path). */
export function createDepartment(
  payload: Partial<Department>,
): Promise<Department> {
  return apiClient.post<Department>('/organization/departments/', payload);
}

/** Production capability codes (mirrors ``ProductionCapability``). */
export type ProductionCapability =
  | 'FILM_BLOWING'
  | 'PRINTING'
  | 'LAMINATION'
  | 'SLITTING'
  | 'CONVERTING'
  | 'RECYCLING_GRINDING'
  | 'CUTTING_SEWING'
  | 'WAREHOUSING';

/** Ordered list of capability choices for select inputs. */
export const PRODUCTION_CAPABILITIES: ProductionCapability[] = [
  'FILM_BLOWING',
  'PRINTING',
  'LAMINATION',
  'SLITTING',
  'CONVERTING',
  'RECYCLING_GRINDING',
  'CUTTING_SEWING',
  'WAREHOUSING',
];

/** A production-capability declaration scoped to a site (mirrors ``SiteCapabilitySerializer``). */
export interface SiteCapability {
  id: string;
  site: string;
  capability: ProductionCapability;
  is_active: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
}

/** Create a site capability (audited write path). */
export function createSiteCapability(
  payload: Partial<SiteCapability>,
): Promise<SiteCapability> {
  return apiClient.post<SiteCapability>(
    '/organization/site-capabilities/',
    payload,
  );
}
