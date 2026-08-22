# Notifications (in-app inbox)

The `notifications` app is a **foundation channel**, not a business module. It
delivers system-generated alerts to a specific user's in-app inbox. Producing a
notification is a side effect of other modules (the workflow engine notifies
approvers and requesters); this app owns only the storage, the per-user read
model and the read/clear API.

## Scope of the confirmed channel

Only the **in-app** channel is built. Email / SMS / push are deferred delivery
interfaces (DR-008, `do-not-build-yet.md` #30) and are intentionally absent from
the model, API and UI — the `NotificationType` taxonomy is delivery-agnostic, so
those channels can be layered on later without reshaping stored data.

## Model

`apps/notifications/models.py`:

- `NotificationType` — `APPROVAL_REQUIRED`, `APPROVAL_COMPLETED`,
  `TASK_ASSIGNED`, `STATUS_CHANGED`, `DEADLINE_APPROACHING`, `SYSTEM_ALERT`.
- `Notification` — `recipient` (CASCADE), `type`, `title`, `body`, an optional
  `entity_type` + `entity_id` pointer to the subject, `is_read` (indexed) and
  `read_at`.

## API surface

Registered at the API root `/api/v1/notifications/` (list + retrieve). Every
endpoint is **self-authorizing**: `get_queryset` filters to
`recipient=request.user`, so a user can only ever see or mutate their own
notifications and **no module permission is required** (authentication only).

- `GET notifications/` — the caller's inbox (paginated).
- `POST notifications/{id}/read/` — mark one read. Marking another user's
  notification is a 404 (it is not in the caller's queryset), not a 403 — the
  existence of others' notifications is never disclosed.
- `POST notifications/read-all/` — mark all of the caller's unread read; returns
  `{updated: <n>}`.
- `GET notifications/unread-count/` — returns `{unread: <n>}` for the header
  badge.

## Frontend

- **Inbox** (`/notifications`, in the sidebar for every authenticated user) —
  a `CollectionView` over `/notifications/` showing type, title (bold while
  unread), body and state, with a per-row **Mark read** action and a header
  **Mark all read** action. Both reload the collection on success.
- **Header bell** (`NotificationBell`) — fetches the unread count once on mount
  and renders a badge when `unread > 0`, linking to the inbox. It deliberately
  does **not** poll; the count refreshes on navigation / reload. A failed count
  fetch is swallowed so it can never break the header.

No icon library is available in the app (lucide-react is artifacts-only), so the
bell is a text label plus a numeric badge.

## Deliberately NOT built

- Email / SMS / push delivery (DR-008, #30) — deferred.
- Real-time push / websockets / polling — the count is fetch-on-mount only.
- Notification preferences / per-type mute — no confirmed business rule.

## Verification status

IMPLEMENTED + STATICALLY CHECKED (`py_compile` clean; i18n en/fa parity holds;
frontend api test authored). Tests are IMPLEMENTED, not EXECUTED (no
Postgres/npm in the authoring sandbox). No schema migration is fabricated and no
new RBAC permission is needed (the channel is self-authorizing). Before relying
on this slice run `python manage.py test apps.notifications` and the frontend
`vitest` / `npm run build`.
