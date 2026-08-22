"""Transaction helpers.

Standard mutation order (see docs/architecture/transactions.md):
    validate  ->  begin  ->  apply changes  ->  write audit  ->  commit
The ``atomic_with_audit`` context manager wraps this so all-or-nothing
semantics hold: if audit writing or any step fails, the whole unit rolls back.
Domain events are collected during the transaction and only published on
successful commit, so subscribers never react to rolled-back state.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, List

from django.db import transaction

from apps.core.events import DomainEvent, bus


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
