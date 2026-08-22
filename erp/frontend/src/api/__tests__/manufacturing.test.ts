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
});
