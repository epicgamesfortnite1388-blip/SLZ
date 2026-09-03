import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ results: [] })),
    post: vi.fn((_url: string, _body: unknown) => Promise.resolve({ id: 'r1' })),
  },
}));

import { apiClient } from '../client';
import {
  addAffectedUnit,
  createRecall,
  fetchRecallAffectedUnits,
  fetchRecallExposure,
  transitionRecall,
} from '../recall';

describe('recall API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('creates a recall on the recalls collection', async () => {
    await createRecall({ company: 'c1', code: 'RC-1', reason: 'test', severity: 'HIGH' });
    const [url, body] = (
      apiClient.post as unknown as { mock: { calls: unknown[][] } }
    ).mock.calls[0];
    expect(url).toBe('/recall/recalls/');
    expect(body).toMatchObject({ code: 'RC-1', severity: 'HIGH' });
  });

  it('transitions through the dedicated endpoint, not a PATCH', async () => {
    await transitionRecall('r1', 'OPEN');
    expect(apiClient.post).toHaveBeenCalledWith('/recall/recalls/r1/transition/', {
      status: 'OPEN',
    });
  });

  it('fetches exposure from the read-only exposure endpoint', async () => {
    await fetchRecallExposure('r1');
    expect(apiClient.get).toHaveBeenCalledWith('/recall/recalls/r1/exposure/');
  });

  it('lists affected units filtered by the recall', async () => {
    await fetchRecallAffectedUnits('r1');
    expect(apiClient.get).toHaveBeenCalledWith(
      '/recall/affected-units/?recall=r1&page_size=100',
    );
  });

  it('adds an affected unit to the junction collection', async () => {
    await addAffectedUnit({ recall: 'r1', traceability_unit: 'u1', note: 'n' });
    expect(apiClient.post).toHaveBeenCalledWith('/recall/affected-units/', {
      recall: 'r1',
      traceability_unit: 'u1',
      note: 'n',
    });
  });
});
