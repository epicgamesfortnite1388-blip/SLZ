import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    post: vi.fn(() => Promise.resolve({ id: 'x-1' })),
  },
}));

import { apiClient } from '../client';
import { createCompany, createSite } from '../organization';

describe('organization API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('creates a company via the audited companies endpoint', async () => {
    await createCompany({ code: 'SLZ', name_fa: 'زرین', name_en: 'Zarrin' });
    expect(apiClient.post).toHaveBeenCalledWith('/organization/companies/', {
      code: 'SLZ',
      name_fa: 'زرین',
      name_en: 'Zarrin',
    });
  });

  it('creates a site via the audited sites endpoint', async () => {
    await createSite({ company: 'c-1', code: 'THR', name_fa: 'تهران', name_en: 'Tehran' });
    expect(apiClient.post).toHaveBeenCalledWith('/organization/sites/', {
      company: 'c-1',
      code: 'THR',
      name_fa: 'تهران',
      name_en: 'Tehran',
    });
  });
});
