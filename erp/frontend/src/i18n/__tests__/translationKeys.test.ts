/**
 * Translation-key drift guard.
 *
 * Every static key passed to `t('…')` must exist in BOTH locale files, and
 * every dynamic prefix used in a template key (`t(`prefix.${x}`)`) must match
 * at least one real key per locale. A missing key renders its raw path to the
 * user — exactly what this test prevents from landing.
 */
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

// Tests execute with the frontend package root as cwd.
const ROOT = process.cwd();
const SRC = join(ROOT, 'src');
const LOCALES = ['en', 'fa'] as const;

const STATIC_KEY_PATTERN = /\bt\('([a-zA-Z0-9_.]+)'\)/g;
const DYNAMIC_PREFIX_PATTERN = /\bt\(`([a-zA-Z0-9_.]+)\$\{/g;

function listFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      // Test fixtures intentionally reference fake keys; never scan them.
      return entry === '__tests__' ? [] : listFiles(full);
    }
    return /\.(ts|tsx)$/.test(entry) ? [full] : [];
  });
}

function flatten(obj: unknown, prefix = ''): string[] {
  return Object.entries(obj ?? {}).flatMap(([key, value]) =>
    value && typeof value === 'object'
      ? flatten(value, `${prefix}${key}.`)
      : [`${prefix}${key}`],
  );
}

function loadLocaleKeys(locale: (typeof LOCALES)[number]): Set<string> {
  const file = join(SRC, 'i18n', 'locales', `${locale}.json`);
  expect(existsSync(file), `Locale file missing: ${file}`).toBe(true);
  return new Set(flatten(JSON.parse(readFileSync(file, 'utf-8'))));
}

function scanSources(): { staticKeys: Map<string, string[]>; prefixes: Set<string> } {
  const staticKeys = new Map<string, string[]>();
  const prefixes = new Set<string>();
  for (const file of listFiles(SRC)) {
    const source = readFileSync(file, 'utf-8');
    for (const match of source.matchAll(STATIC_KEY_PATTERN)) {
      staticKeys.set(match[1], [...(staticKeys.get(match[1]) ?? []), file]);
    }
    for (const match of source.matchAll(DYNAMIC_PREFIX_PATTERN)) {
      prefixes.add(match[1]);
    }
  }
  return { staticKeys, prefixes };
}

describe('translation-key guard', () => {
  it('resolves every static t() key in every locale', () => {
    const { staticKeys } = scanSources();
    for (const locale of LOCALES) {
      const keys = loadLocaleKeys(locale);
      const missing = [...staticKeys.keys()]
        .filter((key) => !keys.has(key))
        .map((key) => `${key} (${staticKeys.get(key)!.length} use(s))`);
      expect(missing, `Missing ${locale} keys`).toEqual([]);
    }
  });

  it('matches at least one real key for every dynamic key prefix', () => {
    const { prefixes } = scanSources();
    for (const locale of LOCALES) {
      const keys = loadLocaleKeys(locale);
      const orphaned = [...prefixes].filter(
        (prefix) => ![...keys].some((key) => key.startsWith(prefix)),
      );
      expect(orphaned, `Dynamic prefixes with no ${locale} keys`).toEqual([]);
    }
  });

  it('finds enough keys that the scan cannot rot silently', () => {
    expect(scanSources().staticKeys.size).toBeGreaterThan(100);
  });
});
