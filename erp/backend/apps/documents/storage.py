"""Storage abstraction.

Wraps Django's storage API so callers never touch the filesystem directly.
Local ``FileSystemStorage`` is used in dev; swapping to an S3-compatible backend
(e.g. MinIO) in production is a settings change only — no call-site changes.
Internal absolute paths are never exposed to clients; downloads always stream
through an authorized view.
"""

from __future__ import annotations

from django.core.files.base import File
from django.core.files.storage import default_storage


class DocumentStorage:
    def __init__(self, backend=None):
        self._backend = backend or default_storage

    def save(self, key: str, content: File) -> str:
        return self._backend.save(key, content)

    def open(self, key: str, mode: str = "rb") -> File:
        return self._backend.open(key, mode)

    def delete(self, key: str) -> None:
        if self._backend.exists(key):
            self._backend.delete(key)

    def exists(self, key: str) -> bool:
        return self._backend.exists(key)

    def size(self, key: str) -> int:
        return self._backend.size(key)


storage = DocumentStorage()
