/**
 * Shipment API module — allocations and deliveries.
 */
import { apiClient } from './client';
import type { Paginated } from './inventory';

export type AllocationStatus = 'RESERVED' | 'RELEASED';

export interface Allocation {
  id: string;
  company: string;
  sales_order_line: string;
  traceability_unit: string;
  quantity: string;
  uom: string;
  status: AllocationStatus;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface ShipmentLine {
  id: string;
  shipment: string;
  sales_order_line: string | null;
  allocation: string | null;
  traceability_unit: string;
  quantity: string;
  uom: string;
  notes: string;
}

export interface Shipment {
  id: string;
  company: string;
  sales_order: string | null;
  customer: string;
  warehouse: string;
  number: string;
  status: string;
  shipped_at: string;
  notes: string;
  lines: ShipmentLine[];
  created_at: string;
  updated_at: string;
}

export function fetchAllocations(query = '?page_size=100'): Promise<Paginated<Allocation>> {
  return apiClient.get<Paginated<Allocation>>(`/shipment/allocations/${query}`);
}

export function createAllocation(payload: Partial<Allocation>): Promise<Allocation> {
  return apiClient.post<Allocation>('/shipment/allocations/', payload);
}

export function releaseAllocation(id: string): Promise<Allocation> {
  return apiClient.post<Allocation>(`/shipment/allocations/${id}/release/`, {});
}

export function fetchShipments(query = '?page_size=100'): Promise<Paginated<Shipment>> {
  return apiClient.get<Paginated<Shipment>>(`/shipment/deliveries/${query}`);
}

export interface ShipmentCreatePayload {
  company: string;
  warehouse: string;
  customer: string;
  sales_order?: string | null;
  number: string;
  shipped_at: string;
  notes?: string;
  lines: Array<{
    traceability_unit: string;
    sales_order_line?: string | null;
    allocation?: string | null;
    quantity: string;
    uom: string;
    notes?: string;
  }>;
}

export function createShipment(payload: ShipmentCreatePayload): Promise<Shipment> {
  return apiClient.post<Shipment>('/shipment/deliveries/', payload);
}