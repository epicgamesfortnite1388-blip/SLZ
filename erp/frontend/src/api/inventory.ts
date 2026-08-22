/**
 * Inventory API layer: warehouse masters plus the confirmed traceability
 * execution records.
 */
import { apiClient } from './client';

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type WarehouseStoreType =
  | 'GENERAL'
  | 'RAW_MATERIAL'
  | 'WIP'
  | 'FINISHED_GOODS'
  | 'SCRAP'
  | 'QUARANTINE'
  | 'CLICHE'
  | 'LINE_SIDE'
  | 'CONSIGNMENT'
  | 'STAGNANT'
  | 'SHIPPING_STAGING'
  | 'RETURNS';

export const WAREHOUSE_STORE_TYPES: WarehouseStoreType[] = [
  'GENERAL',
  'RAW_MATERIAL',
  'WIP',
  'FINISHED_GOODS',
  'SCRAP',
  'QUARANTINE',
  'CLICHE',
  'LINE_SIDE',
  'CONSIGNMENT',
  'STAGNANT',
  'SHIPPING_STAGING',
  'RETURNS',
];

export type WarehouseAccessLevel = 'VIEW' | 'OPERATE';

export interface Warehouse {
  id: string;
  company: string;
  site: string | null;
  code: string;
  name_fa: string;
  name_en: string;
  store_type: WarehouseStoreType;
  is_active: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface WarehouseAccess {
  id: string;
  warehouse: string;
  user: string;
  access_level: WarehouseAccessLevel;
  created_at: string;
  updated_at: string;
}

export type TraceabilityUnitType = 'BATCH' | 'ROLL' | 'PALLET' | 'CARTON';

export interface TraceabilityUnit {
  id: string;
  company: string;
  material: string | null;
  customer_product_id: string | null;
  parent: string | null;
  unit_type: TraceabilityUnitType;
  identifier: string;
  quantity: string | null;
  uom: string | null;
  weight: string | null;
  length: string | null;
  width: string | null;
  core: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export type StockMovementDirection = 'IN' | 'OUT' | 'TRANSFER';

export interface StockMovement {
  id: string;
  company: string;
  warehouse: string;
  traceability_unit: string | null;
  material: string | null;
  direction: StockMovementDirection;
  quantity: string;
  uom: string;
  reference_type: string;
  reference_id: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export function createWarehouse(payload: Partial<Warehouse>): Promise<Warehouse> {
  return apiClient.post<Warehouse>('/inventory/warehouses/', payload);
}

export function fetchTraceabilityUnits(
  query = '?page_size=100',
): Promise<Paginated<TraceabilityUnit>> {
  return apiClient.get<Paginated<TraceabilityUnit>>(`/inventory/traceability-units/${query}`);
}

export function createTraceabilityUnit(
  payload: Partial<TraceabilityUnit>,
): Promise<TraceabilityUnit> {
  return apiClient.post<TraceabilityUnit>('/inventory/traceability-units/', payload);
}

export function fetchStockMovements(
  query = '?page_size=100',
): Promise<Paginated<StockMovement>> {
  return apiClient.get<Paginated<StockMovement>>(`/inventory/movements/${query}`);
}
