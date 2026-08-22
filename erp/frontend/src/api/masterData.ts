/**
 * Master-data (Task 004) API layer: typed entity shapes plus a thin,
 * paginated collection fetcher built on {@link apiClient}.
 *
 * These types mirror the backend DRF serializers exactly. Screens are
 * read-oriented (browse); the only write flow wired here is Partner create,
 * which exercises the full audited service path end-to-end.
 */
import { apiClient } from './client';

/** Standard paginated envelope returned by ``apps.core.pagination``. */
export interface Paginated<T> {
  count: number;
  total_pages: number;
  page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Partner {
  id: string;
  company: string;
  code: string;
  name_fa: string;
  name_en: string;
  legal_name: string;
  national_id: string;
  economic_code: string;
  is_customer: boolean;
  is_supplier: boolean;
  is_sanctioned: boolean;
  is_active: boolean;
  notes: string;
}

export interface Product {
  id: string;
  company: string;
  code: string;
  name_fa: string;
  name_en: string;
  product_group: string | null;
  family: string | null;
  base_uom: string;
  is_active: boolean;
}

export interface Material {
  id: string;
  company: string;
  code: string;
  name_fa: string;
  name_en: string;
  subtype: string;
  base_uom: string;
  is_hazardous: boolean;
  is_active: boolean;
}

export interface UnitOfMeasure {
  id: string;
  code: string;
  name_fa: string;
  name_en: string;
  dimension: string;
  is_active: boolean;
}

export interface Employee {
  id: string;
  company: string;
  employee_code: string;
  first_name_fa: string;
  last_name_fa: string;
  first_name_en: string;
  last_name_en: string;
  job_title: string;
  is_active: boolean;
}

export interface SiteCapability {
  id: string;
  site: string;
  capability: string;
  is_active: boolean;
  notes: string;
}

export interface CollectionQuery {
  page?: number;
  pageSize?: number;
  search?: string;
}

function toQueryString(params: CollectionQuery): string {
  const sp = new URLSearchParams();
  if (params.page) sp.set('page', String(params.page));
  if (params.pageSize) sp.set('page_size', String(params.pageSize));
  if (params.search && params.search.trim()) sp.set('search', params.search.trim());
  const qs = sp.toString();
  return qs ? `?${qs}` : '';
}

/** GET a paginated collection from a master-data endpoint (relative path). */
export function fetchCollection<T>(
  path: string,
  params: CollectionQuery = {},
): Promise<Paginated<T>> {
  return apiClient.get<Paginated<T>>(`${path}${toQueryString(params)}`);
}

/** Create a partner (representative audited write path). */
export function createPartner(payload: Partial<Partner>): Promise<Partner> {
  return apiClient.post<Partner>('/partners/partners/', payload);
}
