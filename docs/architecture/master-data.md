# Master Data (Task 004)

The master-data foundation supplies the shared reference entities every later
domain (sales, production, inventory, costing) will point at: organizations and
their production capabilities, business partners, the product taxonomy and a
thin product identity, materials, units of measure, and a minimal employee
record. This document describes what was built, how writes stay audited, and —
just as importantly — what was deliberately left out and why.

## Scope discipline

Task 004 implements *identity and classification* only. Entities carry enough to
be referenced and browsed; they do not yet carry the operational payload that
belongs to later milestones. The clearest example is `Product`, which is
intentionally **thin**: it holds a business code, bilingual names, its taxonomy
placement, a product group, and a base unit of measure — and nothing else. There
is no specification, BOM, routing, price, stock, or customer link on it yet.
Those belong to Task 005 and the production/inventory domains, and adding them
here would pre-empt decisions that are still open.

Explicitly deferred (see `docs/requirements/do-not-build-yet.md`): product
specifications and revisions, ink/color formulations, drawings and marking, the
SKU-derivation service, print mounting, tooling/clichés, BOM and routing,
warehouse store logic and kardex, CRM, and the full Finance/HR/Maintenance and
foreign-trade domains. Parametric business values that are still open (for
example a customer's delivery tolerance, DR-028) are modelled as nullable with
**no invented default** rather than guessed.

## Entities

`organization` gains `SiteCapability`: a declaration that a given site performs a
particular production capability (blown film, flexo printing, lamination,
slitting, and so on — grounded in the SLZ baseline, SR-15). It is unique per
`(site, capability)`.

`partners` is a new app. `Partner` is company-scoped (`company` + `code` unique
together) and must hold at least one role — enforced by a database
`CheckConstraint` (`is_customer OR is_supplier`) *and* a serializer check so the
API returns a clean `400` rather than a `500` from the integrity error. It also
carries a sanction flag (foreign-trade screening). `Customer` and `Supplier` are
optional one-to-one role extensions; `Contact` and `Address` hang off the
partner.

`catalog` is a new app holding `UnitOfMeasure` and `UomConversion` (a conversion
must be between two *different* units of the *same* dimension with a strictly
positive factor — validated in the serializer), the taxonomy chain
`ProductType → ProductClass → ProductFamily`, the cross-cutting `ProductGroup`
(used as the sales-line axis), the thin `Product`, and `Material`. `Material`
uses a `subtype` discriminator (resin/masterbatch, ink, solvent, consumable,
packaging, regrind, semi-finished, finished) so MRP can later treat the kinds
distinctly; its planning fields (reorder point, safety/min/max stock, lead time,
shelf life) are all optional.

`hr` is a new app with a minimal `Employee` (company-scoped, optional site /
department / login-user links). Full HR — decrees, payroll, attendance — is out
of scope.

## Writes are audited by construction

The platform's audit trail is driven by **domain events**, not ORM signals: an
`AuditLog` row appears only when an `EntityCreated/Updated/Deleted` event is
published (`apps/audit/subscribers.py`). The pre-existing `organization` CRUD
(Company/Site/Department) uses a bare `ModelViewSet` and is therefore *not*
audited.

Rather than copy that unaudited pattern, Task 004 routes every new write through
a small reusable service layer. `apps/core/service.py` exposes
`create_from_serializer` / `update_from_serializer` / `delete_instance`, each of
which runs inside `atomic_with_events()` and appends the matching domain event;
`apps/core/viewsets.py` provides `AuditedModelViewSet`, a `ModelViewSet` whose
`perform_create/update/destroy` call that service with the request user as actor.
Every Task 004 endpoint — and the new `SiteCapability` endpoint — extends
`AuditedModelViewSet`, so creates set `created_by` and emit an audit `CREATE`
row automatically, and soft deletes emit `DELETE`. The existing org CRUD was
left untouched for scope discipline; migrating it onto the audited base is noted
as a follow-up.

## Permissions

Access follows the platform's `module.resource.action` RBAC. Each viewset sets
`required_permission` for reads and a `permission_map` requiring the `.manage`
code for write verbs, enforced by `HasPermission` (superuser bypass applies). The
new codes — `organization.sitecapability.*`, `partners.partner/contact/address.*`,
`catalog.uom/productgroup/producttaxonomy/product/material.*`, and
`hr.employee.*` — are seeded by `apps/identity/management/commands/seed_rbac.py`
and attached to the platform admin role.

## API surface

All endpoints are namespaced under `/api/v1/`: `partners/partners`,
`partners/customers`, `partners/suppliers`, `partners/contacts`,
`partners/addresses`; `catalog/uoms`, `catalog/uom-conversions`,
`catalog/product-groups`, `catalog/product-types`, `catalog/product-classes`,
`catalog/product-families`, `catalog/products`, `catalog/materials`;
`hr/employees`; and `organization/site-capabilities`. They share the standard
paginated envelope (`count`, `total_pages`, `page`, `page_size`, `results`) and
support `search` / filter query params.

## Frontend

The React frontend adds a permission-aware **Master data** section. A hub page
lists only the sub-sections the user can view; browse screens for partners,
products, materials, units of measure, and employees each use a generic
`useCollection` hook (loading / error-with-retry / empty / data states, search,
pagination) and a shared `CollectionView` table. A representative **Partner
create** form exercises the full audited write path end to end; it surfaces the
backend's role-rule `400` rather than duplicating the rule client-side. All
labels are bilingual (fa/en) and the layout uses CSS logical properties so it
mirrors correctly under RTL and LTR. Sidebar entries and routes are gated by the
same view permissions the API enforces — the UI hides what the server would
refuse.

## Known risks / follow-ups

The repository commits **no migration files** for any app (only empty
`migrations/__init__.py` packages); the documented entrypoint is
`python manage.py makemigrations && migrate`. Under strict Django semantics an
app with an empty migrations package but no migration files will *not* get its
tables created by `migrate` alone, so `makemigrations` must be run first. This
convention was followed for the new apps and is flagged here rather than
papered over with hand-written, unverifiable migrations.

Runtime verification (migrations, the Django test suite, and the frontend
build/typecheck) could not be executed in the authoring sandbox because package
installation was unavailable; all Python was checked with `py_compile` and the
TypeScript reviewed by hand. These must be run in a normal dev environment.
