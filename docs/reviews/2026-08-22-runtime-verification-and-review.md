# Runtime Verification & Parallel Review — 2026-08-22

**Author:** parallel development agent (secondary agent run).
**Scope:** independent verification + targeted fixes; no roadmap items touched.

This document records the **first actual runtime execution of the backend test
suite**, the defects it exposed, the fixes applied, and recommendations for
follow-up. It complements `docs/PROJECT-STATUS.md` (which the main agent owns).

---

## 1. Backend suite executed — RUNTIME VERIFIED

```
cd erp/backend
python manage.py test --settings=config.settings.test --noinput
Ran 198 tests in ~3.2s — OK (all pass)
python -m flake8 apps — clean under backend/.flake8 config
```

Environment: local Python 3.12 with Django 4.2.16 installed; SQLite via
`config.settings.test`. No Docker/Postgres involved; Postgres-specific behaviour
(e.g. real row locking) remains unverified.

## 2. Defects found and fixed

### D1 — Infinite on_commit drain loop in shared test client (critical)

`apps/core/tests/factories.py::OnCommitExecutingClient.generic` drained captured
`transaction.on_commit` callbacks with:

```python
del captured[batch_count:]   # removes everything AFTER the first batch
```

The first batch was never removed, so every audited write re-executed its
callback endlessly (each drained request hung the suite). Fixed to
`del captured[:batch_count]` — matching Django's own implementation, which uses
`pop(0)`. This single line is what made the whole suite runnable at all.

### D2 — Test asserted flat error payload instead of the standard envelope

`apps/engineering/tests/test_tooling.py::test_warehouse_must_be_cliche_store`
asserted `'warehouse' in response.data`, but DRF field errors are wrapped by
`standardized_exception_handler` as `data["error"]["details"]["warehouse"]`.
Fixed the assertion (code behaviour was correct).

### D3 — State-machine transition race + undeclared target status

`transition()` in `sales/procurement/production services.py` checked the source
status **outside** the transaction against a possibly stale instance, so two
concurrent transitions could both pass validation; an undeclared target status
string would also have been persisted if the source matched.

All three were hardened identically:
* target status validated against the model's declared `status` choices (409);
* source status re-checked on a `select_for_update()` row **inside**
  `atomic_with_events()` (first committer wins; loser gets 409);
* caller's instance kept consistent with the committed row.
No business rule changed — only mechanical guards tightened. Covered by new
`apps/procurement/tests/test_transition_safety.py` (3 tests, all passing).
Note: true concurrent-locking behaviour needs Postgres; SQLite ignores
`FOR UPDATE` (tests verify the stale-read guard logically).

### D4 — Notifications viewset relied on implicit default permissions

`NotificationViewSet` declared no `permission_classes` and leaned on the global
`DEFAULT_PERMISSION_CLASSES`. Now explicit: `permission_classes = [IsAuthenticated]`.

## 3. Tests added

| File | Tests |
|---|---|
| `apps/procurement/tests/test_transition_safety.py` | undeclared target rejected & nothing persisted; stale in-memory instance cannot drive a disallowed transition; valid transition persists, returns consistent instance, audits on commit |
| `apps/localization/tests/test_views.py` | `/api/v1/localization/info/`: anonymous access + payload contract; fa=rtl / en=ltr; dual-calendar server time keys |

All **executed and passing** as part of the full-suite run above.

## 4. Recommendations for the main agent

1. **`PermissionViewSet` has no explicit `permission_classes`** — any
   authenticated user can enumerate all platform permission codes (information
   disclosure; inconsistent with `RoleViewSet`). Suggest
   `require_permission("identity.role.view")` or similar. Not applied here
   because `identity/views.py` sits next to actively-developed files.
2. **Update `docs/PROJECT-STATUS.md`:** the "Runtime verification checklist"
   section can now record that the backend suite passes (SQLite). The global
   caveat should distinguish "backend tests RUNTIME VERIFIED (SQLite)" from
   "frontend build not yet verified" and "Postgres/Docker not yet exercised".
