# Verification Audit — Domain Modules (Tasks 004–011)

**Date:** 2026-08-21
**Author:** autonomous engineering run
**Scope:** static verification of the committed domain apps (`partners`, `catalog`,
`hr`, `engineering`, `manufacturing`, `inventory`, `quality`, `procurement`,
`sales`, `production`) against the SLZ source-of-truth, architecture conventions,
and the confirmed business rules.

> **Read this before trusting any "milestone complete" claim.** The domain code
> is coded to the platform conventions, but it has **not** been exercised by
> migrations or the test suite in this environment. This document records what
> was checked, what could not be, the issues found, and the fixes applied.

## 1. Environment blocker (why nothing is certified COMPLETE)

The authoring environment is a **network-restricted sandbox**. Package
installation fails not because of a bad pip config but because an **allowlist
egress proxy** refuses connections to non-approved hosts.

### Diagnosed root cause (2026-08-21)

- Python 3.10.12, pip 25.3. **No** `pip.conf` anywhere (`/etc/pip.conf`,
  `~/.pip/`, `~/.config/pip/`), and `pip config list` is empty — so pip uses the
  default index `https://pypi.org/simple`. The failure is **not** a custom index
  misconfiguration.
- All egress is forced through env-var proxies: `HTTP(S)_PROXY=http://localhost:3128`
  and `ALL_PROXY=socks5h://localhost:1080`.
- The proxy port `3128` is open, but tunnelling to external hosts fails:
  `curl https://pypi.org/simple/` → **HTTP 000**, `files.pythonhosted.org` →
  **000**, and `github.com` → **000**. pip surfaces this as
  `ProxyError('Cannot connect to proxy.', OSError('Tunnel connection failed:
  403 Forbidden'))`.
- Because a *general* host (github.com) is equally blocked, this is an
  **intentional allowlist proxy**, not a PyPI-specific outage or a fixable
  setting. → This is cause **(A/F): the proxy is a required security control and
  the environment cannot obtain dependencies from inside the repo.**
- **No offline fallback exists:** `pip cache list` is empty, there are no
  `*.whl`/sdists on disk except pip/setuptools' own bundled wheels, `apt-get`
  has no `python3-django` candidate, and none of the pinned project deps
  (`django`, `djangorestframework`, `celery`, `psycopg2-binary`, `jdatetime`,
  `whitenoise`, `django-cors-headers`, `django-filter`,
  `djangorestframework-simplejwt`, `redis`, `gunicorn`) are installed.

Per §1 of the directive, no VPN/bypass/TLS-disable was attempted; the proxy was
diagnosed, not circumvented. A single probe per host was used — the failing
`pip install` was **not** retried in a loop.

### What this prevents

- `python manage.py makemigrations` / `migrate`
- the Django test suite (`python manage.py test`)
- any API/runtime exercise or the frontend build

All Python in this run was validated with `python3 -m py_compile` **only**, which
proves syntax, **not** that Django loads, models are valid, migrations apply, or
tests pass. This is blocker type **(E) — environment/tooling prevents progress.**

### Required external environment change (to unblock)

One of the following must be provided by whoever controls the sandbox — it
**cannot** be fixed from inside the repository:

1. **Allowlist PyPI** on the egress proxy: `pypi.org` and `files.pythonhosted.org`
   (and `github.com` if any VCS deps are added later); **or**
2. **Provide an offline wheelhouse** (a directory of the pinned wheels) and
   install with `pip install --no-index --find-links <wheelhouse> -r
   requirements/dev.txt`; **or**
3. **Run the verification procedure below in a normal networked dev environment.**


### Deterministic verification procedure

Run top-to-bottom in a networked dev environment (or after an offline wheelhouse
is provided). Each step lists its pass condition. Do not skip step 4 —
`migrate` alone will **not** create tables (see §Migrations below).

