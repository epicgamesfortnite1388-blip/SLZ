"""Upload validation and filename safety."""

from __future__ import annotations

import os
import re
import unicodedata
import uuid

from django.conf import settings

from apps.core.exceptions import ValidationError

_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    """Return a filesystem-safe base filename (no directory components)."""
    name = os.path.basename(name or "").strip()
    name = unicodedata.normalize("NFKD", name)
    name = _SAFE_CHARS.sub("_", name)
    name = name.strip("._") or "file"
    return name[:200]


def get_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lstrip(".").lower()


def quoted_header_filename(name: str) -> str:
    """Make an original filename safe to embed in a ``Content-Disposition``
    quoted-string. Escapes the characters that can break out of the quoting
    (``"`` and ``\\``) or crash header serialization (CR/LF); everything else
    is preserved so users still get a meaningful download name."""
    for ch in ('"', "\\", "\r", "\n"):
        name = name.replace(ch, "_")
    return name


def validate_upload(uploaded_file) -> None:
    """Enforce size and extension policy from settings."""
    max_bytes = getattr(settings, "DOCUMENTS_MAX_UPLOAD_BYTES", 25 * 1024 * 1024)
    if uploaded_file.size > max_bytes:
        raise ValidationError(
            f"File exceeds the maximum allowed size of {max_bytes} bytes.",
            code="documents.file.too_large",
        )
    allowed = {e.lower() for e in getattr(settings, "DOCUMENTS_ALLOWED_EXTENSIONS", [])}
    ext = get_extension(uploaded_file.name)
    if allowed and ext not in allowed:
        raise ValidationError(
            f"File type '.{ext}' is not permitted.",
            code="documents.file.type_not_allowed",
            details={"allowed": sorted(allowed)},
        )


def build_storage_key(entity_type: str, entity_id: str, filename: str) -> str:
    """Opaque, non-guessable storage key that never leaks internal paths."""
    safe = sanitize_filename(filename)
    bucket = sanitize_filename(entity_type).lower()
    return f"documents/{bucket}/{entity_id}/{uuid.uuid4().hex}_{safe}"
