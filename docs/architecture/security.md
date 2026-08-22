# Security

The security baseline for the platform. Business modules inherit these
mechanisms and must not weaken them.

## Authentication

- JWT via `djangorestframework-simplejwt`. Access tokens are short-lived
  (`JWT_ACCESS_MINUTES`, default 60); refresh tokens rotate on use and the prior
  token is **blacklisted** (`token_blacklist` app), so a stolen-then-refreshed
  token is invalidated.
- Logout blacklists the presented refresh token.
- The custom `User` (app `identity`) uses **email as the username field**, has a
  UUID PK, and carries `language` and `timezone` for per-user localization.
- Passwords are hashed with Django's configured hashers (PBKDF2 by default).
  The fast MD5 hasher is used **only** in the test settings.

## RBAC

Authorization is role-based with a strict permission grammar:

```
module.resource.action        e.g.  organization.company.view
                                     identity.role.manage
                                     audit.log.view
```

Model (app `identity`):

- `Permission` — `code` (the triplet) + derived `module`.
- `Role` — `code`, bilingual names, `is_system`, M2M to permissions.
- `UserRole` — assigns roles to users; a user's effective permissions are the
  union across roles.

Enforcement:

- Roles are **never hard-coded**. `seed_rbac` seeds the platform permissions and
  a single `platform_admin` system role; everything else is data.
- Views declare a `permission_map` (per verb) or a `required_permission`; the
  `HasPermission` DRF permission class checks the acting user's permission codes.
- **Superusers bypass** permission checks (break-glass / bootstrap).
- Denials return `AuthorizationError` (403); unauthenticated access returns
  `AuthenticationError` (401).

Grant the least privilege necessary; prefer new fine-grained permissions over
broad ones.

## File / document security

The `documents` app treats uploads as hostile:

- **Validation** — size limit (`DOCUMENTS_MAX_UPLOAD_BYTES`) and an
  **allow-list** of extensions (`DOCUMENTS_ALLOWED_EXTENSIONS`); anything else
  is rejected with `validation_error`.
- **Filename safety** — original names are sanitized; the stored object uses an
  **opaque UUID storage key**, so user-controlled names never touch the
  filesystem path and cannot cause traversal or collisions.
- **Integrity** — a SHA-256 checksum is computed and stored on upload.
- **Storage abstraction** — a wrapper over Django storage (`DocumentStorage`)
  keeps the app swap-ready for S3/MinIO without code changes elsewhere.
- **Authorized, streamed download** — downloads go through a permission-checked
  view that streams the object and restores the original filename; storage keys
  are never exposed directly.

## Transport, hosts & CORS

- `ALLOWED_HOSTS` is environment-driven; production settings **refuse to start**
  with the default/placeholder secret key.
- CORS is restricted to configured origins (`CORS_ALLOWED_ORIGINS`), defaulting
  to the local SPA dev origin only.
- Behind the reverse proxy (nginx), terminate TLS and forward the correlation
  header; the SPA is served with an SPA fallback and `/api` proxied to the
  backend.

## Secrets & configuration

- All secrets come from the environment (`.env` → `config/env.py`); **no real
  secrets** live in the repo. `.env.example` documents every variable with safe
  placeholders.
- `DJANGO_DEBUG` defaults off in production; debug tracebacks are never returned
  to clients — unexpected errors surface as a generic `system_error` with a
  correlation id for server-side lookup.

## Auditability

Security-relevant actions (`LOGIN`, `LOGOUT`, permission-gated mutations,
approvals) are captured in the append-only audit trail with actor and
correlation id — see [data-lifecycle.md](data-lifecycle.md#audit-trail--generic-and-module-independent).

## Baseline checklist for new modules

1. Every endpoint has an explicit permission; no anonymous mutations.
2. New permissions follow `module.resource.action` and are seeded as data.
3. User input validated at the serializer boundary; invariants in services.
4. No secrets in code; new config via env with an `.env.example` entry.
5. State-changing actions publish events so they are audited.
6. Uploads go through the `documents` validation/storage path — never ad-hoc.
