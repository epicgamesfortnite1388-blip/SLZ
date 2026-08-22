import { describe, it, expect } from 'vitest';
import { formatDateTime, isDateOnly } from '../dates';

/**
 * Inputs are built from LOCAL date components so the expected output is
 * independent of the machine's timezone: the ISO round-trip renders the same
 * wall-clock parts that were put in.
 */
function isoLocal(y: number, m: number, d: number, hh = 0, mm = 0): string {
  return new Date(y, m - 1, d, hh, mm).toISOString();
}

describe('formatDateTime (Jalali / Gregorian presentation)', () => {
  it('renders Jalali with Persian digits for fa', () => {
    // Nowruz anchor: 2026-03-21 is 1 Farvardin 1405.
    expect(formatDateTime(isoLocal(2026, 3, 21), 'fa')).toBe('۱۴۰۵/۰۱/۰۱ ۰۰:۰۰');
    // 2026-08-22 is 31 Mordad 1405.
    expect(formatDateTime(isoLocal(2026, 8, 22, 14, 5), 'fa')).toBe('۱۴۰۵/۰۵/۳۱ ۱۴:۰۵');
  });

  it('renders Gregorian for en', () => {
    expect(formatDateTime(isoLocal(2026, 8, 22, 14, 5), 'en')).toBe('2026-08-22 14:05');
  });

  it('defaults to Gregorian for any non-fa language', () => {
    expect(formatDateTime(isoLocal(2026, 8, 22), 'de')).toBe('2026-08-22 00:00');
  });

  it('drops the time part for date-only strings', () => {
    expect(formatDateTime('2026-08-22', 'en')).toBe('2026-08-22');
    expect(formatDateTime('2026-08-22', 'fa')).toBe('۱۴۰۵/۰۵/۳۱');
  });

  it('renders null as a dash and passes garbage through unchanged', () => {
    expect(formatDateTime(null, 'fa')).toBe('—');
    expect(formatDateTime(undefined, 'en')).toBe('—');
    expect(formatDateTime('not-a-date', 'en')).toBe('not-a-date');
  });

  it('detects date-only strings', () => {
    expect(isDateOnly('2026-08-22')).toBe(true);
    expect(isDateOnly('2026-08-22T10:00:00Z')).toBe(false);
  });
});
