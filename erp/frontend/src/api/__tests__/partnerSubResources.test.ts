import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() =>
      Promise.resolve({ count: 0, total_pages: 1, page: 1, page_size: 100, next: null, previous: null, results: [] }),
    ),
    post: vi.fn(() => Promise.resolve({ id: 'c-9' })),
    patch: vi.fn(() => Promise.resolve({ id: 'c-9' })),
  },
}));

import { apiClient } from '../client';
import {
  createPartnerAddress,
  createPartnerContact,
  fetchPartnerAddresses,
  fetchPartnerContacts,
  fetchCustomerProfile,
  fetchSupplierProfile,
  createCustomerProfile,
  updateCustomerProfile,
  createSupplierProfile,
  updateSupplierProfile,
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

  it('resolves the 1:1 customer profile (null when absent) and saves it', async () => {
    const api = apiClient.get as ReturnType<typeof vi.fn>;
    api.mockResolvedValueOnce({ results: [{ id: 'cu-1', requires_coa: true }] });
    const profile = await fetchCustomerProfile('p-3');
    expect(api).toHaveBeenCalledWith('/partners/customers/?partner=p-3&page_size=1');
    expect(profile?.id).toBe('cu-1');

    api.mockResolvedValueOnce({ results: [] });
    const absent = await fetchCustomerProfile('p-4');
    expect(absent).toBeNull();

    await createCustomerProfile({ partner: 'p-3', requires_coa: true });
    expect(apiClient.post).toHaveBeenCalledWith('/partners/customers/', {
      partner: 'p-3',
      requires_coa: true,
    });
    await updateCustomerProfile('cu-1', { notes: 'x' });
    expect(apiClient.patch).toHaveBeenCalledWith('/partners/customers/cu-1/', { notes: 'x' });
  });

  it('resolves the 1:1 supplier profile and drives its save paths', async () => {
    const api = apiClient.get as ReturnType<typeof vi.fn>;
    api.mockResolvedValueOnce({ results: [] });
    expect(await fetchSupplierProfile('p-5')).toBeNull();
    expect(api).toHaveBeenCalledWith('/partners/suppliers/?partner=p-5&page_size=1');

    await createSupplierProfile({ partner: 'p-5', is_approved: false });
    expect(apiClient.post).toHaveBeenCalledWith('/partners/suppliers/', {
      partner: 'p-5',
      is_approved: false,
    });
    await updateSupplierProfile('su-2', { is_approved: true });
    expect(apiClient.patch).toHaveBeenCalledWith('/partners/suppliers/su-2/', {
      is_approved: true,
    });
  });
});
