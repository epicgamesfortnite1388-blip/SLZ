import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ results: [] })),
    post: vi.fn(() => Promise.resolve({ id: '1' })),
  },
}));

import { apiClient } from '../client';
import {
  createTraceabilityUnit,
  createWarehouse,
  fetchStockMovements,
  fetchTraceabilityUnits,
  WAREHOUSE_STORE_TYPES,
} from '../inventory';

describe('inventory API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('posts a warehouse to the inventory endpoint', async () => {
    await createWarehouse({
      company: 'co1',
      code: 'WH-RM',
      name_fa: 'انبار مواد اولیه',
      store_type: 'RAW_MATERIAL',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/inventory/warehouses/', {
      company: 'co1',
      code: 'WH-RM',
      name_fa: 'انبار مواد اولیه',
      store_type: 'RAW_MATERIAL',
    });
  });

  it('targets traceability and movement endpoints', async () => {
    await fetchTraceabilityUnits('?company=co1&page_size=100');
    expect(apiClient.get).toHaveBeenCalledWith(
      '/inventory/traceability-units/?company=co1&page_size=100',
    );
    await fetchStockMovements();
    expect(apiClient.get).toHaveBeenCalledWith('/inventory/movements/?page_size=100');
    await createTraceabilityUnit({
      company: 'co1',
      material: 'mat-1',
      unit_type: 'ROLL',
      identifier: 'R-001',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/inventory/traceability-units/', {
      company: 'co1',
      material: 'mat-1',
      unit_type: 'ROLL',
      identifier: 'R-001',
    });
  });

  it('exposes all SR-10 special store types', () => {
    expect(WAREHOUSE_STORE_TYPES).toContain('GENERAL');
    expect(WAREHOUSE_STORE_TYPES).toContain('CLICHE');
    expect(WAREHOUSE_STORE_TYPES).toHaveLength(12);
  });
});
