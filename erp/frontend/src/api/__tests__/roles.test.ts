import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() =>
      Promise.resolve({
        count: 1,
        total_pages: 1,
        page: 1,
        page_size: 25,
        next: null,
        previous: null,
        results: [
          {
            id: 'r-1',
            code: 'ADMIN',
            name_en: 'Administrator',
            name_fa: 'مدیر',
            description: '',
            is_system: true,
            permission_codes: ['audit.log.view'],
          },
        ],
      }),
    ),
    post: vi.fn(() =>
      Promise.resolve({
        id: 'r-2',
        code: 'PLANNER',
        name_en: 'Planner',
        name_fa: 'برنامه‌ریز',
        description: '',
        is_system: false,
        permission_codes: [],
      }),
    ),
  },
}));

import { apiClient } from '../client';
import { createRole, fetchRoles } from '../roles';

describe('roles API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('lists roles from the auth namespace with pagination', async () => {
    const page = await fetchRoles();

    expect(apiClient.get).toHaveBeenCalledWith('/auth/roles/?page=1&page_size=25');
    expect(page.results[0].permission_codes).toEqual(['audit.log.view']);
  });

  it('creates a role via the audited write path', async () => {
    const role = await createRole({ code: 'PLANNER', name_en: 'Planner' });

    expect(apiClient.post).toHaveBeenCalledWith('/auth/roles/', {
      code: 'PLANNER',
      name_en: 'Planner',
    });
    expect(role.code).toBe('PLANNER');
  });
});
