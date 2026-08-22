# SLZ ERP — Frontend Foundation Shell

Bilingual (Persian / English) frontend shell for the **SLZ ERP**, a custom
ERP/MES for صنایع لفاف زرین (flexible-packaging, make-to-order).

This is a **foundation shell only**: authentication, routing, an RTL/LTR-aware
app layout, a small design-system, and i18n plumbing. It intentionally contains
**no business/ERP screens and no fake ERP data** — those are built on top of
this shell.

## Tech stack

- **Vite** + **React 18** + **TypeScript** (strict mode)
- **react-router-dom v6** for routing and guards
- **i18next** + **react-i18next** for `fa` / `en` localization
- **Vitest** + **@testing-library/react** + **jsdom** for tests
- Plain CSS with custom properties (design tokens). Full RTL/LTR support via
  `document.documentElement.dir` / `lang`.

## Getting started

```bash
npm install
cp .env.example .env   # adjust VITE_API_BASE_URL if needed
npm run dev
```

The app expects the SLZ ERP backend to be reachable at `VITE_API_BASE_URL`
(default `http://localhost:8000/api/v1`).

## Scripts

| Script              | Description                                  |
| ------------------- | -------------------------------------------- |
| `npm run dev`       | Start the Vite dev server                    |
| `npm run build`     | Type-check (project refs) and build for prod |
| `npm run preview`   | Preview the production build                 |
| `npm test`          | Run the test suite once (Vitest)             |
| `npm run test:watch`| Run tests in watch mode                      |
| `npm run lint`      | Lint with ESLint (no warnings allowed)       |
| `npm run typecheck` | Type-check without emitting                  |

## Environment

| Variable            | Default                             | Description             |
| ------------------- | ----------------------------------- | ----------------------- |
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1`      | Backend API base URL    |

## Architecture

```
src/
  api/            Fetch client (Bearer + X-Correlation-ID + 401 refresh), auth calls, types
  auth/           AuthContext + useAuth (tokens, session restore, hasPermission)
  components/
    layout/       AppShell, Header, Sidebar, LanguageSwitcher, UserMenu
    ui/           Button, Input, Card, Spinner, Alert, FormField
    ErrorBoundary, LoadingScreen
  i18n/           i18next init + en/fa locale bundles + useDirection
  pages/          LoginPage, DashboardPage, NotFoundPage, ForbiddenPage
  routes/         ProtectedRoute (auth guard + optional permission guard)
  styles/         theme.css (design tokens), global.css (base + RTL rules)
  test/           Vitest setup
```

### Auth flow

- `POST /auth/login/` returns `{ access, refresh, user }`.
- The access token is held **in memory**; the refresh token is persisted in
  `localStorage` so a page reload can restore the session.
- On mount, if a refresh token exists, the app calls `/auth/refresh/` then
  `/auth/me/` to restore the session.
- The API client retries a request **once** after a `401` by refreshing the
  access token, then replaying the original request.

### Permissions

Permission codes follow `module.resource.action` (e.g.
`organization.company.view`). `hasPermission(code)` returns `true` for
superusers (bypass) or when the code is in the user's `permissions` list.
Sidebar items and protected routes can require a permission.

## Notes for the next engineer

- Dependency versions are **pinned** in `package.json`.
- `npm install` has **not** been run here — install before building.
- No network calls happen in tests; `fetch` is mocked.
