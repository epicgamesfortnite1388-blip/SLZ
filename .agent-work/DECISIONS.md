# SLZ ERP — Decisions & Root Causes

## F1 — P0 concurrency: negative stock via OUT race
- **Root cause**: `post_movement` checked derived on-hand then inserted — no lock between read and write; two parallel OUTs on the same (company, warehouse, material|unit) could both pass → negative stock. No row exists to `select_for_update` (balances are derived).
- **Fix**: `apps/core/transactions.postgres_advisory_xact_lock(*parts)` — `pg_advisory_xact_lock` on a sha256 key inside the atomic block, only on the PostgreSQL backend (SQLite no-op). Taken in `post_movement` for OUT before the guard.
- **Regression**: `test_ledger.TransferTests` etc.; races themselves are exercised by the Postgres smoke (SQLite serializes writes).

## F2 — P0 concurrency: double-shipment
- **Root cause**: `create_shipment` read a RESERVED allocation, checked status, later set SHIPPED — two concurrent shipments of the same allocation both passed.
- **Fix**: `Allocation.objects.select_for_update().get(...)` before the status check (allocation row is the natural serialization point).
- **Regression**: `DeliveryTests.test_shipped_allocation_cannot_be_reused` (+ OUT movement count assert).

## F3 — P2 ledger inconsistency: TRANSFER rows
- **Root cause**: API/`post_movement` accepted direction=TRANSFER but no real transfer flow existed; derived balances ignored TRANSFER while kardex counted it negative → derived views disagreed.
- **Fix**: reject TRANSFER in `post_movement`; add `transfer_stock()` (atomic OUT@source + IN@dest with guards) + `POST /inventory/movements/transfer/` + `TransferMovementSerializer`.
- **Regression**: 4 service tests + 3 API tests (incl. cross-company + raw-TRANSFER rejection).

## F4 — P1 idempotency: duplicate GRN / delivery submissions
- **Root cause**: nonce protection existed only on production postings; GRN + Shipment POST could be retried (network/timeout) and double-post.
- **Fix**: mirror the MaterialIssue pattern — `nonce` UUID + partial unique constraint on GoodsReceipt & Shipment; field on create serializers; IntegrityError→409 `duplicate_request` in views; new migrations 0003 in procurement & shipment.
- **Regression**: GRN + delivery duplicate-nonce 409 tests.

## F5 — P2 business rule: execution on non-RELEASED orders
- **Root cause**: `create_material_issue`/`create_production_output` didn't verify order status at service level (serializers partially did).
- **Fix**: `_assert_order_released` in both services (defense-in-depth under serializer checks).
- **Regression**: draft-order issue/output rejection tests (API 400 + service ConflictError).

## F6 — frontend: sidebar collapse did not expand content; mobile drawer dead
- **Root cause**: collapsed width was hard-coded (`.sidebar--collapsed{width:56px}`) while the main-content offset (`.app-shell__main` margin and shell `--sidebar-width`) stayed 248px; sibling selector `.sidebar--collapsed ~ .app-shell__main` never matched (nav nested in `.app-shell__sidebar`). Mobile: `global.css` hid `.app-shell__sidebar` (display:none) — the fixed drawer toggle/nav/overlay lived inside it, so the drawer was unreachable.
- **Fix**: scope `--sidebar-width` to `.app-shell` + `:has(.sidebar--collapsed)` override (single source of truth, content expands); stop hiding the sidebar wrapper on mobile (it becomes the fixed drawer host); mobile toggle repositioned below the header; added drawer close button, Escape-to-close, `aria-expanded`/`aria-controls`, body scroll lock, focus management, focus-visible styles; nav landmark label + `nav.ariaLabel`/`nav.close` i18n keys (en/fa).
- Sidebar state persisted in localStorage (pre-existing, kept). 90/90 FE tests, tsc, eslint pass.

## External blockers
- Subagent gateway out of credits (403) / model 503 — deeper multi-model audits not possible; mitigated with lead-agent audits + one successful business-logic subagent report (in .agent-work/reports/audit-business.md).
- No browser (Playwright/Chrome not installed) for real viewport/E2E checks; static + API-level verification done instead.