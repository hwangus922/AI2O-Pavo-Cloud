"""ARIA v1.0 — agent message envelope, signing, and verification.

Phase 1 signs with an HMAC over the canonical JSON of the envelope. Real
org-level key pairs and live NPI verification against the CMS registry land in
Phase 3; the envelope shape and the verify path are the same either way.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .config import get_settings

# Phase 1 shared demo secret. Phase 3 replaces this with per-org key pairs.
_DEMO_SIGNING_SECRET = b"pavo-phase1-demo-signing-key"

# Fields covered by the signature. "signature" itself is excluded.
_SIGNED_FIELDS = (
    "aria_version",
    "message_id",
    "timestamp",
    "sender",
    "receiver",
    "payload_type",
    "payload",
)


def _canonical_json(payload: dict[str, Any]) -> bytes:
    """Serialize deterministically so a signature is reproducible."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_message(envelope: dict[str, Any]) -> str:
    """Return the HMAC-SHA256 signature for an ARIA envelope."""
    signed_view = {field: envelope.get(field) for field in _SIGNED_FIELDS}
    digest = hmac.new(
        _DEMO_SIGNING_SECRET, _canonical_json(signed_view), hashlib.sha256
    ).hexdigest()
    return f"sha256:{digest}"


def verify_message(envelope: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Verify an envelope's signature.

    Returns (verified, reason). The reason is None when verification passes and
    a short explanation otherwise.
    """
    provided = envelope.get("signature")
    if not provided:
        return False, "Envelope carries no signature."

    missing = [f for f in _SIGNED_FIELDS if f not in envelope]
    if missing:
        return False, f"Envelope is missing signed field(s): {', '.join(missing)}."

    expected = sign_message(envelope)
    if not hmac.compare_digest(str(provided), expected):
        return False, "Signature does not match the envelope contents."

    return True, None


def build_message(
    *,
    payload_type: str,
    payload: dict[str, Any],
    sender: dict[str, Any],
    receiver: dict[str, Any],
    message_id: Optional[str] = None,
) -> dict[str, Any]:
    """Build a signed ARIA envelope."""
    settings = get_settings()

    envelope: dict[str, Any] = {
        "aria_version": settings.aria_version,
        "message_id": message_id or str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "sender": sender,
        "receiver": receiver,
        "payload_type": payload_type,
        "payload": payload,
    }
    envelope["signature"] = sign_message(envelope)
    return envelope
