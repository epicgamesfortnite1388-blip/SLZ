/**
 * Goods Receipt (GRN) API — receipt posting against purchase orders.
 */
import { apiClient } from './client';

export type GoodsReceiptStatus = 'PENDING' | 'POSTED' | 'CANCELLED';

export interface GoodsReceiptLine {
  id: string;
  sequence: number;
  material: string;
  po_line_id: string | null;
  quantity: string;
  uom: string;
  unit_type: string;
  identifier: string;
  notes: string;
}

export interface GoodsReceipt {
  id: string;
  company: string;
  warehouse: string;
  supplier: string;
  purchase_order: string | null;
  number: string;
  status: GoodsReceiptStatus;
  receipt_date: string;
  notes: string;
  lines: GoodsReceiptLine[];
  created_at: string;
  updated_at: string;
}

export function createGoodsReceipt(
  payload: Record<string, unknown>,
): Promise<GoodsReceipt> {
  return apiClient.post<GoodsReceipt>('/procurement/grns/', payload);
}