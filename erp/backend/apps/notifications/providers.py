"""Delivery-channel providers.

In-app is the only channel implemented now. Email/SMS/push are defined as
interfaces so future work plugs in without touching call sites. The dispatcher
always persists an in-app record, then fans out to any enabled extra channels.
"""

from __future__ import annotations

import abc
import logging

logger = logging.getLogger("apps.notifications")


class NotificationProvider(abc.ABC):
    channel: str = "abstract"

    @abc.abstractmethod
    def send(self, *, recipient, title: str, body: str, metadata: dict) -> None: ...


class InAppProvider(NotificationProvider):
    channel = "in_app"

    def send(self, *, recipient, title, body, metadata) -> None:
        # The dispatcher persists the DB row; nothing else to do here.
        return None


class EmailProvider(NotificationProvider):
    channel = "email"

    def send(self, *, recipient, title, body, metadata) -> None:  # pragma: no cover
        raise NotImplementedError(
            "Email delivery is not enabled yet (deferred; see decision register)."
        )


class SMSProvider(NotificationProvider):
    channel = "sms"

    def send(self, *, recipient, title, body, metadata) -> None:  # pragma: no cover
        raise NotImplementedError(
            "SMS delivery is not enabled yet (deferred; see decision register)."
        )
