/**
 * i18next initialization for the SLZ ERP frontend.
 *
 * Supported languages: `en` (LTR) and `fa` (RTL). Language detection uses
 * localStorage then the browser; the resolved language is persisted.
 */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import type { Language } from '@/api/types';
import en from './locales/en.json';
import fa from './locales/fa.json';

export const SUPPORTED_LANGUAGES: readonly Language[] = ['en', 'fa'] as const;
export const DEFAULT_LANGUAGE: Language = 'fa';

/** Text direction for a given language. */
export function directionForLanguage(language: string): 'rtl' | 'ltr' {
  return language.startsWith('fa') ? 'rtl' : 'ltr';
}

export const resources = {
  en: { translation: en },
  fa: { translation: fa },
} as const;

if (!i18n.isInitialized) {
  void i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
      resources,
      fallbackLng: DEFAULT_LANGUAGE,
      supportedLngs: [...SUPPORTED_LANGUAGES],
      nonExplicitSupportedLngs: true,
      load: 'languageOnly',
      interpolation: { escapeValue: false },
      detection: {
        order: ['localStorage', 'navigator', 'htmlTag'],
        lookupLocalStorage: 'slz_erp_language',
        caches: ['localStorage'],
      },
      returnNull: false,
    });
}

export default i18n;
