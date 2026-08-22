import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import { isApiError } from '@/api/types';
import {
  uploadAttachment,
  deleteAttachment,
  downloadAttachment,
  formatBytes,
  type Attachment,
} from '@/api/documents';

/**
 * Document register over the generic attachment store. Every file is pinned to
 * a target by (`entity_type`, `entity_id`); the store encodes no rule about what
 * may attach to what, so this screen is a plain register plus an upload card.
 *
 * Uploads need only view access (server default); deleting is gated by
 * `documents.attachment.delete`. Downloads are authenticated — the bytes are
 * fetched with the Bearer token and handed to the browser to save, so no token
 * ever leaks into a plain anchor href.
 */
export function DocumentsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<Attachment>('/documents/attachments/');
  const canDelete = hasPermission('documents.attachment.delete');

  const [entityType, setEntityType] = useState('');
  const [entityId, setEntityId] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);

  const handleUpload = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    if (!file) {
      setError(t('documents.errors.noFile'));
      return;
    }
    setUploading(true);
    try {
      await uploadAttachment(entityType, entityId, file, description);
      setDescription('');
      setFile(null);
      collection.reload();
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
      collection.reload();
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setBusy(null);
    }
  };

  const columns: Column<Attachment>[] = [
    { headerKey: 'documents.fields.filename', render: (r) => r.original_filename },
    {
      headerKey: 'documents.fields.entity',
      render: (r) => `${r.entity_type} #${r.entity_id}`,
    },
    {
      headerKey: 'documents.fields.size',
      render: (r) => formatBytes(r.size_bytes),
      align: 'end',
    },
    {
      headerKey: 'documents.fields.actions',
      align: 'center',
      render: (r) => (
        <div className="row-actions">
          <Button
            size="sm"
            variant="secondary"
            loading={busy === `${r.id}:download`}
            onClick={() => void handleDownload(r)}
          >
            {t('documents.actions.download')}
          </Button>
          {canDelete && (
            <Button
              size="sm"
              variant="danger"
              loading={busy === `${r.id}:delete`}
              onClick={() => void handleDelete(r)}
            >
              {t('documents.actions.delete')}
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="stack">
      {error && (
        <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Card title={t('documents.upload.title')}>
        <form className="stack" onSubmit={(e) => void handleUpload(e)} noValidate>
          <FormField label={t('documents.fields.entityType')} required>
            {({ id }) => (
              <Input
                id={id}
                value={entityType}
                onChange={(e) => setEntityType(e.target.value)}
                placeholder={t('documents.fields.entityTypePlaceholder')}
                disabled={uploading}
                required
              />
            )}
          </FormField>

          <FormField label={t('documents.fields.entityId')} required>
            {({ id }) => (
              <Input
                id={id}
                value={entityId}
                onChange={(e) => setEntityId(e.target.value)}
                disabled={uploading}
                required
              />
            )}
          </FormField>

          <FormField label={t('documents.fields.description')}>
            {({ id }) => (
              <Input
                id={id}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={uploading}
              />
            )}
          </FormField>

          <FormField label={t('documents.fields.file')} required>
            {({ id }) => (
              <input
                id={id}
                type="file"
                className="input"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                disabled={uploading}
                required
              />
            )}
          </FormField>

          <div className="form-actions">
            <Button type="submit" loading={uploading}>
              {t('documents.actions.upload')}
            </Button>
          </div>
        </form>
      </Card>

      <CollectionView
        titleKey="documents.title"
        subtitleKey="documents.subtitle"
        columns={columns}
        rowKey={(r) => r.id}
        collection={collection}
      />
    </div>
  );
}
