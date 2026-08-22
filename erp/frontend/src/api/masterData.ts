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
  created_at: string;
  updated_at: string;
}

export interface Material {
  id: string;
  company: string;
  code: string;
  name_fa: string;
  name_en: string;
  subtype: string;
  base_uom: string;
  reorder_point: number | null;
  safety_stock: number | null;
  min_stock: number | null;
  max_stock: number | null;
  lead_time_days: number | null;
  shelf_life_days: number | null;
  is_hazardous: boolean;
  msds_ref: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
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
  site: string | null;
  department: string | null;
  user: string | null;
  employee_code: string;
  first_name_fa: string;
  last_name_fa: string;
  first_name_en: string;
  last_name_en: string;
  job_title: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
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

/** Create a material via the audited service layer. */
export function createMaterial(payload: Partial<Material>): Promise<Material> {
  return apiClient.post<Material>('/catalog/materials/', payload);
}

/** Create a product via the audited service layer. */
export function createProduct(payload: Partial<Product>): Promise<Product> {
  return apiClient.post<Product>('/catalog/products/', payload);
}

/** Create a unit of measure (no audit — lightweight reference data). */
export function createUom(
  payload: Partial<UnitOfMeasure>,
): Promise<UnitOfMeasure> {
  return apiClient.post<UnitOfMeasure>('/catalog/uoms/', payload);
}

/** Create an employee (audited write path). */
export function createEmployee(
  payload: Partial<Employee>,
): Promise<Employee> {
  return apiClient.post<Employee>('/hr/employees/', payload);
}

// ── Product taxonomy (SR-02 — multi-level classification) ──

/** Top commercial grouping (groups on sales lines & CRM). */
export interface ProductGroup {
  id: string;
  code: string;
  name_fa: string;
  name_en: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Level 1 of the product taxonomy (نوع). */
export interface ProductType {
  id: string;
  code: string;
  name_fa: string;
  name_en: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Level 2 of the taxonomy (طبقه), under a ProductType. */
export interface ProductClass {
  id: string;
  product_type: string;
  code: string;
  name_fa: string;
  name_en: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Level 3 of the taxonomy (خانواده), under a ProductClass. */
export interface ProductFamily {
  id: string;
  product_class: string;
  code: string;
  name_fa: string;
  name_en: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export function createProductGroup(payload: Partial<ProductGroup>): Promise<ProductGroup> {
  return apiClient.post<ProductGroup>('/catalog/product-groups/', payload);
}

export function createProductType(payload: Partial<ProductType>): Promise<ProductType> {
  return apiClient.post<ProductType>('/catalog/product-types/', payload);
}

export function createProductClass(payload: Partial<ProductClass>): Promise<ProductClass> {
  return apiClient.post<ProductClass>('/catalog/product-classes/', payload);
}

export function createProductFamily(payload: Partial<ProductFamily>): Promise<ProductFamily> {
  return apiClient.post<ProductFamily>('/catalog/product-families/', payload);
}
