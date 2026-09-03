"""Notification dispatch service."""

from __future__ import annotations

import logging
from typing import Optional

from apps.notifications.models import Notification
from apps.notifications.providers import InAppProvider

logger = logging.getLogger("apps.notifications")

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
    """Create an in-app notification and fan out to any extra channels.

    A failing extra channel never breaks the caller or the in-app record: the
    failure is logged (with the provider name) and the in-app notification
    stands. NotImplementedError covers providers whose channel is not enabled
    yet; any other provider error is caught and logged the same way so a
    misbehaving channel cannot take down a workflow decision or an audit write.
    """
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
        except Exception:  # noqa: BLE001 - a failing channel must never break the caller
            logger.warning(
                "Notification provider %s failed; in-app notification %s kept.",
                provider.__class__.__name__,
                notification.pk,
                exc_info=True,
            )
    return notification
