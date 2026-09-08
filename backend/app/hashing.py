"""Identifier hashing.

Raw member and patient identifiers are never stored. Everything that
identifies a person is hashed here first.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Optional


def hash_identifier(value: Optional[str], prefix: str) -> str:
    """SHA-256 hash an identifier, namespaced by a short prefix.

    A missing value still yields a stable synthetic identifier so downstream
    records are always well-formed.
    """
    raw = (value or "").strip()
    if not raw:
        raw = f"anonymous:{uuid.uuid4()}"
    return f"{prefix}_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]
