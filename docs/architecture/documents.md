# Documents & Attachments

The `documents` app is the platform's **generic file-attachment store** — a
foundation mechanism, not a business module. Any record anywhere in the system
can carry files by pinning an `Attachment` to a target through a
(`entity_type`, `entity_id`) pair. The store deliberately encodes **no** rule
about *what* may be attached to *what*, *how many*, or *by whom beyond RBAC* —
those policies belong to the owning module.

## Model

One entity (`apps/documents/models.py`):

- `Attachment` (a `SoftDeleteModel`) — the file's metadata and provenance:
  `entity_type` + `entity_id` (the target it is pinned to), `original_filename`,
  `content_type`, `size_bytes`, `checksum_sha256` (integrity), a unique
  `storage_key` (the opaque location in the storage backend — never exposed to
  clients), and a free-text `description`. The raw bytes live in the storage
  backend, not the database; the row is metadata plus a pointer.

Soft delete is deliberate: deleting an attachment retires the **metadata** row
while the bytes are retained, so a delete never destroys evidence and remains
recoverable/traceable.

## API surface

Under `/api/v1/documents/attachments/` (`AttachmentViewSet` — a
`GenericViewSet` composed of List / Retrieve / Destroy mixins plus two custom
actions):

- `GET attachments/` — list the register; filterable by `entity_type`,
  `entity_id`, `content_type`. Gated by `documents.attachment.view`.
- `GET attachments/{id}/` — retrieve one row's metadata. View-gated.
- `POST attachments/upload/` — multipart upload (`MultiPartParser`). Validates
  the upload, computes the SHA-256 checksum, writes the bytes under a derived
  `storage_key`, creates the row stamped with `created_by`, and writes a CREATE
  audit entry (`entity_type` `documents.Attachment`, metadata records the
  `linked_to` target). Returns the serialized attachment (201). Falls to the
  `required_permission` (`documents.attachment.view`), so any viewer may upload.
- `GET attachments/{id}/download/` — streams the bytes as an `attachment`
  disposition under the safe `original_filename` (the `storage_key` is never
  revealed). `get_object()` re-checks the view permission and queryset. Returns
  a `NotFoundError` if the stored file is missing.
- `DELETE attachments/{id}/` — soft-deletes the metadata and writes a DELETE
  audit entry. Gated by `documents.attachment.delete` (via `permission_map`).

RBAC `documents.attachment.view` / `.delete` were seeded with the foundation
(Task 003); this slice adds no new permission and no schema migration.

## Frontend

The React app adds a **Documents** screen (`/documents`, in the sidebar for
anyone with `documents.attachment.view`) backed by the register. It combines:

- an **upload card** capturing `entity_type`, `entity_id`, an optional
  `description` and the file itself, posting multipart form data and reloading
  the register on success; and
- a **register** listing each attachment's filename, its target
  (`entity_type #entity_id`) and human-readable size, with a **Download** action
  on every row and a **Delete** action gated by `documents.attachment.delete`.

Two client capabilities were added to support this without weakening the API
contract:

- `apiClient.postForm(path, formData)` sends multipart bodies. The client
  deliberately does **not** set `Content-Type` for form bodies so the browser
  supplies the multipart boundary itself.
- `apiClient.getBlob(path)` / `requestBlob` performs an **authenticated** binary
  fetch — the same Bearer token, correlation id and single 401→refresh→retry as
  `request`, but returning the raw `Blob` instead of JSON. This is required
  because a plain anchor `href` cannot carry the `Authorization` header; the
  frontend fetches the bytes with the token and hands the browser an object URL
  to save under the original filename.

No business rule is duplicated client-side; the server remains the authority and
surfaces its own validation/permission errors.

## Deliberately NOT built

- **Attachment policy** — required document types per entity, count/size quotas
  beyond the server's upload validation, retention schedules, or virus scanning.
- **In-context attachment panels** — embedding the upload/list widget inside each
  business record's detail screen. The generic register is the foundation; wiring
  a per-record panel is left to each owning module.
- **Versioned documents / e-signature / controlled-document workflows** — out of
  scope for the foundation.

## Verification status

IMPLEMENTED + STATICALLY CHECKED (backend `py_compile` clean and pre-existing;
frontend JSON i18n en/fa parity verified; no new migration, no new RBAC
permission). Tests are IMPLEMENTED, not EXECUTED (no Postgres/npm in the
authoring sandbox). Before relying on this slice run:
`python manage.py test apps.documents`, and the frontend `npm run build` /
`vitest` (which covers `src/api/__tests__/documents.test.ts`).
