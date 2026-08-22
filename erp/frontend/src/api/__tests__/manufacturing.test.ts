import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ results: [] })),
    post: vi.fn(() => Promise.resolve({ id: '1' })),
  },
}));

import { apiClient } from '../client';
import {
  createWorkCenter,
  activateBomRevision,
  activateRoutingRevision,
  fetchBom,
  listBomRevisions,
  listBomLines,
  fetchRouting,
  listRoutingRevisions,
  listRoutingOperations,
} from '../manufacturing';

describe('manufacturing API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('posts a work center to the manufacturing endpoint', async () => {
    await createWorkCenter({ code: 'EXT', name_fa: 'اکستروژن', company: 'co1' });
    expect(apiClient.post).toHaveBeenCalledWith('/manufacturing/work-centers/', {
      code: 'EXT',
      name_fa: 'اکستروژن',
      company: 'co1',
    });
  });

  it('activates a BOM revision by id', async () => {
    await activateBomRevision('bom-1');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/manufacturing/bom-revisions/bom-1/activate/',
      {},
    );
  });

  it('activates a routing revision by id', async () => {
    await activateRoutingRevision('rt-1');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/manufacturing/routing-revisions/rt-1/activate/',
      {},
    );
  });

  it('retrieves a BOM root and its revision chain, newest first', async () => {
    const api = apiClient.get as ReturnType<typeof vi.fn>;
    api.mockResolvedValueOnce({ id: 'bom-1' });
    api.mockResolvedValueOnce({
      results: [
        { id: 'r2', revision_number: 2 },
        { id: 'r1', revision_number: 1 },
      ],
    });
    const bom = await fetchBom('bom-1');
    expect(api).toHaveBeenCalledWith('/manufacturing/boms/bom-1/');
    expect(bom.id).toBe('bom-1');
    const revs = await listBomRevisions('bom-1');
    expect(api).toHaveBeenCalledWith(
      '/manufacturing/bom-revisions/?root=bom-1&page_size=100',
    );
    expect(revs.map((r) => r.revision_number)).toEqual([2, 1]);
  });

  it('lists BOM lines of a revision ordered by sequence', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      results: [
        { id: 'l2', sequence: 2 },
        { id: 'l1', sequence: 1 },
      ],
    });
    const lines = await listBomLines('rev-9');
    expect(apiClient.get).toHaveBeenCalledWith(
      '/manufacturing/bom-lines/?revision=rev-9&page_size=100',
    );
    expect(lines.map((l) => l.sequence)).toEqual([1, 2]);
  });

  it('retrieves a routing root and its operations ordered by sequence', async () => {
    const api = apiClient.get as ReturnType<typeof vi.fn>;
    api.mockResolvedValueOnce({ id: 'rt-1' });
    api.mockResolvedValueOnce({ results: [] });
    await fetchRouting('rt-1');
    expect(api).toHaveBeenCalledWith('/manufacturing/routings/rt-1/');
    await listRoutingRevisions('rt-1');
    expect(api).toHaveBeenCalledWith(
      '/manufacturing/routing-revisions/?root=rt-1&page_size=100',
    );
    api.mockResolvedValueOnce({
      results: [
        { id: 'o3', sequence: 3 },
        { id: 'o1', sequence: 1 },
        { id: 'o2', sequence: 2 },
      ],
    });
    const ops = await listRoutingOperations('rev-5');
    expect(api).toHaveBeenCalledWith(
      '/manufacturing/routing-operations/?revision=rev-5&page_size=100',
    );
    expect(ops.map((o) => o.sequence)).toEqual([1, 2, 3]);
  });
});
