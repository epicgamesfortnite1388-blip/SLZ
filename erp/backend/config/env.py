"""Lightweight, dependency-free environment loading.

Reads an optional ``.env`` file (KEY=VALUE lines) from the backend root and
exposes typed getters over ``os.environ``. Kept stdlib-only so settings can be
imported before third-party packages are guaranteed to be present.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

_BOOL_TRUE = {"1", "true", "yes", "on"}


def load_dotenv(path: Path) -> None:
    """Populate os.environ from a .env file if it exists (does not override)."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name, default)


def get_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in _BOOL_TRUE


def get_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    try:
        return int(raw) if raw is not None else default
    except (TypeError, ValueError):
        return default


def get_list(name: str, default: Optional[List[str]] = None) -> List[str]:
    raw = os.environ.get(name)
    if not raw:
        return list(default or [])
    return [item.strip() for item in raw.split(",") if item.strip()]
