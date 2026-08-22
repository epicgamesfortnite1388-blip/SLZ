import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ results: [] })),
    post: vi.fn(() => Promise.resolve({ id: '1' })),
  },
}));

import { apiClient } from '../client';
import { createProductionOrder, transitionProductionOrder } from '../production';

describe('production API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('posts a production order to the orders endpoint', async () => {
    await createProductionOrder({
      company: 'co1',
      customer_product: 'cp1',
      spec_revision: 'sr1',
      uom: 'uom1',
      number: 'WO-001',
      planned_quantity: '1000.000000',
      scheduled_start: null,
      scheduled_end: null,
      notes: '',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/production/orders/', {
      company: 'co1',
      customer_product: 'cp1',
      spec_revision: 'sr1',
      uom: 'uom1',
      number: 'WO-001',
      planned_quantity: '1000.000000',
      scheduled_start: null,
      scheduled_end: null,
      notes: '',
    });
  });

  it('drives production-order transitions at the action endpoint', async () => {
    await transitionProductionOrder('po-1', 'release');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/production/orders/po-1/release/',
      {},
    );
    await transitionProductionOrder('po-1', 'complete');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/production/orders/po-1/complete/',
      {},
    );
    await transitionProductionOrder('po-1', 'close');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/production/orders/po-1/close/',
      {},
    );
    await transitionProductionOrder('po-1', 'cancel');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/production/orders/po-1/cancel/',
      {},
    );
  });
});
