/**
 * Permission-code drift guard.
 *
 * Every permission code referenced by the UI (`hasPermission('…')` /
 * `requiredPermission="…"`) must exist in the canonical RBAC seed
 * (`backend/apps/identity/management/commands/seed_rbac.py`). A typo here
 * compiles fine but renders the gated surface permanently forbidden to
 * non-superusers — exactly the drift this test fails on. Test fixtures are
 * excluded from the scan because they deliberately use fake codes.
 */
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

// Tests execute with the frontend package root as cwd.
const ROOT = process.cwd();
const SRC = join(ROOT, 'src');
const SEED_FILE = join(
  ROOT,
  '..',
  'backend',
  'apps',
  'identity',
  'management',
  'commands',
  'seed_rbac.py',
);

const CODE_PATTERN =
  /requiredPermission="([a-z]+\.[a-z]+\.[a-z]+)"|hasPermission\('([a-z]+\.[a-z]+\.[a-z]+)'\)/g;
/** Mirrors the seed's `(code, name_en, name_fa)` triple entries. */
const SEED_ENTRY_PATTERN = /"([a-z]+\.[a-z]+\.[a-z]+)"/g;

function listFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      // Fixtures intentionally contain fake codes; never scan them.
      return entry === '__tests__' ? [] : listFiles(full);
    }
    return /\.(ts|tsx)$/.test(entry) ? [full] : [];
  });
}

function uiPermissionCodes(): Map<string, string[]> {
  const byCode = new Map<string, string[]>();
  for (const file of listFiles(SRC)) {
    const source = readFileSync(file, 'utf-8');
    for (const match of source.matchAll(CODE_PATTERN)) {
      const code = match[1] ?? match[2];
      byCode.set(code, [...(byCode.get(code) ?? []), file]);
    }
  }
  return byCode;
}

function seededCodes(): Set<string> {
  expect(existsSync(SEED_FILE), `RBAC seed not found at ${SEED_FILE}`).toBe(true);
  const source = readFileSync(SEED_FILE, 'utf-8');
  return new Set(
    [...source.matchAll(SEED_ENTRY_PATTERN)].map((m) => m[1]),
  );
}

describe('permission-code guard', () => {
  it('only references permission codes that exist in the RBAC seed', () => {
    const seeded = seededCodes();
    const violations = [...uiPermissionCodes()]
      .filter(([code]) => !seeded.has(code))
      .map(([code, files]) => `${code} (${files.length} file(s))`);

    expect(violations).toEqual([]);
  });

  it('finds enough real codes that the scan cannot rot silently', () => {
    expect(uiPermissionCodes().size).toBeGreaterThan(30);
  });
});
