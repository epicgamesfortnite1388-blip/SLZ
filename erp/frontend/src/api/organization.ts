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
