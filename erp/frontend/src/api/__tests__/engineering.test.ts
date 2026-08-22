import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ results: [] })),
    post: vi.fn(() => Promise.resolve({ id: '1' })),
  },
}));

import { apiClient } from '../client';
import {
  createCustomerProduct,
  activateSpecification,
  fetchCustomerProduct,
  fetchSpecification,
  listSpecificationRevisions,
  listSpecLayers,
  listSpecColors,
  listSpecParameters,
} from '../engineering';

describe('engineering API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('posts a customer product to the engineering endpoint', async () => {
    await createCustomerProduct({ code: 'CP-1', name_fa: 'الف', customer: 'c1' });
    expect(apiClient.post).toHaveBeenCalledWith('/engineering/customer-products/', {
      code: 'CP-1',
      name_fa: 'الف',
      customer: 'c1',
    });
  });

  it('activates a specification revision by id', async () => {
    await activateSpecification('rev-123');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/engineering/specifications/rev-123/activate/',
      {},
    );
  });

  it('retrieves one customer product and one revision by id', async () => {
    await fetchCustomerProduct('cp-1');
    expect(apiClient.get).toHaveBeenCalledWith('/engineering/customer-products/cp-1/');
    await fetchSpecification('rev-1');
    expect(apiClient.get).toHaveBeenCalledWith('/engineering/specifications/rev-1/');
  });

  it('lists the full revision chain of a root', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      results: [
        { id: 'a', revision_number: 2 },
        { id: 'b', revision_number: 1 },
      ],
    });
    const revs = await listSpecificationRevisions('cp-1');
    expect(apiClient.get).toHaveBeenCalledWith(
      '/engineering/specifications/?root=cp-1&page_size=100',
    );
    // Newest first, so the detail page can preselect the latest chain entry.
    expect(revs.map((r) => r.revision_number)).toEqual([2, 1]);
  });

  it('lists spec child rows filtered by revision', async () => {
    const api = apiClient.get as ReturnType<typeof vi.fn>;
    api.mockResolvedValue({
      results: [
        { id: 'x', sequence: 2 },
        { id: 'y', sequence: 1 },
      ],
    });
    const layers = await listSpecLayers('rev-1');
    expect(api).toHaveBeenCalledWith(
      '/engineering/spec-layers/?revision=rev-1&page_size=100',
    );
    expect(layers.map((l) => l.sequence)).toEqual([1, 2]);
    await listSpecColors('rev-1');
    expect(api).toHaveBeenCalledWith(
      '/engineering/spec-colors/?revision=rev-1&page_size=100',
    );
    api.mockResolvedValue({
      results: [
        { id: 'p2', key: 'seal_width' },
        { id: 'p1', key: 'dart_depth' },
      ],
    });
    const params = await listSpecParameters('rev-1');
    expect(api).toHaveBeenCalledWith(
      '/engineering/spec-parameters/?revision=rev-1&page_size=100',
    );
    // Parameters are ordered by key for stable display.
    expect(params.map((p) => p.key)).toEqual(['dart_depth', 'seal_width']);
  });
});
