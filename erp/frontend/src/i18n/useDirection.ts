/**
 * Keeps `document.documentElement.dir` and `lang` in sync with the active
 * i18next language. Mount once near the app root.
 */
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { directionForLanguage } from './index';

export function useDirection(): { language: string; dir: 'rtl' | 'ltr' } {
  const { i18n } = useTranslation();
  const language = i18n.resolvedLanguage ?? i18n.language;
  const dir = directionForLanguage(language);

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute('dir', dir);
    root.setAttribute('lang', language);
  }, [dir, language]);

  return { language, dir };
}
