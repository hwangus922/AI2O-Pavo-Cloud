"""ARIA v1.0 — agent message envelope, signing, and verification.

Every message is signed over the SHA-256 digest of its canonical contents with
the sending organization's RSA-2048 private key, and verified against that
organization's stored public key. A message that fails verification is
rejected; the caller records the rejection in the audit log.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .config import get_settings
from .crypto import payload_digest, sign_payload, verify_payload
from .db import Repository
from .keyring import get_keyring

# Fields covered by the signature. "signature" itself is excluded.
SIGNED_FIELDS = (
    "aria_version",
    "message_id",
    "timestamp",
    "sender",
    "receiver",
    "payload_type",
    "payload",
)


class MissingSigningKeyError(RuntimeError):
    """Raised when the sending organization has no private key available."""


def signed_view(envelope: dict[str, Any]) -> dict[str, Any]:
    """The subset of an envelope that the signature covers."""
    return {field: envelope.get(field) for field in SIGNED_FIELDS}


def digest_of(envelope: dict[str, Any]) -> str:
    """SHA-256 digest of the signed portion of an envelope."""
    return payload_digest(signed_view(envelope))


def sign_envelope(envelope: dict[str, Any], private_key_pem: str) -> str:
    """Sign an envelope with an organization's private key."""
    return sign_payload(signed_view(envelope), private_key_pem)


def verify_envelope(
    envelope: dict[str, Any], public_key_pem: str
) -> tuple[bool, Optional[str]]:
    """Verify an envelope against a public key.

    Returns (verified, reason); reason is None when verification passes.
    """
    signature = envelope.get("signature")
    if not signature:
        return False, "Envelope carries no signature."

    missing = [field for field in SIGNED_FIELDS if field not in envelope]
    if missing:
        return False, f"Envelope is missing signed field(s): {', '.join(missing)}."

    if not public_key_pem:
        return False, "No public key is on file for the sending organization."

    if not verify_payload(signed_view(envelope), str(signature), public_key_pem):
        return False, "Signature does not match the envelope contents."

    return True, None


def verify_with_repository(
    repository: Repository, envelope: dict[str, Any]
) -> tuple[bool, Optional[str]]:
    """Verify an envelope against the sender's registered public key."""
    sender_org_id = (envelope.get("sender") or {}).get("org_id")
    if not sender_org_id:
        return False, "Envelope does not name a sending organization."

    public_key = repository.get_active_public_key(sender_org_id)
    if not public_key:
        return (
            False,
            f"No active signing key is registered for organization {sender_org_id}.",
        )

    return verify_envelope(envelope, public_key)


def build_message(
    *,
    payload_type: str,
    payload: dict[str, Any],
    sender: dict[str, Any],
    receiver: dict[str, Any],
    private_key_pem: Optional[str] = None,
    message_id: Optional[str] = None,
) -> dict[str, Any]:
    """Build and sign an ARIA envelope.

    The signing key is taken from the runtime keyring using the sender's
    org_id unless one is passed explicitly.
    """
    settings = get_settings()

    envelope: dict[str, Any] = {
        "aria_version": settings.aria_version,
        "message_id": message_id or str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sender": sender,
        "receiver": receiver,
        "payload_type": payload_type,
        "payload": payload,
    }

    if private_key_pem is None:
        sender_org_id = sender.get("org_id")
        private_key_pem = (
            get_keyring().get(sender_org_id) if sender_org_id else None
        )

    if not private_key_pem:
        raise MissingSigningKeyError(
            "No private key is available for organization "
            f"{sender.get('org_id')!r}; cannot sign this message."
        )

    envelope["signature"] = sign_envelope(envelope, private_key_pem)
    return envelope
