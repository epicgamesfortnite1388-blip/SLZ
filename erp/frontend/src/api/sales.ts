/**
 * Sales (Task 010) API layer: typed shapes for the sell-side commercial-document
 * slice — the customer **Sales Order** (header + lines) and its status-transition
 * endpoints.
 *
 * Types mirror the backend DRF serializers in ``apps.sales``. The status state
 * machine (DRAFT → CONFIRMED → CLOSED, + CANCELLED) is enforced server-side; the
 * UI only surfaces the current status and triggers the allowed transition — it
 * never duplicates the rule. NO pricing / ATP / allocation / shipment / invoice
 * shape is declared here because those layers are gated (R-14, SR-12, Q-046) and
 * are not implemented server-side.
 */
import { apiClient } from './client';
import type { Paginated } from './masterData';

/** Sales-order lifecycle (mirrors ``SalesOrderStatus``). */
export type SalesOrderStatus = 'DRAFT' | 'CONFIRMED' | 'CLOSED' | 'CANCELLED';

/** A customer order — the made-to-order demand origin. */
export interface SalesOrder {
  id: string;
  company: string;
  site: string | null;
  number: string;
  customer: string;
  status: SalesOrderStatus;
  order_date: string | null;
  requested_date: string | null;
  currency: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

/** Create a sales order (audited write path). */
export function createSalesOrder(
  payload: Partial<SalesOrder>,
): Promise<SalesOrder> {
  return apiClient.post<SalesOrder>('/sales/orders/', payload);
}

/** Retrieve one sales order (header) by id. */
export function fetchSalesOrder(id: string): Promise<SalesOrder> {
  return apiClient.get<SalesOrder>(`/sales/orders/${id}/`);
}

/** One order line (mirrors ``SalesOrderLineSerializer``). */
export interface SalesOrderLine {
  id: string;
  order: string;
  sequence: number;
  customer_product: string;
  quantity: string;
  uom: string;
  unit_price: string | null;
  notes: string;
}

/** Lines of one order (backend filters ``/sales/order-lines/?order=<id>``). */
export async function fetchSalesOrderLines(orderId: string): Promise<SalesOrderLine[]> {
  const page = await apiClient.get<Paginated<SalesOrderLine>>(
    `/sales/order-lines/?order=${encodeURIComponent(orderId)}&page_size=100`,
  );
  return page.results;
}

/** Sales-order status transition by action name (server enforces legality). */
export function transitionSalesOrder(
  id: string,
  action: 'confirm' | 'close' | 'cancel',
): Promise<SalesOrder> {
  return apiClient.post<SalesOrder>(`/sales/orders/${id}/${action}/`, {});
}
