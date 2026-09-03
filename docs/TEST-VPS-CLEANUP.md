# SLZ ERP — Test VPS Cleanup Report

**Date:** 2026-09-03 (final handoff)
**Host:** `abyss.aeza.network` (1 vCPU / 3.8 GiB RAM / 9.8 GB disk, no swap)
**Scope:** remove only what this session's engineering test work installed; the
application, its data, and pre-existing services were preserved.

---

## VPS Before (observed at session start / prior state)

- Docker daemon present; `postgres:16-alpine` / `redis:7-alpine` images and
  the ERP stack were brought up and rebuilt during the session (final stack:
  5 containers, see Final Health).
- Disk at ~92% (≈840 MB free) after image builds + an earlier prune.
- Pre-existing host services: ssh, fail2ban, postfix, chrony, x-ui + xray
  (VPN), cloudflared, qemu-guest-agent, Docker engine, unattended-upgrades.
- No swap configured (pre-existing).
- Note: the process listening on host `*:6379` was **the redis container's
  process** (parent = containerd-shim for `erp-redis-1`), not a stray host
  service — nothing to clean there.

## Installed During Test (confirmed agent-installed)

| Item | Purpose | Disposition |
|---|---|---|
| `erp/backend/.venv` (Python 3.14 venv, 101 MB) | host-side backend tests/lint | **Removed** (re-create: README quick-start) |
| `erp/frontend/node_modules` (139 MB) + `dist` (build output) | host-side frontend gates/build | **Removed** (re-create: `npm ci`) |
| Docker build cache (≈872 MB reclaimable) | this session's image builds | **Pruned** (`docker builder prune -f`) |
| `/tmp/slz_erp_test_*.sqlite3` + `/tmp/slz_erp_test_media` | Django test databases | **Removed** |
| `/tmp/app_routes*.txt`, `/tmp/fe_paths.txt`, `/tmp/nav_targets.txt`, `/tmp/audit-task.txt`, `/tmp/infra-audit.*`, `/tmp/node-compile-cache`, `/tmp/slz_pg_test.py` | audit/verification scratch files | **Removed** |
| `.agent-work/logs/*` (build/test/gate logs, ≈250 KB) | evidence of this session's verification runs | **Preserved** (kept on disk; not committed) |
| `agent/.keys.json` | subagent harness API keys (user's keys, git-ignored) | **Preserved** (kept; needed by the harness; never committed) |
| ERP container images (`erp-backend`, `erp-celery`, `erp-frontend`) + postgres/redis images | the deployed application | **Preserved** (application stays) |

## Modified During Test (confirmed agent modifications)

| Item | Change | Disposition |
|---|---|---|
| `erp/.env` | real secrets generated/rotated (`gen-env.sh --force`), postgres role password rotated | **Kept** — required by the running stack; git-ignored; 600 perms |
| nginx `limit_req_zone` placement | moved from `server` block to `http` context (config fix) | **Kept** — committed repo fix (`erp/infrastructure/docker/nginx.conf`) |
| backend entrypoint permissions | `chmod 755` so non-root appuser can run it | **Kept** — committed repo fix |
| Celery start behavior | no longer re-runs migrate/seed (backend owns it) | **Kept** — committed repo fix |
| `/etc/cloudflared/config.yml` + `cloudflared-slz.service` | dedicated SLZ-ERP tunnel connector installed/enabled | **Kept** — legitimate committed deployment improvement (`erp/infrastructure/cloudflared/`); removing it would break the documented topology |

## Removed

Exactly the items marked **Removed** above: host `.venv`, `node_modules`,
`dist`, Docker build cache (cache only — no images/containers/volumes), and
all listed `/tmp` test scratch files. Nothing else.

## Restored

Nothing required restoration. No pre-existing host configuration was changed
in a way that needed reverting: all config changes this session are committed
repository/deployment improvements that constitute the deployed state.

## Preserved (intentionally untouched)

- The full ERP stack: postgres (named volume with all data), redis, backend,
  celery, frontend/nginx — all 5 containers still up.
- `erp/.env` secrets, application source, committed migrations.
- Pre-existing services: ssh, fail2ban, postfix, chrony, x-ui/xray, Docker
  engine, qemu-guest-agent, cloudflared (system).
- `agent/` harness (README, subagent.mjs, `.keys.example.json`, `.keys.json`).
- `.agent-work/` working notes + logs (evidence; notes are committed, logs are
  kept on disk).

## Unknown

- `/tmp/.5bf7fde*.so` (Freebuff runtime temp files), `/tmp/update-check`,
  `/tmp/systemd-private-*` — **not ours to attribute or remove**; left
  untouched intentionally.
- Nothing else was ambiguous: every removed item was matched to a session
  log/timestamp/artifact in `.agent-work/`.

## Final Health

```
CPU:        idle-ish (no runaway processes; only client + stack + pre-existing infra)
RAM:        934 MB free / 2.3 GB available (3.8 GiB total, no swap — pre-existing)
Disk:       80% used, 1.9 GB free (was 92% / 840 MB at session end — ~1.1 GB reclaimed)
Failed services: 0 (systemctl --failed: none)
Docker:     5/5 containers up — erp-backend (healthy), erp-postgres (healthy),
            erp-redis (healthy), erp-celery, erp-frontend
Application: /health/ → {"status":"ok"}; /ready/ → database ok, cache ok
Journal:    only pre-existing SSH brute-force attempts (fail2ban) and container
            startup veth messages — nothing caused by cleanup
```

## Repository

```
branch:     main
commit:     408f3687847a9ce77cf0c3addbecfeaa2be2a828 (baseline)
+ this pass: isort lint fix (apps/quality/tests/test_quality.py) and final
  documentation (docs/FINAL-TEST-VPS-AUDIT.md, docs/TEST-VPS-CLEANUP.md,
  .agent-work/FINAL-STATE.md, stage3/TASKS.md update, VPS-DEPLOYMENT-HANDOFF note)
remote:     origin (https://github.com/epicgamesfortnite1388-blip/SLZ.git)
push status: pushed to origin/main; remote HEAD verified by fetch
```

---

Cleanup result: **agent processes gone, agent-only software removed,
agent-only temp files removed, pre-existing services preserved, application
data preserved, system healthy.**