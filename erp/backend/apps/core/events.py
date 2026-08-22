"""In-process domain-event bus.

A deliberately small synchronous publish/subscribe mechanism so modules can
react to each other without importing one another directly (e.g. audit and
notifications subscribe to entity lifecycle events). This is NOT a distributed
message broker; durable/async fan-out is delegated to Celery tasks that a
subscriber may enqueue.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from datetime import timezone as _tz
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Type

logger = logging.getLogger("apps.core.events")


@dataclass
class DomainEvent:
    entity_type: str
    entity_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(_tz.utc))
    actor_id: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityCreated(DomainEvent):
    """A new entity was persisted. ``state`` carries a best-effort snapshot."""

    state: Optional[Dict[str, Any]] = None


@dataclass
class EntityUpdated(DomainEvent):
    changes: Dict[str, Any] = field(default_factory=dict)
    # Full-field snapshots around the write (None when unavailable). ``changes``
    # keeps the serializer's validated_data view; before/after give the diff.
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None


@dataclass
class EntityDeleted(DomainEvent):
    state: Optional[Dict[str, Any]] = None


@dataclass
class EntityApproved(DomainEvent):
    pass


@dataclass
class EntityRejected(DomainEvent):
    reason: Optional[str] = None


Handler = Callable[[DomainEvent], None]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: DefaultDict[Type[DomainEvent], List[Handler]] = defaultdict(list)

    def subscribe(self, event_type: Type[DomainEvent], handler: Handler) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        # Match handlers registered for the concrete type or any base type.
        for event_type, handlers in self._subscribers.items():
            if isinstance(event, event_type):
                for handler in handlers:
                    try:
                        handler(event)
                    except Exception:  # subscribers must never break the caller
                        logger.exception("event handler failed for %s", type(event).__name__)

    def clear(self) -> None:  # primarily for tests
        self._subscribers.clear()


bus = EventBus()
