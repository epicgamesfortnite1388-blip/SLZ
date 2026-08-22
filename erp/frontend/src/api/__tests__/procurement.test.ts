import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ results: [] })),
    post: vi.fn(() => Promise.resolve({ id: '1' })),
  },
}));

import { apiClient } from '../client';
import {
  createPurchaseRequisition,
  createPurchaseOrder,
  transitionRequisition,
  transitionOrder,
} from '../procurement';

describe('procurement API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('posts a requisition to the requisitions endpoint', async () => {
    await createPurchaseRequisition({
      company: 'co1',
      number: 'PR-001',
      need_by_date: null,
      notes: '',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/procurement/requisitions/', {
      company: 'co1',
      number: 'PR-001',
      need_by_date: null,
      notes: '',
    });
  });

  it('posts a purchase order to the orders endpoint', async () => {
    await createPurchaseOrder({
      company: 'co1',
      supplier: 'sup1',
      number: 'PO-001',
      currency: 'IRR',
      expected_date: null,
      notes: '',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/procurement/orders/', {
      company: 'co1',
      supplier: 'sup1',
      number: 'PO-001',
      currency: 'IRR',
      expected_date: null,
      notes: '',
    });
  });

  it('drives requisition transitions at the action endpoint', async () => {
    await transitionRequisition('req-1', 'submit');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/procurement/requisitions/req-1/submit/',
      {},
    );
    await transitionRequisition('req-1', 'approve');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/procurement/requisitions/req-1/approve/',
      {},
    );
  });

  it('drives purchase-order transitions at the action endpoint', async () => {
    await transitionOrder('po-1', 'send');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/procurement/orders/po-1/send/',
      {},
    );
    await transitionOrder('po-1', 'close');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/procurement/orders/po-1/close/',
      {},
    );
  });
});
