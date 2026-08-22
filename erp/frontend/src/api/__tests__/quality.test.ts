import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ results: [] })),
    post: vi.fn(() => Promise.resolve({ id: '1' })),
  },
}));

import { apiClient } from '../client';
import {
  createQualityCharacteristic,
  activateQualityPlanRevision,
  CHARACTERISTIC_DATATYPES,
} from '../quality';

describe('quality API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('posts a characteristic to the quality endpoint', async () => {
    await createQualityCharacteristic({
      company: 'co1',
      code: 'THK',
      name_fa: 'ضخامت',
      datatype: 'NUMBER',
      method: 'ASTM D6988',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/quality/characteristics/', {
      company: 'co1',
      code: 'THK',
      name_fa: 'ضخامت',
      datatype: 'NUMBER',
      method: 'ASTM D6988',
    });
  });

  it('activates a quality-plan revision at the lifecycle endpoint', async () => {
    await activateQualityPlanRevision('rev-1');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/quality/plan-revisions/rev-1/activate/',
      {},
    );
  });

  it('exposes the supported characteristic datatypes', () => {
    expect(CHARACTERISTIC_DATATYPES).toContain('NUMBER');
    expect(CHARACTERISTIC_DATATYPES).toHaveLength(3);
  });
});
