import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ results: [] })),
    post: vi.fn(() => Promise.resolve({ id: '1' })),
  },
}));

import { apiClient } from '../client';
import { recordDecision, cancelWorkflow, createWorkflowDefinition } from '../workflow';

describe('workflow API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('creates a workflow definition via the audited definitions endpoint', async () => {
    await createWorkflowDefinition({
      code: 'po_approval',
      name_fa: 'تأیید',
      name_en: 'PO approval',
      approval_mode: 'SEQUENTIAL',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/workflow/definitions/', {
      code: 'po_approval',
      name_fa: 'تأیید',
      name_en: 'PO approval',
      approval_mode: 'SEQUENTIAL',
    });
  });

  it('posts an approval decision to the decision endpoint', async () => {
    await recordDecision('wf-1', true, 'looks good');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/workflow/instances/wf-1/decision/',
      { approve: true, comment: 'looks good' },
    );
  });

  it('defaults the decision comment to an empty string', async () => {
    await recordDecision('wf-1', false);
    expect(apiClient.post).toHaveBeenCalledWith(
      '/workflow/instances/wf-1/decision/',
      { approve: false, comment: '' },
    );
  });

  it('posts a cancel with a reason to the cancel endpoint', async () => {
    await cancelWorkflow('wf-1', 'superseded');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/workflow/instances/wf-1/cancel/',
      { reason: 'superseded' },
    );
  });
});
