/* eslint-disable */
// Dev-only audit script: extract API paths used by the frontend and compare
// with backend router registrations. Not part of the test suite.
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const apiDir = path.join(ROOT, 'src', 'api');
const paths = new Set();

for (const f of fs.readdirSync(apiDir)) {
  if (!f.endsWith('.ts') || f.includes('test')) continue;
  const s = fs.readFileSync(path.join(apiDir, f), 'utf8');
  // Match string literals beginning with a route-looking slash path.
  for (const m of s.matchAll(/['"`](\/[a-z0-9][a-zA-Z0-9\-/]*)/g)) {
    paths.add(m[1]);
  }
}

// Backend: collect router prefixes + registered viewset prefixes per app urls.py.
const appsDir = path.join(ROOT, '..', 'backend', 'apps');
const backend = new Set();
for (const app of fs.readdirSync(appsDir)) {
  const urlsFile = path.join(appsDir, app, 'urls.py');
  if (!fs.existsSync(urlsFile)) continue;
  const s = fs.readFileSync(urlsFile, 'utf8');
  for (const m of s.matchAll(/register\("([^"]+)"/g)) {
    backend.add(`/${app}/${m[1]}/`);
    backend.add(`/${app}/${m[1]}`);
  }
}
for (const m of fs
  .readFileSync(path.join(ROOT, '..', 'backend', 'config', 'urls.py'), 'utf8')
  .matchAll(/path\("([^"]*)"/g)) {
  if (m[1] && !m[1].includes('<')) backend.add(`/${m[1].replace(/\/$/, '')}`);
}

console.log('--- frontend paths not obviously matching a backend registration ---');
for (const p of [...paths].sort()) {
  const stripped = p.replace(/\/[^/]+$/, ''); // drop trailing id segment
  const hit =
    backend.has(p) ||
    backend.has(stripped) ||
    [...backend].some((b) => p.startsWith(b) || b.startsWith(p));
  if (!hit) console.log(p);
}
console.log('--- done ---');
