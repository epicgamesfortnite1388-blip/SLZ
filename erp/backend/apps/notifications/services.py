"""Notification dispatch service."""

from __future__ import annotations

from typing import Optional

from apps.notifications.models import Notification
from apps.notifications.providers import InAppProvider

_inapp = InAppProvider()


def notify(
    *,
    recipient,
    type: str,
    title: str,
    body: str = "",
    entity_type: str = "",
    entity_id: str = "",
    extra_channels: Optional[list] = None,
) -> Notification:
    """Create an in-app notification and fan out to any extra channels."""
    notification = Notification.objects.create(
        recipient=recipient,
        type=type,
        title=title,
        body=body,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else "",
    )
    _inapp.send(recipient=recipient, title=title, body=body, metadata={})
    for provider in extra_channels or []:
        try:
            provider.send(recipient=recipient, title=title, body=body, metadata={})
        except NotImplementedError:
            # Channel not enabled yet; the in-app record still stands.
            pass
    return notification
