/**
 * Locale-aware date presentation.
 *
 * The API contract stays canonical UTC ISO — nothing here changes what is sent
 * or stored. This layer only renders, following the platform convention
 * (docs/architecture: UTC canonical; Jalali at the presentation layer):
 *
 *   fa → Solar Hijri (Jalali) with Persian digits  e.g. ۱۴۰۵/۰۵/۳۱ ۱۴:۰۵
 *   en → Gregorian                                 e.g. 2026-08-22 14:05
 *
 * Conversion uses `jalaali-js`; rendering happens in the viewer's local
 * timezone via the standard `Date` getters, consistent with the rest of the
 * SPA. Date-only strings (no time part) render without a time component.
 */
import { toJalaali } from 'jalaali-js';

const pad = (n: number): string => String(n).padStart(2, '0');

const PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹';

function toPersianDigits(text: string): string {
  return text.replace(/\d/g, (d) => PERSIAN_DIGITS[Number(d)]);
}

/** True when the string is a plain calendar date (YYYY-MM-DD), no time. */
export function isDateOnly(iso: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(iso);
}

/**
 * Format an ISO datetime/date-only string for display.
 * Unparseable input is returned unchanged; null/undefined renders as a dash.
 */
export function formatDateTime(
  iso: string | null | undefined,
  lang: string = 'en',
): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;

  const dateOnly = isDateOnly(iso);
  const time = dateOnly ? '' : ` ${pad(d.getHours())}:${pad(d.getMinutes())}`;

  if (lang === 'fa') {
    const j = toJalaali(d.getFullYear(), d.getMonth() + 1, d.getDate());
    return toPersianDigits(`${j.jy}/${pad(j.jm)}/${pad(j.jd)}${time}`);
  }
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}${time}`;
}
