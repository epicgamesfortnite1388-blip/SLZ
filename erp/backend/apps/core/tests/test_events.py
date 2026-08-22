"""Domain-event bus and transaction-event tests."""

from __future__ import annotations

from django.test import TestCase

from apps.core.events import EntityCreated, EntityUpdated, EventBus


class EventBusTests(TestCase):
    def test_publish_invokes_matching_subscriber(self):
        bus = EventBus()
        received = []
        bus.subscribe(EntityCreated, lambda e: received.append(e))
        bus.publish(EntityCreated(entity_type="X", entity_id="1"))
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].entity_type, "X")

    def test_subscriber_for_base_type_receives_subclass(self):
        bus = EventBus()
        from apps.core.events import DomainEvent

        seen = []
        bus.subscribe(DomainEvent, lambda e: seen.append(type(e).__name__))
        bus.publish(EntityUpdated(entity_type="X", entity_id="1", changes={"a": 1}))
        self.assertEqual(seen, ["EntityUpdated"])

    def test_failing_subscriber_does_not_break_publish(self):
        bus = EventBus()
        ok = []

        def boom(_):
            raise RuntimeError("boom")

        bus.subscribe(EntityCreated, boom)
        bus.subscribe(EntityCreated, lambda e: ok.append(1))
        bus.publish(EntityCreated(entity_type="X", entity_id="1"))
        self.assertEqual(ok, [1])
