/**
 * Procurement (Task 009) API layer: typed shapes for the commercial-document
 * slice — Purchase Requisition and Purchase Order (headers + lines) and their
 * status-transition endpoints.
 *
 * Types mirror the backend DRF serializers in ``apps.procurement``. The status
 * state machine is enforced server-side; the UI only surfaces the current status
 * and triggers the allowed transition — it never duplicates the rule. NO goods
 * receipt / MRP / FX / valuation / invoice shape is declared here because those
 * layers are gated / belong to later phases and are not implemented server-side.
 */
import { apiClient } from './client';
import type { Paginated } from './masterData';

/** Requisition lifecycle (mirrors ``PurchaseRequisitionStatus``). */
export type PurchaseRequisitionStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'APPROVED'
  | 'REJECTED'
  | 'CANCELLED';

/** Purchase-order lifecycle (mirrors ``PurchaseOrderStatus``; pre-receipt). */
export type PurchaseOrderStatus =
  | 'DRAFT'
  | 'APPROVED'
  | 'SENT'
  | 'CLOSED'
  | 'CANCELLED';

/** An internal request to purchase materials. */
export interface PurchaseRequisition {
  id: string;
  company: string;
  site: string | null;
  number: string;
  status: PurchaseRequisitionStatus;
  requested_by: string | null;
  need_by_date: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

/** A commitment to buy from a supplier. */
export interface PurchaseOrder {
  id: string;
  company: string;
  site: string | null;
  number: string;
  supplier: string;
  status: PurchaseOrderStatus;
  order_date: string | null;
  expected_date: string | null;
  currency: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

/** Create a purchase requisition (audited write path). */
export function createPurchaseRequisition(
  payload: Partial<PurchaseRequisition>,
): Promise<PurchaseRequisition> {
  return apiClient.post<PurchaseRequisition>(
    '/procurement/requisitions/',
    payload,
  );
}

/** Retrieve one purchase requisition (header) by id. */
export function fetchPurchaseRequisition(id: string): Promise<PurchaseRequisition> {
  return apiClient.get<PurchaseRequisition>(`/procurement/requisitions/${id}/`);
}

/** One requisition line (mirrors ``PurchaseRequisitionLineSerializer``). */
export interface PurchaseRequisitionLine {
  id: string;
  requisition: string;
  sequence: number;
  material: string;
  quantity: string;
  uom: string;
  notes: string;
}

/** Lines of one requisition (`/procurement/requisition-lines/?requisition=`). */
export async function fetchPurchaseRequisitionLines(
  requisitionId: string,
): Promise<PurchaseRequisitionLine[]> {
  const page = await apiClient.get<Paginated<PurchaseRequisitionLine>>(
    `/procurement/requisition-lines/?requisition=${encodeURIComponent(requisitionId)}&page_size=100`,
  );
  return page.results;
}

/** Create a purchase order (audited write path). */
export function createPurchaseOrder(
  payload: Partial<PurchaseOrder>,
): Promise<PurchaseOrder> {
  return apiClient.post<PurchaseOrder>('/procurement/orders/', payload);
}

/** Retrieve one purchase order (header) by id. */
export function fetchPurchaseOrder(id: string): Promise<PurchaseOrder> {
  return apiClient.get<PurchaseOrder>(`/procurement/orders/${id}/`);
}

/** One order line (mirrors ``PurchaseOrderLineSerializer``). */
export interface PurchaseOrderLine {
  id: string;
  order: string;
  sequence: number;
  material: string;
  quantity: string;
  uom: string;
  unit_price: string | null;
  requisition_line: string | null;
  notes: string;
}

/** Lines of one purchase order (`/procurement/order-lines/?order=`). */
export async function fetchPurchaseOrderLines(orderId: string): Promise<PurchaseOrderLine[]> {
  const page = await apiClient.get<Paginated<PurchaseOrderLine>>(
    `/procurement/order-lines/?order=${encodeURIComponent(orderId)}&page_size=100`,
  );
  return page.results;
}

/** Requisition status transition by action name (server enforces legality). */
export function transitionRequisition(
  id: string,
  action: 'submit' | 'approve' | 'reject' | 'cancel',
): Promise<PurchaseRequisition> {
  return apiClient.post<PurchaseRequisition>(
    `/procurement/requisitions/${id}/${action}/`,
    {},
  );
}

/** Purchase-order status transition by action name (server enforces legality). */
export function transitionOrder(
  id: string,
  action: 'approve' | 'send' | 'close' | 'cancel',
): Promise<PurchaseOrder> {
  return apiClient.post<PurchaseOrder>(
    `/procurement/orders/${id}/${action}/`,
    {},
  );
}
