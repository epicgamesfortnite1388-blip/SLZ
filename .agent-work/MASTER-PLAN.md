# SLZ ERP — Master Plan (takeover session 2026-09-14)

Legend: [ ] pending · [~] active · [x] completed + verified · [!] blocked

## P0 — Security / data integrity
[~] P0-audit: independent re-verification of tenancy + auth enforcement on this
    baseline (AuditedModelViewSet scoping, serializer write guards, attachment
    resolver). No changes expected unless a real defect surfaces.
    Status: core/viewsets.py re-read this session — fail-closed scoping + write
    guards + superuser bypass confirmed in source; full suite green. No defect found.

## P1 — Core ERP correctness / roadmap item #1
[x] Task 014b — replicate the master-data EDIT flow (frontend; backend already
    accepts PATCH with manage-permission mapping):
    - [x] update API fns: updateProduct, updateMaterial, updateCompany,
          updateSite, updateDepartment, updateWarehouse, updateEmployee,
          updateWorkCenter, updateMachine
    - [x] edit pages (PartnerEditPage pattern; identity fields read-only):
          ProductEdit, MaterialEdit, CompanyEdit, SiteEdit, DepartmentEdit,
          WarehouseEdit, EmployeeEdit, WorkCenterEdit, MachineEdit
    - [x] "Edit" links on detail pages (product, material, employee, warehouse,
          work-center, machine) + list-row Edit links for company/site/department
          (no detail pages exist for those)
    - [x] routes + ProtectedRoute manage permissions in App.tsx
    - [x] i18n fa/en keys (parity guard — verified equal key sets)
    - [x] PATCH contract tests in src/api/__tests__/ (+10 tests)
    - [x] full gates: typecheck ✓ · eslint 0 warnings ✓ · vitest 28 files /
          108 tests OK ✓ · vite build ✓ · backend suite re-run 381 OK ✓
    - [ ] commit to origin/main (awaiting user-visible session commit)

## P2 — Operational
[x] Deployment verification on THIS VPS (2026-09-14): prod stack
    (`docker-compose.prod.yml`, secrets via scripts/gen-env.sh) — postgres/redis/
    backend(healthy)/celery/frontend all up; ZERO public ports (nginx on
    127.0.0.1:80 only); /ready/ through nginx = database ok + cache ok; JWT login
    OK; audited company CREATE + PATCH edit flow exercised live (before/after
    diff present in /audit/logs/). Superuser admin@slz.local created on the fresh
    DB; test company TAKEOVER left as evidence. NO DNS/tunnel work (not this VPS).
[ ] Code-splitting for the >500 kB vendor chunk (P4, deferred — cosmetic).

## Second audit (adversarial pass, 2026-09-14)
[x] Self-parent / cross-site / cycle paths in the department edit flow traced:
    found Department.parent had NO same-site or cycle validation server-side
    (user-reachable once reparenting UI exists — would corrupt org hierarchy).
    FIXED in DepartmentSerializer.validate (create + update; explicit-null clear
    still allowed); 4 regression tests added (same-site, self-parent, two-level
    cycle, deep chain + legal clears). Backend 385 tests OK; prod stack rebuilt
    and /ready/ green after the fix.
[x] LIVE adversarial re-test on the running prod stack (2026-09-14, commit
    dec40b1): two companies + two scoped users (alice→A, bob→B) provisioned via
    API/ORM; 15 HTTP-level checks executed.
    IDOR: all cross-company attachment paths REJECTED (list invisible, get/
    download/delete → 404, foreign-entity upload → 403, unsupported entity
    type → 400 fail-closed). Own-company upload/download → 201/200.
    Nonce/duplicate: same-nonce replay → 409 duplicate_request; cross-company
    nonce replay → 409; over-receipt → 422 grn.over_receipt; GRN lists
    company-scoped (bob sees 0 of alice's 2).
    TWO REAL DEFECTS FOUND & FIXED (commit dec40b1):
    (1) attachment upload 500ed in prod — media volume root-owned over
    /app/media, appuser could not write. Fixed: mkdir+chown in image, one-shot
    media-init compose service, entrypoint chown when root. Verified: upload
    201 + download 200 on the rebuilt stack.
    (2) duplicate document-number retry tripped uq_grn/shipment_company_number
    (no "nonce" in name) → 500 instead of 409. Fixed: backend-agnostic
    duplicate-key mapping in both views; +2 regression tests (backend 387).
    Ledger verified exact: on_hand 10 = two legitimate 5-unit receipts; no
    duplicate rows ever persisted.
[~] Remaining audit ideas: i18n visual RTL pass (needs a browser on host).
- No destructive git operations; no history rewrite; no force push.
- Business-blocked scope stays blocked (do-not-build-yet lists).
- Every completed task needs verification evidence before [x].


## Session addendum 2026-09-14 (public exposure + browser E2E)
[x] Superuser `abystral` created (email-keyed login: abystral@slz.local) — verified live
[x] Browser E2E via headless Chromium: 18/18 PASS (login, RTL/fa, sidebar, edit flow, mobile drawer) — no page errors
[x] P0 fix committed d310a41: SPA now calls same-origin /api/v1 (was baked-in localhost:8000 → CSP-blocked in prod)
[x] VPS NAT discovery: all inbound ports provider-filtered → Cloudflare Tunnel selected (matches repo's documented architecture)
[!] Public URL erp.slz.dpdns.org — BLOCKED on one Cloudflare credential:
    - Option 1 (preferred): user pastes a CF API token (Zone:DNS Edit + Account:Cloudflare Tunnel Edit) → agent creates tunnel + CNAME via API
    - Option 2: user creates tunnel in Zero Trust dashboard, pastes the tunnel token → agent runs connector + adds public hostname
    - Option 3: user uploads the cert.pem their browser downloaded during tunnel login
    Staged and ready: /etc/cloudflared/config.yml (ingress erp.slz.dpdns.org → http://127.0.0.1:8080), systemd unit, DJANGO_ALLOWED_HOSTS/CORS include the domain, app healthy on 127.0.0.1:8080
