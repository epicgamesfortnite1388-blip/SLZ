import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { Alert, Button, Card, Spinner } from '@/components/ui';
import { isApiError } from '@/api/types';
import {
  listAttachments,
  uploadAttachment,
  deleteAttachment,
  downloadAttachment,
  formatBytes,
  type Attachment,
} from '@/api/documents';

interface AttachmentPanelProps {
  /** Backend entity label, e.g. `partners.Partner`. */
  entityType: string;
  /** Target record id. */
  entityId: string;
}

/**
 * Reusable in-context file panel for a single record. Lists the attachments
 * pinned to (`entityType`, `entityId`), and — for users with the right
 * permissions — supports upload, authenticated download, and soft-delete.
 *
 * It reuses the generic `/documents/attachments/` API, so it encodes no rule
 * about what may attach to what; a detail screen simply drops it in with the
 * owning record's type and id. Uploading needs `documents.attachment.view`
 * (the server default for the upload action); deleting is gated by
 * `documents.attachment.delete`. Rendered only when the signed-in user can view
 * attachments — the caller checks the permission before mounting.
 */
export function AttachmentPanel({ entityType, entityId }: AttachmentPanelProps): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canDelete = hasPermission('documents.attachment.delete');

  const [items, setItems] = useState<Attachment[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const reload = useCallback(() => {
    let active = true;
    setError(null);
    listAttachments(entityType, entityId)
      .then((rows) => {
        if (active) setItems(rows);
      })
      .catch((err: unknown) => {
        if (active) {
          setItems([]);
          setError(isApiError(err) ? err.message : t('common.error'));
        }
      });
    return () => {
      active = false;
    };
  }, [entityType, entityId, t]);

  useEffect(() => reload(), [reload]);

  const handleUpload = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    if (!file) {
      setError(t('documents.errors.noFile'));
      return;
    }
    setUploading(true);
    try {
      await uploadAttachment(entityType, entityId, file);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      reload();
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (att: Attachment): Promise<void> => {
    setBusy(`${att.id}:download`);
    try {
      await downloadAttachment(att);
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setBusy(null);
    }
  };

  const handleDelete = async (att: Attachment): Promise<void> => {
    setBusy(`${att.id}:delete`);
    try {
      await deleteAttachment(att.id);
      reload();
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setBusy(null);
    }
  };

  return (
    <Card title={t('documents.panel.title')}>
      <div className="stack">
        {error && (
          <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {items === null ? (
          <Spinner size="sm" inline />
        ) : items.length === 0 ? (
          <p className="detail-grid__value">{t('documents.panel.empty')}</p>
        ) : (
          <ul className="attachment-list">
            {items.map((att) => (
              <li className="attachment-list__item" key={att.id}>
                <div className="attachment-list__meta">
                  <span className="attachment-list__name">{att.original_filename}</span>
                  <span className="attachment-list__size">{formatBytes(att.size_bytes)}</span>
                </div>
                <div className="row-actions">
                  <Button
                    size="sm"
                    variant="secondary"
                    loading={busy === `${att.id}:download`}
                    onClick={() => void handleDownload(att)}
                  >
                    {t('documents.actions.download')}
                  </Button>
                  {canDelete && (
                    <Button
                      size="sm"
                      variant="danger"
                      loading={busy === `${att.id}:delete`}
                      onClick={() => void handleDelete(att)}
                    >
                      {t('documents.actions.delete')}
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}

        <form className="attachment-upload" onSubmit={(e) => void handleUpload(e)} noValidate>
          <input
            ref={fileInputRef}
            type="file"
            className="input"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            disabled={uploading}
          />
          <Button type="submit" size="sm" loading={uploading}>
            {t('documents.actions.upload')}
          </Button>
        </form>
      </div>
    </Card>
  );
}
