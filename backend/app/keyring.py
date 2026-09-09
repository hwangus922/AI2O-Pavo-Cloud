"""Runtime holder for the demo agents' private keys.

In production an organization holds its own private key and signs before a
message ever reaches Pavo. In this prototype Pavo also runs the provider and
payer agents, so those agents need a key to sign with.

This module keeps those keys in process memory only. Nothing here is written
to the database or to disk, and everything is lost on restart — which is why
the demo organizations get a fresh key pair each boot. It exists so the signed
message flow is demoable end to end; it is not how a real deployment holds
key material.
"""
from __future__ import annotations

import threading
from typing import Optional


class RuntimeKeyring:
    """In-memory map of org_id -> private key PEM."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._keys: dict[str, str] = {}

    def store(self, org_id: str, private_key_pem: str) -> None:
        with self._lock:
            self._keys[org_id] = private_key_pem

    def get(self, org_id: str) -> Optional[str]:
        with self._lock:
            return self._keys.get(org_id)

    def has(self, org_id: str) -> bool:
        with self._lock:
            return org_id in self._keys

    def clear(self) -> None:
        with self._lock:
            self._keys.clear()


_keyring = RuntimeKeyring()


def get_keyring() -> RuntimeKeyring:
    return _keyring


def reset_keyring() -> RuntimeKeyring:
    """Drop every held key. Used by tests."""
    _keyring.clear()
    return _keyring
