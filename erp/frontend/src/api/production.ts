/**
 * Production (Task 011) API layer: typed shapes for the manufacturing
 * commercial-document slice — the **Production Order** (a.k.a. Work Order) and
 * its status-transition endpoints.
 *
 * Types mirror the backend DRF serializer in ``apps.production``. The status
 * state machine (DRAFT → RELEASED → COMPLETED → CLOSED, + CANCELLED) is enforced
 * server-side; the UI only surfaces the current status and triggers the allowed
 * transition — it never duplicates the rule. The order is header-only: material
 * lines and operations live on the frozen BOM/Routing revisions, and execution
 * capture (issue / confirmation / genealogy / QC results) is gated (Q-046) and
 * intentionally absent here.
 */
import { apiClient } from './client';

/** Production-order lifecycle (mirrors ``ProductionOrderStatus``). */
export type ProductionOrderStatus =
  | 'DRAFT'
  | 'RELEASED'
  | 'COMPLETED'
  | 'CLOSED'
  | 'CANCELLED';

/** A shop-floor order to make one customer product to a frozen definition. */
export interface ProductionOrder {
  id: string;
  company: string;
  site: string | null;
  number: string;
  customer_product: string;
  spec_revision: string;
  bom_revision: string | null;
  routing_revision: string | null;
  sales_order_line: string | null;
  status: ProductionOrderStatus;
  planned_quantity: string;
  uom: string;
  scheduled_start: string | null;
  scheduled_end: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

/** Create a production order (audited write path). */
export function createProductionOrder(
  payload: Partial<ProductionOrder>,
): Promise<ProductionOrder> {
  return apiClient.post<ProductionOrder>('/production/orders/', payload);
}

/** Retrieve one production order by id (header-only document). */
export function fetchProductionOrder(id: string): Promise<ProductionOrder> {
  return apiClient.get<ProductionOrder>(`/production/orders/${id}/`);
}

/** Production-order status transition by action name (server enforces legality). */
export function transitionProductionOrder(
  id: string,
  action: 'release' | 'complete' | 'close' | 'cancel',
): Promise<ProductionOrder> {
  return apiClient.post<ProductionOrder>(`/production/orders/${id}/${action}/`, {});
}
