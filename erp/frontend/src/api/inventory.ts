/**
 * Inventory foundation (Task 007) API layer: typed entity shapes for the
 * CONFIRMED, un-gated master-data slice — Warehouse (with SR-10 special store
 * types) and per-user WarehouseAccess.
 *
 * Types mirror the backend DRF serializers in ``apps.inventory``. NO stock
 * movement / kardex / lot-roll / genealogy shape is declared here because that
 * transactional + traceability layer is gated (Q-046 roll serialization and
 * related open decisions) and is not implemented server-side.
 */
import { apiClient } from './client';

/**
 * Special store types (SR-10). Mirrors ``WarehouseStoreType`` on the backend;
 * the option list is data the UI surfaces — the enum itself is enforced
 * server-side (an invalid value is rejected with a 400).
 */
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

/** Ordered list of store types for select inputs (labels come from i18n). */
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

/** Per-user access level to a warehouse (SR-10). */
export type WarehouseAccessLevel = 'VIEW' | 'OPERATE';

/** A company/site-scoped storage location master record. */
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

/** An explicit grant of a user's access to a single warehouse (SR-10). */
export interface WarehouseAccess {
  id: string;
  warehouse: string;
  user: string;
  access_level: WarehouseAccessLevel;
  created_at: string;
  updated_at: string;
}

/** Create a warehouse (representative audited write path). */
export function createWarehouse(
  payload: Partial<Warehouse>,
): Promise<Warehouse> {
  return apiClient.post<Warehouse>('/inventory/warehouses/', payload);
}
