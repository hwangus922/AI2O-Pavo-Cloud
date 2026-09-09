"""RSA-2048 identity for organizations.

An organization's key pair is generated once. The public key is stored; the
private key is returned to the organization at creation and is never written
to the database — only a SHA-256 digest of it is kept, so an organization can
prove which key it controls.

Messages are signed over the SHA-256 digest of the canonical payload using
RSASSA-PSS.
"""
from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

KEY_SIZE = 2048
PUBLIC_EXPONENT = 65537

# Marks the algorithm in the signature string, so a future scheme change is
# distinguishable on sight.
SIGNATURE_PREFIX = "rsa-pss-sha256"


class SignatureVerificationError(Exception):
    """Raised when a signature does not verify against a public key."""


def generate_key_pair() -> tuple[str, str]:
    """Generate an RSA-2048 key pair.

    Returns (private_key_pem, public_key_pem).
    """
    private_key = rsa.generate_private_key(
        public_exponent=PUBLIC_EXPONENT, key_size=KEY_SIZE
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )

    return private_pem, public_pem


def hash_private_key(private_key_pem: str) -> str:
    """SHA-256 digest of a private key.

    This is what the database holds — enough to recognize the key, never
    enough to reconstruct it.
    """
    digest = hashlib.sha256(private_key_pem.strip().encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def canonical_payload(payload: dict[str, Any]) -> bytes:
    """Serialize deterministically so a signature is reproducible."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def payload_digest(payload: dict[str, Any]) -> str:
    """SHA-256 digest of the canonical payload, for the audit trail."""
    return hashlib.sha256(canonical_payload(payload)).hexdigest()


def sign_payload(payload: dict[str, Any], private_key_pem: str) -> str:
    """Sign the SHA-256 digest of a payload with an organization's private key."""
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"), password=None
    )

    signature = private_key.sign(
        canonical_payload(payload),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    return f"{SIGNATURE_PREFIX}:{base64.b64encode(signature).decode('ascii')}"


def verify_payload(
    payload: dict[str, Any], signature: str, public_key_pem: str
) -> bool:
    """Verify a signature against an organization's public key."""
    if not signature or not public_key_pem:
        return False

    prefix, _, encoded = signature.partition(":")
    if prefix != SIGNATURE_PREFIX or not encoded:
        return False

    try:
        raw_signature = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError):
        return False

    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False

    try:
        public_key.verify(
            raw_signature,
            canonical_payload(payload),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
    except InvalidSignature:
        return False

    return True
