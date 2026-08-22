import { useTranslation } from 'react-i18next';
import { Alert, Button } from '@/components/ui';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import { useAsyncAction } from '@/hooks/useAsyncAction';
import {
  markAllNotificationsRead,
  markNotificationRead,
  type Notification,
} from '@/api/notifications';

/**
 * The signed-in user's in-app notification inbox. The backend scopes every
 * endpoint to the requesting user, so the page needs authentication only — no
 * module permission. Read one item, or clear all unread at once.
 */
export function NotificationsPage(): JSX.Element {
  const { t } = useTranslation();
  const collection = useCollection<Notification>('/notifications/');
  const action = useAsyncAction();

  const readOne = (id: string): Promise<boolean> =>
    action.run(id, async () => {
      await markNotificationRead(id);
      collection.reload();
    });

  const readAll = (): Promise<boolean> =>
    action.run('all', async () => {
      await markAllNotificationsRead();
      collection.reload();
    });

  const columns: Column<Notification>[] = [
    {
      headerKey: 'notifications.fields.type',
      render: (r) => t(`notifications.types.${r.type}`),
    },
    {
      headerKey: 'notifications.fields.title',
      render: (r) => (
        <span className={r.is_read ? undefined : 'is-unread'}>{r.title}</span>
      ),
    },
    { headerKey: 'notifications.fields.body', render: (r) => r.body || '—' },
    {
      headerKey: 'notifications.fields.state',
      render: (r) =>
        r.is_read ? t('notifications.states.read') : t('notifications.states.unread'),
    },
    {
      headerKey: 'notifications.fields.actions',
      align: 'center',
      render: (r) =>
        r.is_read ? (
          '—'
        ) : (
          <Button
            size="sm"
            variant="secondary"
            loading={action.busy === r.id}
            onClick={() => void readOne(r.id)}
          >
            {t('notifications.actions.markRead')}
          </Button>
        ),
    },
  ];

  return (
    <div className="stack">
      {action.error && (
        <Alert variant="danger" title={t('common.error')}>
          <p>{action.error.message}</p>
          <Button variant="secondary" size="sm" onClick={action.clearError}>
            {t('common.close')}
          </Button>
        </Alert>
      )}
      <CollectionView
        titleKey="notifications.title"
        subtitleKey="notifications.subtitle"
        columns={columns}
        rowKey={(r) => r.id}
        collection={collection}
        headerAction={
          <Button
            size="sm"
            variant="secondary"
            loading={action.busy === 'all'}
            onClick={() => void readAll()}
          >
            {t('notifications.actions.markAllRead')}
          </Button>
        }
      />
    </div>
  );
}