3. **Migrations exist but were never regenerated against a clean DB** — the
   suite applies committed migrations successfully, which is stronger than
   before, but `makemigrations --check` under Postgres should still be run once.
4. **Frontend runtime verification remains entirely unverified** (no
   `node_modules`; no npm available offline).
5. Consider extracting the now-identical `transition()` helpers into a shared
   core helper when sales/procurement/production next evolve (low priority;
   triplication is currently harmless and keeps domain modules decoupled).

## 5. Files changed

* `erp/backend/apps/core/tests/factories.py` — D1 fix (one line)
* `erp/backend/apps/sales/services.py`, `apps/procurement/services.py`,
  `apps/production/services.py` — D3 hardening (identical)
* `erp/backend/apps/notifications/views.py` — D4
* `erp/backend/apps/engineering/tests/test_tooling.py` — D2 fix (assertion)
* `erp/backend/apps/procurement/tests/test_transition_safety.py` — new
* `erp/backend/apps/localization/tests/test_views.py` — new

---

# Second parallel run — security & test-hygiene pass (2026-08-22, later)

## Work completed

### S1 — Permission catalogue endpoint gated (closes earlier recommendation #1)

`PermissionViewSet` had no explicit permissions: any authenticated user could
enumerate every platform permission code. Now:

* new seeded permission `identity.permission.view`
  (`apps/identity/management/commands/seed_rbac.py`);
* `permission_classes = [require_permission("identity.permission.view")]` on
  `apps/identity/views.py::PermissionViewSet`;
* superusers bypass as usual; no frontend consumer existed, so nothing breaks.

### S2 — Test uploads no longer pollute the repository

Document-upload tests wrote bytes into `erp/backend/media/` because
`config/settings/test.py` never isolated `MEDIA_ROOT`. Test settings now point
`MEDIA_ROOT` at a temp directory; the stray `backend/media/documents/` test
artifacts were deleted. (Dev/prod settings untouched.)

### S3 — New tests (all executed, passing)

| File | Coverage |
|---|---|
| `apps/identity/tests/test_permissions_api.py` | catalogue endpoint requires `identity.permission.view`; granted user lists + filters by module; superuser bypass; `seed_rbac` idempotency (no duplicate permissions/role/links) and creates no superuser without env |
| `apps/documents/tests/test_documents_policy.py` | oversize upload → `documents.file.too_large`; soft-deleted attachment hidden from list + download 404 while metadata retained; DELETE requires `documents.attachment.delete`; upload rejected without any documents permission |

Note: the shared `grant()` factory reuses one role across users, so grants leak
between users in the same test class; `test_documents_policy.py` includes an
isolated-role helper (`grant_isolated`) for per-user permission sets.

## Verification

```
python manage.py test --settings=config.settings.test --noinput
Ran 207 tests — OK
python -m flake8 apps config — clean
```

## Files changed (second run)

* `apps/identity/management/commands/seed_rbac.py` (+1 permission)
* `apps/identity/views.py` (gate PermissionViewSet)
* `config/settings/test.py` (MEDIA_ROOT isolation)
* `apps/identity/tests/test_permissions_api.py`, `apps/documents/tests/test_documents_policy.py` (new)
* deleted stray `backend/media/documents/` test artifacts

---

# Third parallel batch — pagination contract pinned (2026-08-22)

* **New:** `apps/core/tests/test_pagination.py` (3 tests) — pins the standard
  list-envelope contract (`count` / `total_pages` / `page` / `page_size` /
  next / previous / `results`), second-page navigation, and that an oversized
  `page_size` can never bypass `max_page_size`.
* Full suite after: **210 tests — OK**.

## Observation left to the primary agent

`apps/procurement/serializers.py` currently fails flake8 (W391 trailing blank
line). It was being edited concurrently during this run, so it was left alone
deliberately.
