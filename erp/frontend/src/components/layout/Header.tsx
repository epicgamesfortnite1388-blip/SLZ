import { useTranslation } from 'react-i18next';
import { LanguageSwitcher } from './LanguageSwitcher';
import { NotificationBell } from './NotificationBell';
import { UserMenu } from './UserMenu';

/** App header: brand, language switcher, and user menu. */
export function Header(): JSX.Element {
  const { t } = useTranslation();
  return (
    <header className="header">
      <div className="header__brand">
        <span className="header__mark" aria-hidden="true">
          SLZ
        </span>
        <span>{t('app.title')}</span>
      </div>
      <div className="header__actions">
        <NotificationBell />
        <LanguageSwitcher />
        <UserMenu />
      </div>
    </header>
  );
}
