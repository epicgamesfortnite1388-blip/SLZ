import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    post: vi.fn(() => Promise.resolve({ id: 'x-1' })),
    patch: vi.fn(() => Promise.resolve({ id: 'x-1' })),
  },
}));

import { apiClient } from '../client';
import {
  createCompany,
  createSite,
  updateCompany,
  updateSite,
  updateDepartment,
} from '../organization';

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

  it('PATCHes the company edit flow (code stays immutable client-side)', async () => {
    await updateCompany('co-1', { name_fa: 'زرین', name_en: 'Zarrin', is_active: true });
    expect(apiClient.patch).toHaveBeenCalledWith('/organization/companies/co-1/', {
      name_fa: 'زرین',
      name_en: 'Zarrin',
      is_active: true,
    });
  });

  it('PATCHes the site edit flow to the sites endpoint', async () => {
    await updateSite('site-1', { timezone: 'Asia/Tehran', is_active: false });
    expect(apiClient.patch).toHaveBeenCalledWith('/organization/sites/site-1/', {
      timezone: 'Asia/Tehran',
      is_active: false,
    });
  });

  it('PATCHes the department edit flow to the departments endpoint', async () => {
    await updateDepartment('dep-1', { name_fa: 'تولید', parent: null });
    expect(apiClient.patch).toHaveBeenCalledWith('/organization/departments/dep-1/', {
      name_fa: 'تولید',
      parent: null,
    });
  });
});
