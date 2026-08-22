# Database Conventions

## Primary keys: UUID

Every entity uses a **UUID version-4 primary key** (`UUIDModel` in
`apps/core/models.py`). UUIDs are:

- **Stable** — safe to reference across modules and to expose in URLs without
  leaking counts or ordering.
- **Non-guessable** — no sequential enumeration of records.
- **Merge-friendly** — generated client- or server-side without a central
  sequence.

Never expose or rely on an auto-increment integer as an identity.

## Business numbers ≠ primary keys

Human-facing identifiers (order numbers, product codes, document numbers, …)
are **separate fields** from the PK. This separation is a hard rule:

- The PK is an internal, immutable UUID.
- The business number is a domain concern: it may be formatted, sequenced,
  reset per year, or reissued, and it belongs to the module that owns the
  entity.
- The foundation ships **no** business-number generator — that is module
  policy. It only guarantees the PK/business-number split as a convention.

## Base model classes

Composable abstract bases (`apps/core/models.py`) — pick the minimum a model
needs; **do not** apply soft delete blindly:

| Base              | Adds                                                        |
|-------------------|------------------------------------------------------------|
| `UUIDModel`       | `id` UUID PK                                                |
| `TimeStampedModel`| `created_at`, `updated_at` (auto)                          |
| `AuthoredModel`   | `created_by`, `updated_by` (FK to user)                    |
| `BaseModel`       | UUID + timestamps + authored (the common default)          |
| `SoftDeleteModel` | `BaseModel` + `deleted_at`, soft-delete managers           |

See [data-lifecycle.md](data-lifecycle.md) for soft-delete semantics.

## Naming

- Tables: Django default (`<app>_<model>`); do not override without reason.
- Fields: `snake_case`; booleans read as predicates (`is_active`, `is_system`).
- Foreign keys: singular noun (`company`, `created_by`).
- Timestamps: `*_at`; dates: `*_date`; choices backed by `TextChoices`.

## Bilingual fields

Persian is the primary language, English secondary; the UI is RTL by default.
Where an entity carries human names/labels, store **both**:

```python
name_fa = models.CharField(max_length=255)
name_en = models.CharField(max_length=255, blank=True)
```

Store content, not presentation. Digit shaping (Persian/Latin), thousands
grouping, and currency formatting are done at the edge by the `localization`
app — never persisted pre-formatted.

## Datetimes

All datetimes are **timezone-aware and stored in UTC**. `USE_TZ=True`. Naive
datetimes are a bug. Jalali dates are a **presentation** transform over the same
UTC instant (see the `localization` app); they are not a separate stored value.

## Money & quantities

Store as exact numerics (`DecimalField` with explicit `max_digits`/
`decimal_places`), never floats, and never as pre-formatted strings. The
currency code lives beside the amount; default reporting currency is IRR.

## Uniqueness & integrity

- Use `unique` / `unique_together` (or `UniqueConstraint`) to enforce natural
  keys at the DB level; a violated constraint surfaces as `ConflictError` (409).
- Prefer `PROTECT` or `SET_NULL` over `CASCADE` for references to master data,
  so deleting a parent cannot silently erase history.

## Indexing

- Index every FK used in filters and every field used for lookups/sorting.
- Audit rows are indexed by `(entity_type, entity_id)` and `created_at`.
- Add composite indexes to match real query patterns as modules define them.

## Migrations

- Migrations are the source of truth for schema; they are additive and
  reviewed.
- The dev/compose entrypoint runs `makemigrations` + `migrate` + `seed_rbac`
  for convenience so a fresh checkout boots with the platform RBAC seeded. In a
  controlled environment, generate and commit migrations explicitly and run
  only `migrate`.
- `seed_rbac` seeds **platform** permissions and the `platform_admin` role
  only — no business data.
