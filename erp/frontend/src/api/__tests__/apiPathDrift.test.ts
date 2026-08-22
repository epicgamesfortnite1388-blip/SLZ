/**
 * Frontend→backend API path drift guard.
 *
 * Every route-shaped string literal in `src/api/*.ts` must correspond to a
 * backend router registration (the per-app "urls.py" routers plus the root
 * config urls). This is the same class of guarantee as the permission/i18n
 * guards: a typo or stale endpoint here compiles fine but 404s at runtime.
 * The check is heuristic (string-prefix matching against registered
 * prefixes) — it can never produce false positives on paths that DO resolve.
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

// Tests execute with the frontend package root as cwd.
const ROOT = process.cwd();
const SRC = join(ROOT, 'src');
const BACKEND_APPS = join(ROOT, '..', 'backend', 'apps');
const CONFIG_URLS = join(ROOT, '..', 'backend', 'config', 'urls.py');

const PATH_PATTERN = /['"`](\/[a-z0-9][a-zA-Z0-9\-/]*)/g;
const REGISTER_PATTERN = /register\("([^"]+)"/g;
const DJANGO_PATH_PATTERN = /path\("([^"]*)"/g;

function frontendPaths(): Map<string, string[]> {
  const byPath = new Map<string, string[]>();
  const apiDir = join(SRC, 'api');
  expect(existsSync(apiDir), `API layer not found at ${apiDir}`).toBe(true);
  for (const f of readdirSync(apiDir)) {
    if (!f.endsWith('.ts') || f.endsWith('.d.ts') || f.includes('test')) continue;
    const file = join(apiDir, f);
    const source = readFileSync(file, 'utf-8');
    for (const m of source.matchAll(PATH_PATTERN)) {
      byPath.set(m[1], [...(byPath.get(m[1]) ?? []), `api/${f}`]);
    }
  }
  return byPath;
}

function backendPrefixes(): Set<string> {
  expect(existsSync(BACKEND_APPS), `Backend apps not found at ${BACKEND_APPS}`).toBe(true);
  const prefixes = new Set<string>();
  for (const app of readdirSync(BACKEND_APPS)) {
    const urlsFile = join(BACKEND_APPS, app, 'urls.py');
    if (!existsSync(urlsFile)) continue;
    const source = readFileSync(urlsFile, 'utf-8');
    for (const m of source.matchAll(REGISTER_PATTERN)) {
      prefixes.add(`/${app}/${m[1]}/`);
      prefixes.add(`/${app}/${m[1]}`);
    }
  }
  const config = readFileSync(CONFIG_URLS, 'utf-8');
  for (const m of config.matchAll(DJANGO_PATH_PATTERN)) {
    const p = m[1].replace(/\/+$/, '');
    if (p && !p.includes('<')) prefixes.add(`/${p}`);
  }
  return prefixes;
}

describe('frontend→backend API path drift guard', () => {
  it('resolves every frontend API path to a backend registration', () => {
    const backend = backendPrefixes();
    const orphans: string[] = [];
    for (const [p, files] of frontendPaths()) {
      // Drop a trailing dynamic segment (".../{id}") and try the stem too.
      const stem = p.replace(/\/[^/]+$/, '');
      const resolves =
        backend.has(p) ||
        backend.has(stem) ||
        [...backend].some((b) => p.startsWith(b) || b.startsWith(p));
      if (!resolves) orphans.push(`${p} (${files.join(', ')})`);
    }
    expect(orphans).toEqual([]);
  });

  it('scans enough real paths that the scan cannot rot silently', () => {
    expect(frontendPaths().size).toBeGreaterThan(20);
  });
});
