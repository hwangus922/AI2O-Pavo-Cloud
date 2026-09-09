"""Organization identity provisioning.

Creating an organization generates an RSA-2048 key pair. The public key is
written to org_keys and onto the organization record; only a digest of the
private key is stored. The private key itself is returned to the caller once
and never persisted by Pavo.
"""
from __future__ import annotations

from typing import Any, Optional

from .crypto import generate_key_pair, hash_private_key
from .db import Repository
from .keyring import get_keyring


def provision_org_key(
    repository: Repository,
    org_id: str,
    *,
    retain_in_runtime_keyring: bool = False,
) -> tuple[str, str]:
    """Generate and register a key pair for an organization.

    Returns (private_key_pem, public_key_pem). The private key is the caller's
    only copy — Pavo stores just its digest.

    retain_in_runtime_keyring is for the Pavo-hosted demo agents, which need a
    key in memory to sign with. It never writes the key to storage.
    """
    private_key_pem, public_key_pem = generate_key_pair()

    repository.insert_org_key(
        {
            "org_id": org_id,
            "public_key": public_key_pem,
            "private_key_hash": hash_private_key(private_key_pem),
        }
    )
    repository.set_organization_public_key(org_id, public_key_pem)

    if retain_in_runtime_keyring:
        get_keyring().store(org_id, private_key_pem)

    return private_key_pem, public_key_pem


def ensure_demo_org_keys(repository: Repository, org_ids: list[str]) -> None:
    """Give each demo organization a key the in-process agents can sign with.

    Called at startup. Keys live only in the runtime keyring, so each boot
    issues a fresh pair.
    """
    keyring = get_keyring()

    for org_id in org_ids:
        if keyring.has(org_id):
            continue
        provision_org_key(repository, org_id, retain_in_runtime_keyring=True)
