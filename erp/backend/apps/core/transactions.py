"""Transaction helpers.

Standard mutation order (see docs/architecture/transactions.md):
    validate  ->  begin  ->  apply changes  ->  write audit  ->  commit
The ``atomic_with_audit`` context manager wraps this so all-or-nothing
semantics hold: if audit writing or any step fails, the whole unit rolls back.
Domain events are collected during the transaction and only published on
successful commit, so subscribers never react to rolled-back state.
"""

from __future__ import annotations

import hashlib
from contextlib import contextmanager
from typing import Iterator, List

from django.db import connection, transaction

from apps.core.events import DomainEvent, bus


def postgres_advisory_xact_lock(*key_parts: object) -> None:
    """Serialise callers on a named key using a PostgreSQL advisory xact lock.

    Used where the natural row to lock does not exist (e.g. an OUT stock
    movement against a *derived* balance), so two concurrent transactions can
    both pass a read-then-write guard. The lock is scoped to the current
    transaction and released automatically on commit/rollback.

    Non-PostgreSQL backends (SQLite test runs) execute no-op: SQLite serialises
    writes at the database level and tests run single-process.
    """
    if connection.vendor != "postgresql":
        return
    raw = "\x00".join(str(part) for part in key_parts)
    digest = hashlib.sha256(raw.encode("utf-8")).digest()[:8]
    key = int.from_bytes(digest, "big", signed=True)
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [key])


@contextmanager
def atomic_with_events() -> Iterator[List[DomainEvent]]:
    """Run a block atomically; publish collected events only after commit.

    Usage::

        with atomic_with_events() as events:
            obj = Model.objects.create(...)
            events.append(EntityCreated(entity_type="Model", entity_id=str(obj.pk)))
    """
    pending: List[DomainEvent] = []
    with transaction.atomic():
        yield pending
        # Defer publishing until the outermost transaction actually commits.
        for event in pending:
            transaction.on_commit(lambda ev=event: bus.publish(ev))
