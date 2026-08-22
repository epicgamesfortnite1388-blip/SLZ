# SLZ ERP — Release Checklist & Recovery Procedures

Practical, executable checklist for releasing the SLZ ERP. Items marked
**IMPLEMENTED** are automated or built; **PROCEDURE** items are manual steps
documented here (no fake infrastructure is implied).

---

## 0. Prerequisites

- [ ] Docker + Docker Compose v2 on the target host (`docker compose version`)
- [ ] Python 3.11 / Node 20 match CI and the images
- [ ] Access to the GitHub repo and to the target server's secret store

## 1. Dependencies

- [ ] Backend: `pip install -r erp/backend/requirements/prod.txt` (pinned)
- [ ] Frontend: `npm ci` in `erp/frontend` (lockfile-exact — never `npm install`)
- [ ] CI enforces both on every push (`.github/workflows/ci.yml`)

## 2. Environment configuration

- [ ] Copy `erp/.env.example` → `erp/.env`; set at minimum:
  - `DJANGO_SECRET_KEY` (random ≥50 chars — prod settings **refuse to boot**
    with the dev placeholder), `DJANGO_DEBUG=false`, real `DJANGO_ALLOWED_HOSTS`,
    `POSTGRES_*` credentials, `CORS_ALLOWED_ORIGINS` for the SPA origin,
    optional `ADMIN_EMAIL`/`ADMIN_PASSWORD` bootstrap superuser
- [ ] Confirm `.env` is NOT committed (`.gitignore` excludes it; only
  `.env.example` templates are tracked)
- [ ] Review tunables: `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS`,
  `AUTH_THROTTLE_RATE` (login/refresh per-IP limit), `DOCUMENTS_MAX_UPLOAD_BYTES`,
  `DOCUMENTS_ALLOWED_EXTENSIONS`

## 3. Database migrations

- [ ] CI already ran `makemigrations --check --dry-run --noinput`
      (drift ⇒ red build). Locally: `make migrations-check-local`.
- [ ] Migrations are applied by the container entrypoint on startup
      (**IMPLEMENTED**, idempotent). The entrypoint deliberately does NOT
      generate migrations at deploy time.
- [ ] Review `git diff <last-release>..HEAD -- '**/migrations/'` and read any
      new migration before shipping it.

## 4. Seed data

- [ ] `python manage.py seed_rbac` (entrypoint runs it automatically;
      idempotent). Seeds the permission catalogue + `platform_admin` role
      only — no business data exists to seed.

## 5–9. Verification gates (all **IMPLEMENTED** in CI)

Run locally as one command: `make verify-local` (or let CI do it):

- [ ] Backend tests: `python manage.py test --settings=config.settings.test --noinput`
- [ ] Migration drift check (see §3)
- [ ] flake8 + black + isort clean
- [ ] Frontend: `npm run typecheck && npm run lint && npm run test && npm run build`

## 10. Security checks

- [ ] `DJANGO_DEBUG=false`, `ALLOWED_HOSTS` explicit (prod defaults are safe:
      HTTPS redirect, HSTS, secure cookies, nosniff, `X-Frame-Options: DENY`)
- [ ] TLS termination in front of gunicorn/nginx
- [ ] No secrets in the image or repo; secrets come from the environment only
- [ ] Spot-check `/api/v1/auth/login/` throttling and that unauthenticated
      requests get 401 envelopes

## 11. Database & media backup (**PROCEDURE**)

Backups are NOT automated — schedule these on the host:

```bash
# Postgres logical backup (inside the compose stack)
docker compose -f erp/docker-compose.yml exec postgres \
  pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" > "backup-$(date +%F-%H%M).dump"

# Uploaded attachments live on the named volume `media_data`
docker run --rm -v slz_media_data:/data:ro -v "$PWD":/out alpine \
  tar czf /out/media-$(date +%F-%H%M).tar.gz -C /data .
```

Store copies off-host. Test a restore quarterly.

## 12. Deployment

```bash
git fetch origin && git checkout <release-tag>
cd erp && docker compose pull || docker compose build
docker compose up -d          # entrypoint: wait-for-db → migrate → seed_rbac
docker compose logs -f backend
```

## 13. Smoke tests

- [ ] `curl -fsS http://<host>/health/` → `{"status": "ok"}`
- [ ] `curl -fsS http://<host>/ready/` → database+cache checks `"ok"`
- [ ] Log in via the SPA with the bootstrap admin; dashboard tiles render
- [ ] Create one record in a master-data module; confirm it appears and lands
      in the audit trail (`/audit/logs`)

## 14. Rollback (**PROCEDURE**)

- Code: redeploy the previous git tag (images are rebuilt from source).
- Schema: Django cannot auto-reverse arbitrary migrations. Prefer rolling
  *forward* a fix; if reversal is unavoidable use
  `docker compose exec backend python manage.py migrate <app>.<migration>`
  **only after reviewing that migration's `Reverse` operations**, and after
  restoring the pre-release `pg_dump` if data was destructive.
- Data: restore from §11 backups into a fresh volume, then start the previous
  release against it.

---

## Known verification gap

The full container path (image builds, PostgreSQL/Redis under Compose,
nginx serving) has not been executed in this environment — no Docker daemon
was available. Application logic itself is fully verified (237 backend /
75 frontend tests, migration-drift gate, lint/typecheck/build green).
Running §12–13 once on a Docker-capable host is the remaining deployment
verification requirement.
