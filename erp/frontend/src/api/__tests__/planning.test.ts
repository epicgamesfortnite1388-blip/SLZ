import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ rows: [], summary: {} })),
    post: vi.fn((_url: string, _body: unknown) => Promise.resolve({ id: 'p1' })),
  },
}));

import { apiClient } from '../client';
import { createPlanningPolicy, runPlanning } from '../planning';

describe('planning API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('runs the engine with no warehouse filter', async () => {
    await runPlanning();
    expect(apiClient.get).toHaveBeenCalledWith('/planning/policies/run/');
  });

  it('runs the engine scoped to one warehouse when given', async () => {
    await runPlanning('wh-123');
    expect(apiClient.get).toHaveBeenCalledWith(
      '/planning/policies/run/?warehouse=wh-123',
    );
  });

  it('posts a policy with exactly one item kind set', async () => {
    await createPlanningPolicy({
      company: 'c1',
      warehouse: 'w1',
      material: 'm1',
      customer_product: null,
      reorder_point: '50',
      target_level: '200',
    });
    const [url, body] = (
      apiClient.post as unknown as { mock: { calls: unknown[][] } }
    ).mock.calls[0];
    expect(url).toBe('/planning/policies/');
    expect(body).toMatchObject({ material: 'm1', customer_product: null });
  });
});
