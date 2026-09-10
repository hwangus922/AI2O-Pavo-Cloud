"""Persistence and deployment paths the in-memory suite cannot reach.

The Supabase backend is exercised against a recording stub of the client, so
the repository is instantiated, every abstract method is implemented, and
each call hits the table it should — without a live database.
"""
from __future__ import annotations

from typing import Any

import pytest

from app.config import DEMO_PROVIDER_ORG_ID
from app.db import InMemoryRepository, Repository, SupabaseRepository, reset_repository
from app.identity import ensure_demo_org_keys, provision_org_key
from app.keyring import reset_keyring


# ------------------------------------------------------------ stub client


class _Result:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _Query:
    """Records the PostgREST-style call chain and returns canned rows."""

    def __init__(self, log: list[tuple[str, str, Any]], table: str) -> None:
        self._log = log
        self._table = table
        self._rows: list[dict[str, Any]] = [{"id": "row-1", "table": table}]

    def _record(self, op: str, *args: Any) -> "_Query":
        self._log.append((self._table, op, args))
        return self

    def select(self, *a: Any) -> "_Query":
        return self._record("select", *a)

    def insert(self, data: Any) -> "_Query":
        self._rows = [dict(data, id="row-1")] if isinstance(data, dict) else list(data)
        return self._record("insert", data)

    def update(self, changes: Any) -> "_Query":
        return self._record("update", changes)

    def upsert(self, data: Any) -> "_Query":
        return self._record("upsert", data)

    def eq(self, *a: Any) -> "_Query":
        return self._record("eq", *a)

    def is_(self, *a: Any) -> "_Query":
        return self._record("is_", *a)

    def order(self, *a: Any, **k: Any) -> "_Query":
        return self._record("order", *a, k)

    def limit(self, *a: Any) -> "_Query":
        return self._record("limit", *a)

    def execute(self) -> _Result:
        return _Result(self._rows)


class _StubClient:
    def __init__(self) -> None:
        self.log: list[tuple[str, str, Any]] = []

    def table(self, name: str) -> _Query:
        return _Query(self.log, name)


def _stub_repository() -> tuple[SupabaseRepository, _StubClient]:
    repository = SupabaseRepository.__new__(SupabaseRepository)
    client = _StubClient()
    repository._client = client
    return repository, client


def _tables(client: _StubClient, op: str) -> list[str]:
    return [table for table, called, _ in client.log if called == op]


# ------------------------------------------------------------------ tests


def test_supabase_repository_implements_the_whole_interface():
    """A deployment against Supabase must boot.

    Any abstract method left unimplemented makes the class impossible to
    instantiate, which fails the backend at startup — and never shows up in
    an in-memory test run.
    """
    assert SupabaseRepository.__abstractmethods__ == frozenset()
    assert Repository.__abstractmethods__ <= set(vars(SupabaseRepository))


def test_supabase_zk_proof_methods_hit_the_zk_proofs_table():
    repository, client = _stub_repository()

    inserted = repository.insert_zk_proof({"criteria": {}, "public_signals": []})
    assert inserted["id"] == "row-1"
    assert repository.get_zk_proof("row-1")["table"] == "zk_proofs"
    assert repository.update_zk_proof("row-1", {"verified": True})
    assert repository.list_zk_proofs(limit=5)

    assert _tables(client, "insert") == ["zk_proofs"]
    assert _tables(client, "update") == ["zk_proofs"]
    assert _tables(client, "select") == ["zk_proofs", "zk_proofs"]
    # Newest first, by the column the table actually has.
    assert ("zk_proofs", "order", ("generated_at", {"desc": True})) in client.log


def test_supabase_system_queries_read_newest_first():
    repository, client = _stub_repository()

    assert repository.list_aria_messages_recent(limit=3)
    assert repository.list_audit_log_all(limit=7)

    assert _tables(client, "select") == ["aria_messages", "audit_log"]
    assert ("aria_messages", "limit", (3,)) in client.log
    assert ("audit_log", "limit", (7,)) in client.log
    assert ("audit_log", "order", ("created_at", {"desc": True})) in client.log


