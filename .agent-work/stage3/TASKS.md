# Stage 3 — Task Ledger (final pass 2026-09-03)

[x] Handoff: repo state captured
[x] Discovery: seed_demo_data exists; genealogy/ledger verified; dashboard KPIs live
[x] Scope decision: planning, recall, exposure, RBAC, tests, frontend, deploy
[x] Backend planning app (models/services/serializers/views/urls/migrations)
[x] Backend recall app (models/services/serializers/views/urls/migrations)
[x] Registration in settings/urls + RBAC codes in seed_rbac
[x] Backend tests (API/RBAC/isolation/engine/exposure) — 381 OK (4 PG-only skip)
[x] Migration drift clean; flake8/black/isort clean
[x] Frontend: api layers + planning pages + recall pages + routes/sidebar/i18n
[x] Frontend gates: typecheck, eslint, vitest 98 OK
[x] Docs: PROJECT-STATUS + roadmap-gap-matrix updated
[x] Deploy: rebuild images, migrate, restart prod, verify health — DONE (services healthy, planning.0001 + recall.0001 applied)
[x] Commit + push + verify remote — DONE (408f368, remote HEAD verified by fetch)
[x] Final handoff pass (2026-09-03): final gate re-run (381 backend / 98 frontend OK),
    docs/FINAL-TEST-VPS-AUDIT.md, .agent-work/FINAL-STATE.md, docs/TEST-VPS-CLEANUP.md,
    isort lint fix (apps/quality/tests/test_quality.py) committed + pushed

Deferred with justification: bin/location tracking (balance layer untouched),
email/SMS channels (DR-008 gated), BOM-exploded MRP demand (business-open
consumption basis).
