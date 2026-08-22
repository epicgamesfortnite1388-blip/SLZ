import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ results: [] })),
    post: vi.fn(() => Promise.resolve({ id: '1' })),
  },
}));

import { apiClient } from '../client';
import {
  createToolingAsset,
  transitionToolingAsset,
  listToolingAssetsByCustomerProduct,
} from '../tooling';

describe('tooling API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('posts a tooling asset to the tooling-assets endpoint', async () => {
    await createToolingAsset({
      company: 'co1',
      customer: 'cu1',
      customer_product: null,
      tooling_type: 'CLICHE',
      warehouse: null,
      code: 'CL-001',
      name_fa: 'کلیشه',
      name_en: '',
      usage_life_limit: null,
      notes: '',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/engineering/tooling-assets/', {
      company: 'co1',
      customer: 'cu1',
      customer_product: null,
      tooling_type: 'CLICHE',
      warehouse: null,
      code: 'CL-001',
      name_fa: 'کلیشه',
      name_en: '',
      usage_life_limit: null,
      notes: '',
    });
  });

  it('drives tooling transitions at the action endpoint', async () => {
    await transitionToolingAsset('tl-1', 'retire');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/engineering/tooling-assets/tl-1/retire/',
      {},
    );
    await transitionToolingAsset('tl-1', 'reactivate');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/engineering/tooling-assets/tl-1/reactivate/',
      {},
    );
  });

  it('lists tooling assets linked to one customer product', async () => {
    await listToolingAssetsByCustomerProduct('cp-9');
    expect(apiClient.get).toHaveBeenCalledWith(
      '/engineering/tooling-assets/?customer_product=cp-9&page_size=100',
    );
  });
});
