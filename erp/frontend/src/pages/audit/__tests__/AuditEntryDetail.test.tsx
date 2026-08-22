import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Initialize the real i18n bundle (en) so translated labels resolve.
import '@/i18n';

vi.mock('@/api/audit', () => ({
  fetchAuditEntry: vi.fn(),
}));

import { fetchAuditEntry, type AuditLogEntry } from '@/api/audit';
import { AuditEntryDetail } from '../AuditEntryDetail';

const entry: AuditLogEntry = {
  id: 'e-1',
  timestamp: '2026-08-22T09:30:00Z',
  actor: null,
  actor_label: 'buyer@slz.test',
  action: 'UPDATE',
  entity_type: 'procurement.PurchaseOrder',
  entity_id: 'po-7',
  before_state: { status: 'DRAFT', note: '' },
  after_state: { status: 'SUBMITTED', note: '' },
  correlation_id: 'corr-9',
  metadata: {},
};

describe('AuditEntryDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetchAuditEntry).mockResolvedValue(entry);
  });

  it('renders nothing when no entry is selected', () => {
    const { container } = render(<AuditEntryDetail entryId={null} onClose={() => {}} />);
    expect(container).toBeEmptyDOMElement();
    expect(fetchAuditEntry).not.toHaveBeenCalled();
  });

  it('fetches the entry and renders the before/after diff', async () => {
    render(<AuditEntryDetail entryId="e-1" onClose={() => {}} />);

    await waitFor(() => {
      expect(fetchAuditEntry).toHaveBeenCalledWith('e-1');
    });

    // Meta summary.
    expect(await screen.findByText('buyer@slz.test')).toBeInTheDocument();
    expect(screen.getByText(/procurement\.PurchaseOrder #po-7/)).toBeInTheDocument();

    // Diff table: header + one changed row and one unchanged row.
    expect(screen.getByText('Field')).toBeInTheDocument();
    expect(screen.getByText('Before')).toBeInTheDocument();
    expect(screen.getByText('After')).toBeInTheDocument();
    const statusCells = screen.getAllByText(/^DRAFT$|^SUBMITTED$/);
    expect(statusCells).toHaveLength(2);
    // Unchanged `note` ("") renders on both sides of its row.
    expect(screen.getAllByText("''")).toHaveLength(2);
  });

  it('calls onClose when the backdrop is clicked', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    const { container } = render(<AuditEntryDetail entryId="e-1" onClose={onClose} />);

    await screen.findByText('buyer@slz.test');
    await user.click(container.querySelector('.modal-backdrop') as HTMLElement);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
