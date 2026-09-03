# SLZ ERP — VPS Deployment Handoff

**Status:** VPS-VERIFIED — prod compose + Cloudflare Tunnel deployed and
health-checked on a 1-vCPU/4 GB Ubuntu VPS (September 2026). Items below still
marked unverified remain so.

> **Freshness note (2026-09-03):** counts in this doc (18 apps, 342 backend
tests, "costing not yet implemented") are superseded. Current ground truth:
> **22 apps / 381 backend tests / 98 frontend tests**, costing auto-posts
> (RECEIPT + ISSUE + PRODUCTION_OUTPUT), plus planning + recall modules. See
> `docs/PROJECT-STATUS.md` and `docs/FINAL-TEST-VPS-AUDIT.md`. The topology and
> runbook sections below remain accurate.

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

The public name (e.g. `slz.abystral.kdns.fr`) must resolve through Cloudflare
so the edge can terminate TLS and reach the tunnel connector. Two supported
shapes: (1) the zone itself is in Cloudflare, or (2) DNS is hosted elsewhere
(e.g. OVH) and the name is a CNAME into a Cloudflare-for-SaaS custom hostname
on a CF zone. Set `DJANGO_ALLOWED_HOSTS` to the public name plus localhost.

## E. Required environment variables (`erp/.env`)

```
DJANGO_SECRET_KEY=<50+ random chars>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=slz.abystral.kdns.fr,localhost,127.0.0.1
POSTGRES_DB=slz_erp
POSTGRES_USER=slz_erp
POSTGRES_PASSWORD=<generated>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
REDIS_CACHE_URL=redis://redis:6379/2
CORS_ALLOWED_ORIGINS=https://slz.abystral.kdns.fr
AUTH_THROTTLE_RATE=30/min
DOCUMENTS_MAX_UPLOAD_BYTES=26214400
DOCUMENTS_ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg,xlsx,csv
```

## F. Secret generation

```bash
bash erp/scripts/gen-env.sh            # writes erp/.env (random secrets, chmod 600)
bash erp/scripts/gen-env.sh --force    # rotate (then ALTER the postgres role
                                       # password to match and restart the stack)
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
bash scripts/gen-env.sh   # writes erp/.env with real random secrets (600)
docker compose -f docker-compose.prod.yml up -d --build
```

Services: postgres, redis, backend (gunicorn), celery worker, frontend/nginx.

**`docker-compose.yml` is the LOCAL DEV file and `docker-compose.prod.yml` is
standalone production** — never merge the two (compose concatenates `ports`
across files, so overlaying prod settings on the dev file keeps the public dev
publishes). In production NOTHING is published to the public interface: the
frontend nginx binds only `127.0.0.1:80` and the Cloudflare Tunnel connector
(see §S/§T) is the sole public ingress. PostgreSQL/Redis/backend live only on
the compose network.

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

`erp/scripts/backup-erp.sh` handles the nightly ERP backup:

```bash
bash erp/scripts/backup-erp.sh                 # run one backup now
bash erp/scripts/backup-erp.sh --install-cron  # install /etc/cron.d/slz-erp-backup (daily 03:15)
```

It pg_dumps the database through `docker compose exec` (no host port needed),
archives the media volume, verifies both archives, records SHA256, keeps the
newest 30 daily archives (override `BACKUP_RETENTION`), and optionally rsyncs
off-box when `OFFBOX_TARGET=user@host:/path` is set. Test restores quarterly.

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

## S. Firewall / port exposure

No inbound HTTP/S ports are required: the deployment uses a Cloudflare Tunnel
connector (outbound-only). Nothing is published on the public interface — not
5432/6379/8000 (compose-internal only) and not even 80/443 on the box (nginx
binds `127.0.0.1:80`; if port 443 is occupied by another service, e.g. a VPN
VLESS inbound, the tunnel topology avoids the conflict entirely). SSH from
admin IPs only.

## T. HTTPS — Cloudflare Tunnel (verified topology)

Public topology (TLS terminates at the Cloudflare edge):

```text
https://<domain>  ->  Cloudflare edge (TLS)  ->  cloudflared connector
                  ->  http://127.0.0.1:80    ->  nginx (SPA + /api proxy)
```

Setup (see `erp/infrastructure/cloudflared/` for templates):

1. `cloudflared tunnel login` (scoped to the zone hosting the public name),
   `cloudflared tunnel create slz-erp`, then `cloudflared tunnel route dns
   slz-erp <domain>` — the DNS record must live in a Cloudflare zone, or be a
   CNAME at the upstream DNS provider into a Cloudflare-for-SaaS custom
   hostname on a CF zone.
2. Install `/etc/cloudflared/config.yml` (hostname → `http://127.0.0.1:80`)
   and `cloudflared-slz.service`, then `systemctl enable --now cloudflared-slz`.
3. Django prod settings enforce `SECURE_SSL_REDIRECT` via the
   `X-Forwarded-Proto: https` header that cloudflared sends; nginx preserves it
   (`$slz_forwarded_proto` map in nginx.conf) instead of overwriting it with
   `$scheme` — overwriting would cause a redirect loop. The compose healthcheck
   sends the header too so `/ready/` probes return 200, not 301.

## U. Production security checklist

- [x] `DJANGO_DEBUG=False` (prod settings; `gen-env.sh` writes it)
- [x] Unique generated secret key (`scripts/gen-env.sh`, 600 perms; rotate with
      `--force` + restart + postgres `ALTER ROLE`)
- [x] `ALLOWED_HOSTS` exact domains only (from `erp/.env`)
- [x] CORS restricted to the frontend origin
- [x] Auth throttle enabled (default 30/min per IP)
- [x] Admin panel not reachable through nginx (no /admin proxy)
- [x] Uploads: extension allowlist active; virus scanning deferred (documented gap)
- [x] Restricted port exposure (nothing on the public interface; tunnel ingress)
- [x] Backups scheduled (see §O) — restore still to be exercised on a schedule
- [ ] Q-055 memberships provisioned per real org chart (IT-administered)

---

## Known limitations carried into VPS phase

1. Costing engine (dated WA) designed but not yet implemented.
2. Celery workers exist but no task currently requires them locally (eager mode);
   verify async delivery on VPS.
3. Virus scanning of uploads intentionally deferred.
4. Q-038 KPIs and DR-000 remain business-open.