def test_supabase_key_revocation_targets_only_active_keys():
    repository, client = _stub_repository()

    revoked = repository.revoke_active_org_keys(DEMO_PROVIDER_ORG_ID)

    assert revoked == 1
    assert ("org_keys", "eq", ("org_id", DEMO_PROVIDER_ORG_ID)) in client.log
    assert ("org_keys", "is_", ("revoked_at", "null")) in client.log
    update = next(args for t, op, args in client.log if t == "org_keys" and op == "update")
    assert update[0]["revoked_at"]


# --------------------------------------------------------- key rotation


@pytest.fixture(autouse=True)
def clean_state():
    reset_keyring()
    reset_repository()
    yield
    reset_repository()
    reset_keyring()


def _active_keys(repository: InMemoryRepository, org_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in repository._org_keys
        if row["org_id"] == org_id and row["revoked_at"] is None
    ]


def test_provisioning_rotates_to_exactly_one_active_key():
    """org_keys allows one active key per organization (a unique partial
    index), so re-issuing must revoke the previous key or the insert fails."""
    repository = InMemoryRepository()
    repository.ensure_demo_organizations()

    _, first_public = provision_org_key(repository, DEMO_PROVIDER_ORG_ID)
    _, second_public = provision_org_key(repository, DEMO_PROVIDER_ORG_ID)

    active = _active_keys(repository, DEMO_PROVIDER_ORG_ID)
    assert len(active) == 1
    assert active[0]["public_key"] == second_public
    assert repository.get_active_public_key(DEMO_PROVIDER_ORG_ID) == second_public
    assert first_public != second_public

    revoked = [r for r in repository._org_keys if r["revoked_at"] is not None]
    assert [r["public_key"] for r in revoked] == [first_public]


def test_second_boot_against_persisted_keys_rotates_cleanly():
    """Simulate a restart: the store keeps the previous boot's keys, the
    runtime keyring starts empty, and startup provisions again."""
    repository = InMemoryRepository()
    repository.ensure_demo_organizations()
    org_ids = [DEMO_PROVIDER_ORG_ID]

    reset_keyring()  # first boot starts with no keys in memory
    ensure_demo_org_keys(repository, org_ids)
    reset_keyring()  # process restart: private keys are gone
    ensure_demo_org_keys(repository, org_ids)

    assert len(_active_keys(repository, DEMO_PROVIDER_ORG_ID)) == 1
    assert len(repository._org_keys) == 2


# ------------------------------------------------------------- full boot


def test_backend_boots_against_supabase_twice(monkeypatch):
    """The deployment path end to end: Supabase configured, process started,
    then restarted. The SDK is replaced by the recording stub, so this checks
    everything the app does at boot short of the network."""
    import sys
    import types

    from app import db as db_module
    from app.config import get_settings

    client = _StubClient()
    fake_sdk = types.SimpleNamespace(create_client=lambda url, key: client)
    monkeypatch.setitem(sys.modules, "supabase", fake_sdk)
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role")
    get_settings.cache_clear()

    try:
        for boot in range(2):
            db_module._repository = None  # a fresh process
            reset_keyring()
            repository = db_module.get_repository()
            assert repository.backend_name == "supabase"

        org_key_ops = [op for t, op, _ in client.log if t == "org_keys"]
        # Every provisioning revokes before it inserts, on both boots, so the
        # unique active-key index is never violated.
        assert org_key_ops.count("insert") == 4  # two orgs x two boots
        assert org_key_ops.count("update") == 4
        first_insert = org_key_ops.index("insert")
        assert "update" in org_key_ops[:first_insert]
    finally:
        db_module._repository = None
        get_settings.cache_clear()
