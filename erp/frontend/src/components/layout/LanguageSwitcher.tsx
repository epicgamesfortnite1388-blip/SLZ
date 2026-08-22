import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGUAGES } from '@/i18n';
import type { Language } from '@/api/types';

/** fa/en toggle. Changing language updates i18next; direction is handled by useDirection. */
export function LanguageSwitcher(): JSX.Element {
  const { i18n, t } = useTranslation();
  const current = (i18n.resolvedLanguage ?? i18n.language ?? 'fa').slice(0, 2);

  const change = (lng: Language): void => {
    if (lng !== current) {
      void i18n.changeLanguage(lng);
    }
  };

  return (
    <div className="lang-switch" role="group" aria-label={t('language.switchTo')}>
      {SUPPORTED_LANGUAGES.map((lng) => (
        <button
          key={lng}
          type="button"
          className={`lang-switch__btn${lng === current ? ' is-active' : ''}`}
          aria-pressed={lng === current}
          onClick={() => change(lng)}
        >
          {t(`language.${lng}`)}
        </button>
      ))}
    </div>
  );
}