```bash
# --- 1. Dependencies -------------------------------------------------------
cd erp/backend
python -m venv .venv && . .venv/bin/activate      # Python 3.11 recommended
pip install -r requirements/dev.txt               # networked
#   OFFLINE alt: pip install --no-index --find-links <wheelhouse> -r requirements/dev.txt
#   PASS: pip exits 0; `python -c "import django, rest_framework"` works.

# --- 2. Environment --------------------------------------------------------
cp .env.example .env 2>/dev/null || true          # set POSTGRES_*, DJANGO_SECRET_KEY, etc.
#   For the test suite no Postgres is needed (config/settings/test.py uses SQLite :memory:).
#   For a real run, a reachable PostgreSQL is required.

# --- 3. Django loads + system check ---------------------------------------
python manage.py check --settings=config.settings.test
#   PASS: "System check identified no issues".

# --- 4. Generate migrations (REQUIRED — none are committed) ----------------
python manage.py makemigrations --settings=config.settings.test
#   Inspect the generated files. PASS: migrations created for core, identity,
#   organization, audit, documents, localization, notifications, workflow,
#   partners, catalog, hr, engineering, manufacturing, inventory, quality,
#   procurement, sales, production — and NONE are unexpectedly destructive.

# --- 5. Apply migrations to a clean database -------------------------------
python manage.py migrate --settings=config.settings.test
#   PASS: all migrations apply with no error on a fresh DB.

# --- 6. RBAC seed ----------------------------------------------------------
python manage.py seed_rbac --settings=config.settings.test
#   PASS: permission codes + platform admin role seed idempotently.

# --- 7. Backend tests (focused + integration + regression) -----------------
python manage.py test --settings=config.settings.test
#   Some audit-trail assertions may need TransactionTestCase because events
#   publish on transaction.on_commit — if such tests error, that is a real
#   finding, not flakiness. PASS: full suite green.

# --- 8-9. Frontend build + typecheck --------------------------------------
cd ../frontend        # from erp/backend -> erp/frontend
npm ci
npm run typecheck     # tsc -b --noEmit
npm run build         # tsc -b && vite build
npm run test          # vitest run
npm run lint          # eslint, --max-warnings 0
#   PASS: typecheck, build, tests, and lint all exit 0.

# --- 10. Final regression --------------------------------------------------
#   Re-run step 7 after any fixes; confirm no regressions.
```

Per the completion gate (project directive §14), **no milestone may be marked
COMPLETE** until steps 4–7 (and 8–9 where frontend applies) pass.

## Migrations — status and reasoning

- **Status: NOT GENERATED, NOT COMMITTED.** Every app under `erp/backend/apps/`
  has a `migrations/` package containing only `__init__.py`.
- **Why they cannot be generated here:** `makemigrations` requires Django to be
  importable; it is not installable (see §1). Migrations were **not** fabricated
  or hand-guessed — autogenerated migrations must be produced by Django from the
  real model state and reviewed.
- **Important trap:** an app with an *empty* migrations package is treated by
  Django as "migrated with zero migrations", so `migrate` will **not** create its
  tables. `makemigrations` (step 4) MUST run first. This also means the Django
  test runner will fail to build the schema until initial migrations exist.
- **Apps requiring initial migrations:** `core`, `identity`, `organization`,
  `audit`, `documents`, `localization`, `notifications`, `workflow`, `partners`,
  `catalog`, `hr`, `engineering`, `manufacturing`, `inventory`, `quality`,
  `procurement`, `sales`, `production`.
- **Exact command once the environment is available:**
  `python manage.py makemigrations` then `python manage.py migrate`.


## 2. Overall assessment

The domain apps are **generally well-structured and architecture-compliant**:

- writes route through `AuditedModelViewSet` + `apps.core.service`, so creates
  set `created_by` and emit `EntityCreated/Updated/Deleted` → audit rows;
- RBAC uses `module.resource.action` with a `required_permission` (read) and a
  `permission_map` (write → `.manage`), enforced by `HasPermission`;
