# SLZ ERP — VPS Deployment Handoff

**Status:** LOCAL ALPHA READY (verified on Windows dev machine, SQLite).
**Everything below marked NOT YET VERIFIED ON VPS must be executed on an
Ubuntu VPS before the system is considered production-candidate.**

---

## A. Current application state

* Django 4.2 modular monolith — 18 apps, 342 backend tests green (SQLite).
* React 18 + Vite SPA — 90 tests green, typecheck/lint/build clean.
* Confirmed business decisions implemented: serialized rolls (Q-046),
  stage-split issue methods (Q-048), category-based traceability granularity
  (Q-049), stocked WIP intermediates (Q-026), multi-company membership with
  company-granular isolation (Q-055/Q-053).
* Dated weighted-average costing engine: **designed, NOT yet implemented**
  (see `docs/architecture/execution-preparation.md`).

## B. Ubuntu version

Ubuntu **22.04 LTS** or 24.04 LTS. Docker Engine ≥ 24 with Compose v2 plugin.

## C. Recommended server resources

| Component | Minimum |
|---|---|
| CPU | 2 vCPU |
| RAM | 4 GB |
| Disk | 40 GB SSD (incl. DB growth + uploads) |
| Swap | 2 GB |

## D. DNS / domain

Point an A/AAAA record at the VPS IP (e.g. `erp.example.com`). TLS terminates
at nginx (or a reverse-proxy/CDN in front). Set `DJANGO_ALLOWED_HOSTS` to the
domain plus localhost.

## E. Required environment variables (`erp/.env`)

```
DJANGO_SECRET_KEY=<50+ random chars>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=erp.example.com,localhost
POSTGRES_DB=slz_erp
POSTGRES_USER=slz_erp
POSTGRES_PASSWORD=<generated>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
REDIS_CACHE_URL=redis://redis:6379/2
CORS_ALLOWED_ORIGINS=https://erp.example.com
AUTH_THROTTLE_RATE=30/min
VITE_API_BASE_URL=https://erp.example.com/api/v1   # build-time only
DOCUMENTS_MAX_UPLOAD_BYTES=26214400
DOCUMENTS_ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg,xlsx,csv
```

## F. Secret generation

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"   # DJANGO_SECRET_KEY
openssl rand -base64 24                                        # POSTGRES_PASSWORD
```

Never commit `.env`. The repo's `.env.example` lists every variable.

## G. PostgreSQL setup

Provided by `docker-compose.yml` (postgres:16-alpine) with a named volume.
For bare-metal Postgres instead: create the DB/user, grant CREATEDB-free
least-privilege access, set `POSTGRES_*` env vars, and run migrations manually.
**NOT YET VERIFIED ON VPS.**

## H. Redis setup

redis:7-alpine via Compose, three logical DBs (broker/results/cache).
**NOT YET VERIFIED ON VPS.**

## I. Startup

```bash
cd /opt/slz && git clone <repo> slz && cd slz/erp
cp .env.example .env    # then edit secrets
docker compose up --build -d
```

Services: postgres, redis, backend (gunicorn), celery worker, frontend/nginx.

## J. Migrations

```bash
docker compose exec backend python manage.py migrate --noinput
```

Applied by the entrypoint on boot as well; CI enforces no drift.

## K. RBAC seed

```bash
docker compose exec backend python manage.py seed_rbac
docker compose exec backend python manage.py seed_demo_data   # demo only — skip in production
```

Create the real superuser:

```bash
docker compose exec backend python manage.py createsuperuser
```

## L. Frontend/backend startup

Backend: gunicorn (3 workers) behind nginx; static served by WhiteNoise.
Frontend: built by its container into nginx; `/api/` proxied to backend.
Both restart under `restart: unless-stopped` in compose.

## M. Health checks

```
GET /health/   → {"status": "ok"}          (liveness)
GET /ready/    → database ok, cache ok     (readiness; used by compose)
```

## N. Smoke tests (first VPS bring-up)

1. `/health/` + `/ready/` return 200.
2. Login with the superuser → tokens returned.
3. `GET /api/v1/auth/users/` → 200.
4. Create partner → appears in list → audit row exists.
5. Create PO (APPROVED) → post GRN → traceability unit + IN movement exist.
6. Switch company context → data changes accordingly.

Full checklist: `docs/LOCAL-ALPHA-CHECKLIST.md` (steps apply identically).

## O. Backups

Nightly:

```bash
docker compose exec postgres pg_dump -U slz_erp slz_erp | gzip > backup-$(date +%F).sql.gz
tar czf media-$(date +%F).tgz /var/lib/docker/volumes/*_media_data/_data
```

Ship off-box (rsync/S3). Retain ≥ 30 days. Test restores quarterly.

## P. Restore

```bash
docker compose down
# restore volumes / start postgres only
gunzip -c backup.sql.gz | docker compose exec -T postgres psql -U slz_erp slz_erp
docker compose up -d
```

## Q. Logs

`docker compose logs -f backend celery` — structured single-line logs with
`correlation_id=` on every request/error line. Ship to journald/Loki.

## R. Rollback

Images are rebuilt from git tags; rollback = `git checkout <previous-tag>`
then `docker compose up --build -d`. Migrations are forward-only: pair
destructive migrations with documented reversals before release.

## S. Firewall

Allow 80/443 in, SSH from admin IPs only. Postgres/Redis bind inside the
compose network only — never publish 5432/6379.

## T. HTTPS

Terminate TLS at nginx (certbot) or a load balancer; redirect 80→443;
set `SECURE_SSL_REDIRECT`, `SECURE_PROXY_SSL_HEADER`,
`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS` in
production settings before go-live.

## U. Production security checklist

- [ ] `DJANGO_DEBUG=False`
- [ ] Unique generated secret key, rotated quarterly
- [ ] `ALLOWED_HOSTS` exact domains only
- [ ] CORS restricted to the frontend origin
- [ ] Auth throttle enabled (default 30/min per IP)
- [ ] Admin panel either disabled or IP-restricted
- [ ] Uploads: extension allowlist active; virus scanning deferred (documented gap)
- [ ] Backups scheduled AND restore tested
- [ ] Q-055 memberships provisioned per real org chart (IT-administered)

---

## Known limitations carried into VPS phase

1. Costing engine (dated WA) designed but not yet implemented.
2. Celery workers exist but no task currently requires them locally (eager mode);
   verify async delivery on VPS.
3. Virus scanning of uploads intentionally deferred.
4. Q-038 KPIs and DR-000 remain business-open.
