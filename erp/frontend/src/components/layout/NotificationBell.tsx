import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { fetchUnreadCount } from '@/api/notifications';

/**
 * Header entry point to the notification inbox. Fetches the unread count once
 * on mount (no polling — the count refreshes on navigation / reload) and shows
 * it as a badge. Links to the full inbox at `/notifications`.
 */
export function NotificationBell(): JSX.Element {
  const { t } = useTranslation();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    let active = true;
    fetchUnreadCount()
      .then((r) => {
        if (active) setUnread(r.unread);
      })
      .catch(() => {
        /* non-blocking: a failed count must never break the header */
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <Link
      to="/notifications"
      className="notif-bell"
      aria-label={t('notifications.title')}
    >
      <span className="notif-bell__label">{t('notifications.title')}</span>
      {unread > 0 && (
        <span className="notif-bell__badge" aria-hidden="true">
          {unread}
        </span>
      )}
    </Link>
  );
}