- the versioning apps (`engineering`, `manufacturing`, `quality`) correctly use
  the `VersionedRoot` / `Revision` pattern with a DRAFT→ACTIVE→SUPERSEDED
  lifecycle and delegate the lifecycle to a `services` module;
- the document apps (`procurement`, `sales`, `production`) correctly use a
  **status state machine** instead of the versioning pattern;
- OPEN/gated business rules (SKU derivation, roll-vs-lot genealogy, scrap/
  downtime tables, costing formulas, ATP/capacity) are **deliberately not
  implemented** — the code defers them rather than inventing SLZ rules. This
  matches the do-not-build-yet gates.

The issues below are the exceptions, ranked by severity. **MAJOR** = correctness/
integrity risk; **MINOR** = quality/robustness.

## 3. Systemic issues (project-wide)

1. **No migration files committed (project-wide).** Every app has an empty
   `migrations/` package. Tables are generated at deploy via `makemigrations`.
   This is a deliberate convention here, but it means the schema is unverified
   and `migrate`-alone will not build tables. *Action: generate & commit
   migrations, then run the suite.*

2. **Multi-tenant (company/site) consistency is enforced inconsistently.** Most
   references are not checked for company agreement at the API boundary, and
   there are **no server-side company-scoped querysets** (list endpoints return
   all companies' rows; filtering is client-supplied only). A user with a global
   `.view` permission can read another company's data. *This is a confirmed
   multi-company system (DR-040), so cross-company leakage is a real concern.*
   Severity ranges MINOR→MAJOR by app; `sales` (customer_product↔customer) and
   `production` (spec/BOM/routing↔product↔company) are the sharpest.

3. **Audit subscriber dropped `actor_id` (MINOR) — FIXED this run.** Previously
   `apps/audit/subscribers.py` forwarded `metadata` + `correlation_id` to
   `record_audit` but not the event's `actor_id`, so audit rows from the event
   path recorded the action but not who did it. Fixed by adding an `actor_id`
   parameter to `record_audit` that resolves the `User` by id (best-effort;
   an unknown/malformed id degrades to an anonymous row rather than failing the
   write) and passing `event.actor_id` from all three subscribers. Tests added
   (`test_event_actor_id_is_resolved_onto_audit_row`,
   `test_unknown_actor_id_degrades_to_anonymous_row`).

## 4. Per-app findings

### engineering (Task 005) — FIXED this run
- **MAJOR (fixed):** child rows (`SpecLayer`/`SpecColor`/`SpecParameter`) could
  be **soft-deleted while their revision was ACTIVE/SUPERSEDED**, bypassing the
  immutability invariant. Serializers guarded create/update but DELETE skips
  serializer validation. Fixed by overriding `perform_destroy` on the child
  viewsets to call `services.assert_revision_editable(instance.revision)`. Tests
  added (`test_can_delete_layer_of_draft_revision`,
  `test_cannot_delete_layer_of_active_revision`).
- Note: audit tests that assert an `AuditLog` row exists may need
  `TransactionTestCase` (events publish on `transaction.on_commit`).

### manufacturing (Task 006) — FIXED this run
- **MAJOR (fixed):** same child-row DELETE immutability bypass on `BomLine` and
  `RoutingOperation`. Fixed identically; tests added
  (`test_delete_bom_line_only_while_draft`,
  `test_delete_operation_only_while_draft`).
- **MINOR:** `WorkCenter` / `Machine` are hard-deletable master data that later
  production references will point at — consider soft-delete / PROTECT once
  referenced.

### production (Task 011) — FIXED this run
- **MAJOR (fixed):** the production order pinned a `spec_revision`,
  `bom_revision`, and `routing_revision` with **no consistency validation** —
  a WO for product X could pin a spec revision belonging to product Y, a BOM/
  routing built for a different spec, or references from another company.
  FR-038 requires the order to be a coherent frozen snapshot of the definition.
  Added referential-integrity validation in `ProductionOrderSerializer.validate`:
  `spec_revision.root == customer_product`, `customer_product.company == company`,
  `site.company == company`, and (when pinned) `bom_revision`/`routing_revision`
  `.root.spec_revision == spec_revision`. Tests added
  (`test_spec_revision_must_belong_to_customer_product`,
  `test_customer_product_must_belong_to_order_company`).
  **Not** enforced (would invent an OPEN rule): requiring BOM/routing at release,
  or requiring the pinned revisions to be ACTIVE (Q-026 keeps BOM level OPEN;
  the model deliberately leaves these optional).

### sales (Task 010) — FIXED this run
- **MAJOR (fixed):** a sales-order line's `customer_product` was not checked
  against the order's `customer` or `company`, so customer A's product could be
  ordered on customer B's order, or another company's product could leak onto
  the order (DR-040). Added `SalesOrderLineSerializer.validate` referential
  integrity: `customer_product.company == order.company` and
  `customer_product.customer == order.customer.partner`. Tests added
  (`test_line_customer_product_must_belong_to_order_customer`,
  `test_line_customer_product_must_belong_to_order_company`,
  `test_line_matching_customer_and_company_is_accepted`). Mirrors the production
  guard; invents no OPEN rule (pricing/ATP/allocation remain gated).

### procurement (Task 009) — FIXED this run
- **MINOR→MAJOR (fixed):** requisition/order lines did not check that the
  `material` belongs to the header's company, and a PO line's provenance
  `requisition_line` was not checked for company agreement (DR-040). Added a
  `_validate_references` hook on the shared `_LineOfDocumentSerializer` base and
  implemented it for both line types (`material.company == header.company`; PO
  line `requisition_line.requisition.company == order.company`). Tests added
  (`test_line_material_must_belong_to_requisition_company`,
  `test_order_line_material_must_belong_to_order_company`).

### quality (Task 008) — FIXED this run
- **MINOR→MAJOR (fixed):** a `QualityPlanItem` could reference a
  `characteristic` or `work_center` from a different company than the product
  the plan is written for. Added `QualityPlanItemSerializer._validate_references`
  deriving the plan company through `revision.root.spec_revision.root.company`
  and requiring `characteristic.company` and `work_center.company` to match.
  Tests added (`test_plan_item_characteristic_must_match_plan_company`,
  `test_plan_item_work_center_must_match_plan_company`). The free-text
  measurement `unit` remains as-is (acceptable for a definition layer; still
  flagged for a future `UnitOfMeasure` FK).

### inventory (Task 007)
- **MINOR:** warehouse master data is company/site-scoped; there are no child
  cross-references to guard at this layer yet. Per-user warehouse access (SR-10)
  is part of the systemic read-isolation decision (§8), not a local fix.

## 5. Fixes applied this run

| App | Change | File | Tests |
|---|---|---|---|
| engineering | child-row DELETE immutability guard | `apps/engineering/views.py` | `tests/test_engineering.py` |
| manufacturing | child-row DELETE immutability guard | `apps/manufacturing/views.py` | `tests/test_manufacturing.py` |
| production | snapshot referential-integrity validation | `apps/production/serializers.py` | `tests/test_production.py` |
| sales | order-line customer_product↔customer/company guard | `apps/sales/serializers.py` | `tests/test_sales.py` |
| procurement | line material↔company + PO-line provenance guard | `apps/procurement/serializers.py` | `tests/test_procurement.py` |
| quality | plan-item characteristic/work_center↔company guard | `apps/quality/serializers.py` | `tests/test_quality.py` |
| audit | event-path `actor_id` resolution onto audit rows | `apps/audit/services.py`, `apps/audit/subscribers.py` | `tests/test_audit.py` |

All changes are **additive, low-regression-risk**, and mirror existing patterns.
Existing green tests use consistent data, so the new guards do not reject any
previously-passing case. All files pass `py_compile`. **The new tests have not
been executed** (environment blocker) and must be run to confirm behavior.

## 6. Deferred (needs a working test environment or a business decision)

- **Server-side company-scoped querysets** (multi-tenant *read* isolation) —
  systemic; blocked on the user↔company binding decision (see §8). This is a
  business/architecture decision, **not** a safe local fix.
- **`WorkCenter`/`Machine` deletion policy** (soft-delete vs `PROTECT`). Both
  extend `BaseModel` (hard-deletable). The audit recommends soft-delete/PROTECT
  "once referenced", but (a) it is a model+migration change that cannot be
  verified here, and (b) the deletion policy for master data is not a confirmed
  SLZ rule. Deferred deliberately.
- **Generating and committing migrations** for all apps — blocked on the
  environment (Django not installable here; see §1). Must be produced by
  `makemigrations` in a networked env and reviewed.

All company/site *referential-integrity* consistency guards that were previously
deferred (sales, procurement, quality) were **implemented this run** as pure
data-integrity invariants (§4, §5). They do **not** pre-empt the systemic
read-isolation decision in §8.

These remaining items were **not** attempted blind: each is either an OPEN
business/architecture decision or needs the test suite to prove no regression,
and the directive forbids sacrificing correctness for speed.

## 6a. Roadmap status — why no *new* feature milestone was built this run

After the integrity-hardening pass, the next candidate feature areas were
assessed against `docs/requirements/do-not-build-yet.md` and the reconciliation
domain model. **Every forward-flow feature is gated on an OPEN SLZ business
decision**, so building any of them would violate the "never invent an SLZ
decision" rule:

- Stock movements / rial+qty **Kardex** / on-hand, **lots/rolls/genealogy**,
  two-stage **goods receipt**, **QC execution** (results/NCR/COA/auto-stop),
  **production execution** (confirmations/scrap/downtime), and **MRP** are all
  blocked primarily by **Q-046 / DR-020** (roll-serialization vs lot+count) —
  `do-not-build-yet.md` #18, the highest-priority gate; constraint **C-003**
  forbids migrating the traceability schema until it is decided.
- **Sales pricing / quotation / proforma** — pricing policy undefined
  (#26, R-14). **ATP / promised date** — SR-12 + capacity modeling tied to the
  OPEN DR-041. **Delivery / shipment / marking** — needs the stock layer (#18)
  + marking model NQ-008 (#25). **SKU-derivation** — coding scheme Q-019/NQ-005
  (#14). **Costing** — #1–6. **Approval-hierarchy content** — thresholds/roles
  Q-053/054/056 (#7/#8). **Finance/CRM/Maintenance** — deferred phases.
- The apparent "next" un-gated entity, a standalone **Artwork/prepress** model,
  is **not** separately specified in `slz-domain-model.md`: artwork/"design &
  cliché profile"/ink formulation is modelled as *part of the versioned product
  specification*, and cliché is "revised with artwork". Building a standalone
  artwork entity would require inventing its structure (fields, mounting-calc,
  approval) — several parts of which are explicitly OPEN. **Deliberately not
  built.**

**Conclusion:** offline feature work is exhausted without SLZ input. The highest
-leverage unblockers are human decisions — resolve **Q-046/DR-020** first (it
alone unblocks stock, traceability, GRN, execution, QC results, and delivery),
then the pricing/costing decisions. Until then, the safe offline work remaining
is limited to test-coverage backfill and the runtime verification below.

## 6b. Consolidated runtime-verification handoff (run on the real local machine)

Runtime verification is a **separate external stage** (the sandbox cannot install
Django — §1). Run this **once** on the networked local machine to verify
everything implemented so far *including this run's guards* in one pass, so the
environment need not be spun up per change:

```bash
# 1. exact directory
cd erp/backend

# 2. exact setup commands (networked; Python 3.11 recommended)
python -m venv .venv && . .venv/bin/activate
pip install -r requirements/dev.txt
python -c "import django, rest_framework; print(django.get_version())"   # sanity

# 3. exact migration commands (NONE are committed — makemigrations MUST run first)
python manage.py check --settings=config.settings.test
python manage.py makemigrations --settings=config.settings.test
python manage.py migrate       --settings=config.settings.test
python manage.py seed_rbac     --settings=config.settings.test

# 4. exact test commands (full suite; then the guards added/changed this run)
python manage.py test --settings=config.settings.test
python manage.py test apps.audit apps.sales apps.procurement apps.quality \
                      apps.production apps.engineering apps.manufacturing \
                      --settings=config.settings.test

# 5. exact frontend verification commands
cd ../frontend
npm ci
npm run typecheck && npm run build && npm run test && npm run lint
```

**6. Expected success conditions**
- `check` → "System check identified no issues".
- `makemigrations` → initial migrations created for every app (core, identity,
  organization, audit, documents, localization, notifications, workflow,
  partners, catalog, hr, engineering, manufacturing, inventory, quality,
  procurement, sales, production) and none unexpectedly destructive.
- `migrate` / `seed_rbac` → apply/seed cleanly on a fresh DB, idempotent.
- `manage.py test` → full suite green, including this run's new tests:
  audit actor_id (2), sales RI (3), procurement RI (2), quality RI (2),
  production RI (2), engineering/manufacturing child-DELETE (4).
- Frontend: typecheck, build, test, lint all exit 0.

**7. Known issues to watch for**
- Audit-trail assertions that check an `AuditLog` row exists after an API write
  may need `TransactionTestCase` because domain events publish on
  `transaction.on_commit`. If such a test errors (not fails-on-logic), that is
  the on_commit timing, not a guard bug — the direct-`bus.publish` audit tests
  are unaffected. Convert to `TransactionTestCase` if needed.
- The new referential-integrity guards return **HTTP 400** (validation);
  editability violations still return **409**. A test expecting the wrong code
  indicates a real behavior mismatch to investigate, not flakiness.
- If `makemigrations` reports model changes on a second run, a model/migration
  is out of sync — inspect before committing.

Report results back and any red test will be fixed before further development.

## 7. Open business questions (unchanged — require human input)

None newly raised. The pre-existing OPEN items (Q-026 BOM level, Q-046 roll-vs-
lot genealogy, SKU-derivation NQ-005, NQ-002 full company/site list, DR-043
outsourcing locus) remain gated in `docs/requirements/do-not-build-yet.md` and
are correctly deferred by the code.

## 8. Multi-tenancy — architectural decision required (do not patch piecemeal)

The audit's most consequential systemic finding is **read isolation**. Confirmed
facts: SLZ is multi-company (DR-040: phase-1 = SLZ Tehran + Helena Saveh), and
every domain model is company-scoped via a `company` FK. **However**, the API
layer has **no server-side company scoping**: list endpoints return every
company's rows, and a caller with a global `.view` permission can read another
company's data (client-supplied `?company=` filtering is not a security
boundary).

This is **systemic**, not a per-endpoint bug, so it must be resolved by an
architectural decision — **not** by adding ad-hoc filters to individual
viewsets. The source of truth does **not** yet specify the user↔company binding,
so the following is genuinely OPEN and should be decided by the team before
implementation:

- **Is a user bound to one company or many?** (e.g. a `User.company` FK, or a
  many-to-many company membership.)
- **Are RBAC permissions global or company-scoped?** Today `HasPermission`
  checks `module.resource.action` with a superuser bypass and no company
  dimension.
- **Enforcement mechanism:** the clean, consistent fix is a shared mixin that
  filters every domain queryset to the request user's company/companies (with an
  explicit cross-company role for holding-level users), applied once at the
  `AuditedModelViewSet` layer — rather than N inconsistent local patches.

**Recommendation:** decide the user↔company model, then implement a single
queryset-scoping mixin at the base viewset. The per-document *referential*
integrity guard added to `production` this run is compatible with any of these
choices (it validates that references are mutually consistent, which is correct
regardless of the isolation model) and does **not** pre-empt this decision.

Until this is decided and implemented, treat the API as **not tenant-isolated
for reads** — acceptable only for a trusted single-tenant dev/test setup.


