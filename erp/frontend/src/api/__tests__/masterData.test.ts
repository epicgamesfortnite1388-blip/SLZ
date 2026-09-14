import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ results: [] })),
    post: vi.fn(() => Promise.resolve({ id: '1' })),
    patch: vi.fn(() => Promise.resolve({ id: '1' })),
  },
}));

import { apiClient } from '../client';
import {
  fetchCollection,
  createPartner,
  fetchPartner,
  fetchMaterial,
  fetchUom,
  updatePartner,
  updateProduct,
  updateMaterial,
  updateEmployee,
} from '../masterData';

describe('masterData API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('builds a bare path when no query params are given', async () => {
    await fetchCollection('/partners/partners/');
    expect(apiClient.get).toHaveBeenCalledWith('/partners/partners/');
  });

  it('encodes page, page_size and search params', async () => {
    await fetchCollection('/catalog/products/', {
      page: 2,
      pageSize: 50,
      search: 'coffee',
    });
    expect(apiClient.get).toHaveBeenCalledWith(
      '/catalog/products/?page=2&page_size=50&search=coffee',
    );
  });

  it('omits blank search terms', async () => {
    await fetchCollection('/hr/employees/', { search: '   ' });
    expect(apiClient.get).toHaveBeenCalledWith('/hr/employees/');
  });

  it('posts a partner to the partners endpoint', async () => {
    await createPartner({ code: 'C-1', name_fa: 'الف', is_customer: true });
    expect(apiClient.post).toHaveBeenCalledWith('/partners/partners/', {
      code: 'C-1',
      name_fa: 'الف',
      is_customer: true,
    });
  });

  it('fetches reference records by id for detail labels', async () => {
    await fetchPartner('partner-1');
    expect(apiClient.get).toHaveBeenCalledWith('/partners/partners/partner-1/');
    await fetchMaterial('material-1');
    expect(apiClient.get).toHaveBeenCalledWith('/catalog/materials/material-1/');
    await fetchUom('uom-1');
    expect(apiClient.get).toHaveBeenCalledWith('/catalog/uoms/uom-1/');
  });

  it('PATCHes the partner edit flow to the partners endpoint', async () => {
    await updatePartner('p-1', { name_fa: 'الف', is_customer: true });
    expect(apiClient.patch).toHaveBeenCalledWith('/partners/partners/p-1/', {
      name_fa: 'الف',
      is_customer: true,
    });
  });

  it('PATCHes the product edit flow to the catalog endpoint', async () => {
    await updateProduct('prod-1', { name_fa: 'محصول', is_active: true });
    expect(apiClient.patch).toHaveBeenCalledWith('/catalog/products/prod-1/', {
      name_fa: 'محصول',
      is_active: true,
    });
  });

  it('PATCHes the material edit flow to the catalog endpoint', async () => {
    await updateMaterial('mat-1', { reorder_point: 10, safety_stock: 5 });
    expect(apiClient.patch).toHaveBeenCalledWith('/catalog/materials/mat-1/', {
      reorder_point: 10,
      safety_stock: 5,
    });
  });

  it('PATCHes the employee edit flow to the hr endpoint', async () => {
    await updateEmployee('emp-1', { job_title: 'اپراتور', is_active: false });
    expect(apiClient.patch).toHaveBeenCalledWith('/hr/employees/emp-1/', {
      job_title: 'اپراتور',
      is_active: false,
    });
  });
});
