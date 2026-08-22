import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ results: [] })),
    post: vi.fn(() => Promise.resolve({ id: '1' })),
  },
}));

import { apiClient } from '../client';
import { createSalesOrder, transitionSalesOrder } from '../sales';

describe('sales API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('posts a sales order to the orders endpoint', async () => {
    await createSalesOrder({
      company: 'co1',
      customer: 'cust1',
      number: 'SO-001',
      currency: 'IRR',
      requested_date: null,
      notes: '',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/sales/orders/', {
      company: 'co1',
      customer: 'cust1',
      number: 'SO-001',
      currency: 'IRR',
      requested_date: null,
      notes: '',
    });
  });

  it('drives sales-order transitions at the action endpoint', async () => {
    await transitionSalesOrder('so-1', 'confirm');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/sales/orders/so-1/confirm/',
      {},
    );
    await transitionSalesOrder('so-1', 'close');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/sales/orders/so-1/close/',
      {},
    );
    await transitionSalesOrder('so-1', 'cancel');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/sales/orders/so-1/cancel/',
      {},
    );
  });
});
