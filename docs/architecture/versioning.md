# Versioning

Manufacturing master data is **revisable**: a product spec, a bill of materials,
a routing, or a price list changes over time, and older transactions must keep
pointing at the revision that was in force when they were created. The
foundation ships a **reusable pattern** for this — not any concrete versioned
business entity.

> The versioning primitives live in `apps/core/versioning.py`. No business model
> uses them yet; that is the job of future modules (starting with Master Data).

## The pattern: Root + Revision

Two abstract models:

```
VersionedRoot        # the stable identity of the thing being versioned
   └── Revision      # an immutable-ish snapshot of its content at a point in time
         revision_number   (1, 2, 3, …)
         status            (DRAFT → ACTIVE → SUPERSEDED / ARCHIVED)
         effective_from    (when this revision takes effect)
         effective_to      (when it stops; null = open-ended)
         change_reason     (why this revision exists)
```

- The **root** is what everything else references (a product, a BOM header).
  Its UUID never changes across revisions.
- A **revision** carries the actual content and a monotonically increasing
  `revision_number` within its root.
- Exactly one revision is normally **active** for a given effective window.

## Statuses

`RevisionStatus`:

| Status       | Meaning                                                     |
|--------------|-------------------------------------------------------------|
| `DRAFT`      | Being prepared; editable; not yet in force                  |
| `ACTIVE`     | In force for its effective window                           |
| `SUPERSEDED` | Replaced by a newer revision                                |
| `ARCHIVED`   | Retired, retained for history                               |

Helper properties on `Revision`:

- `is_active` — status is `ACTIVE` and "now" is within `[effective_from,
  effective_to)`.
- `is_editable` — only `DRAFT` revisions may be edited; `ACTIVE`/`SUPERSEDED`
  content is frozen so historical references remain trustworthy.

## Rules for modules adopting the pattern

1. **Never mutate an active revision.** To change content, create a new
   `DRAFT` revision, then activate it (which supersedes the previous active one
   and sets its `effective_to`).
2. **Transactions bind to a revision, not a root.** When a sales order or work
   order captures a BOM/spec, it stores the specific revision id so later edits
   don't rewrite history.
3. **Approval before activation.** Activating a revision is a natural fit for
   the [workflow](../architecture/system-architecture.md) engine; wire it
   through an approval where the business requires sign-off.
4. **Effectivity is explicit.** Use `effective_from`/`effective_to` for
   time-based selection; do not infer effectivity from `created_at`.
5. **Audit comes for free** if activation/supersession publish standard events.

## What the foundation does *not* decide

- Numbering scheme of the root's business number.
- Whether revisions require approval (module policy).
- Concrete fields of any revision (BOM lines, routing steps, prices) — those
  belong to the owning module.

This keeps the mechanism reusable while leaving domain policy to Master Data and
the modules that follow it.
