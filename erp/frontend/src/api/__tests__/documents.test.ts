import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ results: [] })),
    postForm: vi.fn(() => Promise.resolve({ id: '1' })),
    delete: vi.fn(() => Promise.resolve(undefined)),
    getBlob: vi.fn(() => Promise.resolve(new Blob(['x']))),
  },
}));

import { apiClient } from '../client';
import {
  uploadAttachment,
  deleteAttachment,
  listAttachments,
  formatBytes,
} from '../documents';

describe('documents API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('uploads via multipart to the upload endpoint with all fields', async () => {
    const file = new File(['hello'], 'note.txt', { type: 'text/plain' });
    await uploadAttachment('procurement.PurchaseOrder', 'po-1', file, 'a note');

    expect(apiClient.postForm).toHaveBeenCalledTimes(1);
    const [path, form] = (apiClient.postForm as unknown as { mock: { calls: unknown[][] } })
      .mock.calls[0];
    expect(path).toBe('/documents/attachments/upload/');
    const fd = form as FormData;
    expect(fd.get('entity_type')).toBe('procurement.PurchaseOrder');
    expect(fd.get('entity_id')).toBe('po-1');
    expect(fd.get('description')).toBe('a note');
    expect(fd.get('file')).toBeInstanceOf(File);
  });

  it('omits the description field when blank', async () => {
    const file = new File(['hi'], 'x.txt', { type: 'text/plain' });
    await uploadAttachment('sales.SalesOrder', 'so-9', file);
    const [, form] = (apiClient.postForm as unknown as { mock: { calls: unknown[][] } })
      .mock.calls[0];
    expect((form as FormData).get('description')).toBeNull();
  });

  it('deletes an attachment by id', async () => {
    await deleteAttachment('att-7');
    expect(apiClient.delete).toHaveBeenCalledWith('/documents/attachments/att-7/');
  });

  it('lists attachments filtered by entity, unwrapping the envelope', async () => {
    (apiClient.get as unknown as { mockResolvedValueOnce: (v: unknown) => void })
      .mockResolvedValueOnce({ results: [{ id: 'a1' }, { id: 'a2' }] });
    const rows = await listAttachments('partners.Partner', 'p-1');

    expect(rows).toHaveLength(2);
    const [url] = (apiClient.get as unknown as { mock: { calls: unknown[][] } }).mock.calls[0];
    expect(url).toContain('/documents/attachments/?');
    expect(url).toContain('entity_type=partners.Partner');
    expect(url).toContain('entity_id=p-1');
    expect(url).toContain('page_size=200');
  });

  it('formats byte sizes into human units', () => {
    expect(formatBytes(0)).toBe('0 B');
    expect(formatBytes(512)).toBe('512 B');
    expect(formatBytes(1024)).toBe('1 KB');
    expect(formatBytes(1536)).toBe('1.5 KB');
    expect(formatBytes(1024 * 1024)).toBe('1 MB');
  });
});
