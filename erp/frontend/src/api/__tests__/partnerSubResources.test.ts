import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() =>
      Promise.resolve({ count: 0, total_pages: 1, page: 1, page_size: 100, next: null, previous: null, results: [] }),
    ),
    post: vi.fn(() => Promise.resolve({ id: 'c-9' })),
  },
}));

import { apiClient } from '../client';
import {
  createPartnerAddress,
  createPartnerContact,
  fetchPartnerAddresses,
  fetchPartnerContacts,
} from '../masterData';

describe('partner contacts/addresses API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('filters contacts by partner and returns the rows', async () => {
    await fetchPartnerContacts('p-1');
    expect(apiClient.get).toHaveBeenCalledWith('/partners/contacts/?partner=p-1&page_size=100');
  });

  it('filters addresses by partner and returns the rows', async () => {
    await fetchPartnerAddresses('p-2');
    expect(apiClient.get).toHaveBeenCalledWith('/partners/addresses/?partner=p-2&page_size=100');
  });

  it('posts contacts and addresses to their collection endpoints', async () => {
    await createPartnerContact({ partner: 'p-1', name: 'Ali', kind: 'SALES' });
    expect(apiClient.post).toHaveBeenCalledWith('/partners/contacts/', {
      partner: 'p-1',
      name: 'Ali',
      kind: 'SALES',
    });

    await createPartnerAddress({ partner: 'p-1', kind: 'SHIPPING', line1: 'Road 5' });
    expect(apiClient.post).toHaveBeenCalledWith('/partners/addresses/', {
      partner: 'p-1',
      kind: 'SHIPPING',
      line1: 'Road 5',
    });
  });
});
