"""Persistence layer.

Two interchangeable backends sit behind one interface:

* SupabaseRepository — used when SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
  are both set.
* InMemoryRepository — the fallback, so the demo and the test suite run with
  no external dependencies. Data lives for the life of the process only.

Both write the same rows, so switching backends changes nothing upstream.
"""
from __future__ import annotations

import copy
import threading
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from .config import (
    DEMO_PAYER_ORG_ID,
    DEMO_PROVIDER_ORG_ID,
    get_settings,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _new_id() -> str:
    return str(uuid.uuid4())


DEMO_ORGANIZATIONS: tuple[dict[str, Any], ...] = (
    {
        "id": DEMO_PROVIDER_ORG_ID,
        "name": "Metro Valley Health Network",
        "type": "provider",
        "npi": "1598765432",
        "payer_id": None,
        "public_key": "demo-provider-public-key",
    },
    {
        "id": DEMO_PAYER_ORG_ID,
        "name": "Meridian Health Plan",
        "type": "payer",
        "npi": None,
        "payer_id": "MERIDIAN-001",
        "public_key": "demo-payer-public-key",
    },
)


class Repository(ABC):
    """Storage interface used by the agents and routers."""

    @abstractmethod
    def ensure_demo_organizations(self) -> None: ...

    @abstractmethod
    def get_organization(self, org_id: str) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    def create_auth_request(self, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def update_auth_request(
        self, request_id: str, changes: dict[str, Any]
    ) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    def get_auth_request(self, request_id: str) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    def list_auth_requests(self, limit: int = 100) -> list[dict[str, Any]]: ...

    @abstractmethod
    def insert_aria_message(self, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def list_aria_messages(self, auth_request_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def insert_audit_log(self, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def list_audit_log(self, entity_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def insert_insurance_document(self, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def get_insurance_document(
        self, document_id: str
    ) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    def insert_price_query(self, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def get_price_query(self, query_id: str) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    def list_price_queries(self, limit: int = 100) -> list[dict[str, Any]]: ...

    @abstractmethod
    def insert_org_key(self, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def get_active_public_key(self, org_id: str) -> Optional[str]: ...

    @abstractmethod
    def revoke_active_org_keys(self, org_id: str) -> int:
        """Revoke every active key for an organization; returns how many."""

    @abstractmethod
    def set_organization_public_key(self, org_id: str, public_key: str) -> None: ...

    @abstractmethod
    def insert_appeal(self, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def update_appeal(
        self, appeal_id: str, changes: dict[str, Any]
    ) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    def get_appeal(self, appeal_id: str) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    def list_appeals_for_request(
        self, auth_request_id: str
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    def list_appeals(self, limit: int = 200) -> list[dict[str, Any]]: ...

    @abstractmethod
    def insert_zk_proof(self, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def get_zk_proof(self, proof_id: str) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    def update_zk_proof(
        self, proof_id: str, changes: dict[str, Any]
    ) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    def list_zk_proofs(self, limit: int = 200) -> list[dict[str, Any]]: ...

    @abstractmethod
    def list_aria_messages_recent(self, limit: int = 10) -> list[dict[str, Any]]: ...

    @abstractmethod
    def list_audit_log_all(self, limit: int = 500) -> list[dict[str, Any]]: ...

    @property
    @abstractmethod
    def backend_name(self) -> str: ...


class InMemoryRepository(Repository):
    """Process-local store. Everything is lost on restart."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._organizations: dict[str, dict[str, Any]] = {}
        self._auth_requests: dict[str, dict[str, Any]] = {}
        self._aria_messages: list[dict[str, Any]] = []
        self._audit_log: list[dict[str, Any]] = []
        self._insurance_documents: dict[str, dict[str, Any]] = {}
        self._price_queries: dict[str, dict[str, Any]] = {}
        self._org_keys: list[dict[str, Any]] = []
        self._appeals: dict[str, dict[str, Any]] = {}
        self._zk_proofs: dict[str, dict[str, Any]] = {}

    @property
    def backend_name(self) -> str:
        return "in-memory"

    def ensure_demo_organizations(self) -> None:
        with self._lock:
            for org in DEMO_ORGANIZATIONS:
                if org["id"] not in self._organizations:
                    row = dict(org)
                    row["created_at"] = _now_iso()
                    self._organizations[org["id"]] = row

    def get_organization(self, org_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            org = self._organizations.get(org_id)
            return copy.deepcopy(org) if org else None

    def create_auth_request(self, data: dict[str, Any]) -> dict[str, Any]:
        row = dict(data)
        row.setdefault("id", _new_id())
        row.setdefault("created_at", _now_iso())
        row.setdefault("resolved_at", None)
        with self._lock:
            self._auth_requests[row["id"]] = row
        return copy.deepcopy(row)

    def update_auth_request(
        self, request_id: str, changes: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._auth_requests.get(request_id)
            if row is None:
                return None
            row.update(changes)
            return copy.deepcopy(row)

    def get_auth_request(self, request_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._auth_requests.get(request_id)
            return copy.deepcopy(row) if row else None

    def list_auth_requests(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            rows = list(self._auth_requests.values())
        rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
        return copy.deepcopy(rows[:limit])

    def insert_aria_message(self, data: dict[str, Any]) -> dict[str, Any]:
        row = dict(data)
        row.setdefault("id", _new_id())
        row.setdefault("created_at", _now_iso())
        with self._lock:
            self._aria_messages.append(row)
        return copy.deepcopy(row)

    def list_aria_messages(self, auth_request_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = [
                r
                for r in self._aria_messages
                if r.get("auth_request_id") == auth_request_id
            ]
        rows.sort(key=lambda r: str(r.get("created_at") or ""))
        return copy.deepcopy(rows)

    def insert_audit_log(self, data: dict[str, Any]) -> dict[str, Any]:
        row = dict(data)
        row.setdefault("id", _new_id())
        row.setdefault("created_at", _now_iso())
        with self._lock:
            self._audit_log.append(row)
        return copy.deepcopy(row)

    def list_audit_log(self, entity_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = [r for r in self._audit_log if r.get("entity_id") == entity_id]
        rows.sort(key=lambda r: str(r.get("created_at") or ""))
        return copy.deepcopy(rows)

    def insert_insurance_document(self, data: dict[str, Any]) -> dict[str, Any]:
        row = dict(data)
        row.setdefault("id", _new_id())
        row.setdefault("created_at", _now_iso())
        with self._lock:
            self._insurance_documents[row["id"]] = row
        return copy.deepcopy(row)

    def get_insurance_document(self, document_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._insurance_documents.get(document_id)
            return copy.deepcopy(row) if row else None

    def insert_price_query(self, data: dict[str, Any]) -> dict[str, Any]:
        row = dict(data)
        row.setdefault("id", _new_id())
        row.setdefault("created_at", _now_iso())
        with self._lock:
            self._price_queries[row["id"]] = row
        return copy.deepcopy(row)

    def get_price_query(self, query_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._price_queries.get(query_id)
            return copy.deepcopy(row) if row else None

    def list_price_queries(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            rows = list(self._price_queries.values())
        rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
        return copy.deepcopy(rows[:limit])

    def insert_org_key(self, data: dict[str, Any]) -> dict[str, Any]:
        row = dict(data)
        row.setdefault("id", _new_id())
        row.setdefault("created_at", _now_iso())
        row.setdefault("revoked_at", None)
        with self._lock:
            self._org_keys.append(row)
        return copy.deepcopy(row)

    def get_active_public_key(self, org_id: str) -> Optional[str]:
        with self._lock:
            for row in reversed(self._org_keys):
                if row.get("org_id") == org_id and row.get("revoked_at") is None:
                    return row.get("public_key")
        return None

    def revoke_active_org_keys(self, org_id: str) -> int:
        revoked = 0
        with self._lock:
            for row in self._org_keys:
                if row.get("org_id") == org_id and row.get("revoked_at") is None:
                    row["revoked_at"] = _now_iso()
                    revoked += 1
        return revoked

    def set_organization_public_key(self, org_id: str, public_key: str) -> None:
        with self._lock:
            org = self._organizations.get(org_id)
            if org is not None:
                org["public_key"] = public_key

    def insert_appeal(self, data: dict[str, Any]) -> dict[str, Any]:
        row = dict(data)
        row.setdefault("id", _new_id())
        row.setdefault("created_at", _now_iso())
        row.setdefault("resolved_at", None)
        with self._lock:
            self._appeals[row["id"]] = row
        return copy.deepcopy(row)

    def update_appeal(
        self, appeal_id: str, changes: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._appeals.get(appeal_id)
            if row is None:
                return None
            row.update(changes)
            return copy.deepcopy(row)

    def get_appeal(self, appeal_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._appeals.get(appeal_id)
            return copy.deepcopy(row) if row else None

    def list_appeals_for_request(self, auth_request_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = [
                r
                for r in self._appeals.values()
                if r.get("auth_request_id") == auth_request_id
            ]
        rows.sort(key=lambda r: str(r.get("created_at") or ""))
        return copy.deepcopy(rows)

    def list_appeals(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock:
            rows = list(self._appeals.values())
        rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
        return copy.deepcopy(rows[:limit])

    def insert_zk_proof(self, data: dict[str, Any]) -> dict[str, Any]:
        row = dict(data)
        row.setdefault("id", _new_id())
        row.setdefault("generated_at", _now_iso())
        with self._lock:
            self._zk_proofs[row["id"]] = row
        return copy.deepcopy(row)

    def get_zk_proof(self, proof_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._zk_proofs.get(proof_id)
            return copy.deepcopy(row) if row else None

    def update_zk_proof(
        self, proof_id: str, changes: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._zk_proofs.get(proof_id)
            if row is None:
                return None
            row.update(changes)
            return copy.deepcopy(row)

    def list_zk_proofs(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock:
            rows = list(self._zk_proofs.values())
        rows.sort(key=lambda r: str(r.get("generated_at") or ""), reverse=True)
        return copy.deepcopy(rows[:limit])

    def list_aria_messages_recent(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._lock:
            rows = list(self._aria_messages)
        rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
        return copy.deepcopy(rows[:limit])

    def list_audit_log_all(self, limit: int = 500) -> list[dict[str, Any]]:
        with self._lock:
            rows = list(self._audit_log)
        rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
        return copy.deepcopy(rows[:limit])


class SupabaseRepository(Repository):
    """Supabase-backed store, using the service-role key."""

    def __init__(self, url: str, service_role_key: str) -> None:
        from supabase import create_client  # imported lazily

        self._client = create_client(url, service_role_key)

    @property
    def backend_name(self) -> str:
        return "supabase"

    def ensure_demo_organizations(self) -> None:
        # upsert is idempotent, so this is safe on every boot.
        self._client.table("organizations").upsert(
            [dict(org) for org in DEMO_ORGANIZATIONS]
        ).execute()

    def get_organization(self, org_id: str) -> Optional[dict[str, Any]]:
        result = (
            self._client.table("organizations")
            .select("*")
            .eq("id", org_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def create_auth_request(self, data: dict[str, Any]) -> dict[str, Any]:
        result = self._client.table("auth_requests").insert(data).execute()
        return result.data[0]

    def update_auth_request(
        self, request_id: str, changes: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        result = (
            self._client.table("auth_requests")
            .update(changes)
            .eq("id", request_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def get_auth_request(self, request_id: str) -> Optional[dict[str, Any]]:
        result = (
            self._client.table("auth_requests")
            .select("*")
            .eq("id", request_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def list_auth_requests(self, limit: int = 100) -> list[dict[str, Any]]:
        result = (
            self._client.table("auth_requests")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    def insert_aria_message(self, data: dict[str, Any]) -> dict[str, Any]:
        result = self._client.table("aria_messages").insert(data).execute()
        return result.data[0]

    def list_aria_messages(self, auth_request_id: str) -> list[dict[str, Any]]:
        result = (
            self._client.table("aria_messages")
            .select("*")
            .eq("auth_request_id", auth_request_id)
            .order("created_at")
            .execute()
        )
        return result.data or []

    def insert_audit_log(self, data: dict[str, Any]) -> dict[str, Any]:
        result = self._client.table("audit_log").insert(data).execute()
        return result.data[0]

    def list_audit_log(self, entity_id: str) -> list[dict[str, Any]]:
        result = (
            self._client.table("audit_log")
            .select("*")
            .eq("entity_id", entity_id)
            .order("created_at")
            .execute()
        )
        return result.data or []

    def insert_insurance_document(self, data: dict[str, Any]) -> dict[str, Any]:
        result = self._client.table("insurance_documents").insert(data).execute()
        return result.data[0]

    def get_insurance_document(self, document_id: str) -> Optional[dict[str, Any]]:
        result = (
            self._client.table("insurance_documents")
            .select("*")
            .eq("id", document_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def insert_price_query(self, data: dict[str, Any]) -> dict[str, Any]:
        result = self._client.table("price_queries").insert(data).execute()
        return result.data[0]

    def get_price_query(self, query_id: str) -> Optional[dict[str, Any]]:
        result = (
            self._client.table("price_queries")
            .select("*")
            .eq("id", query_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def list_price_queries(self, limit: int = 100) -> list[dict[str, Any]]:
        result = (
            self._client.table("price_queries")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    def insert_org_key(self, data: dict[str, Any]) -> dict[str, Any]:
        result = self._client.table("org_keys").insert(data).execute()
        return result.data[0]

    def get_active_public_key(self, org_id: str) -> Optional[str]:
        result = (
            self._client.table("org_keys")
            .select("public_key")
            .eq("org_id", org_id)
            .is_("revoked_at", "null")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0]["public_key"] if result.data else None

    def revoke_active_org_keys(self, org_id: str) -> int:
        result = (
            self._client.table("org_keys")
            .update({"revoked_at": _now_iso()})
            .eq("org_id", org_id)
            .is_("revoked_at", "null")
            .execute()
        )
        return len(result.data or [])

    def set_organization_public_key(self, org_id: str, public_key: str) -> None:
        self._client.table("organizations").update(
            {"public_key": public_key}
        ).eq("id", org_id).execute()

    def insert_appeal(self, data: dict[str, Any]) -> dict[str, Any]:
        result = self._client.table("appeals").insert(data).execute()
        return result.data[0]

    def update_appeal(
        self, appeal_id: str, changes: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        result = (
            self._client.table("appeals").update(changes).eq("id", appeal_id).execute()
        )
        return result.data[0] if result.data else None

    def get_appeal(self, appeal_id: str) -> Optional[dict[str, Any]]:
        result = (
            self._client.table("appeals")
            .select("*")
            .eq("id", appeal_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def list_appeals_for_request(self, auth_request_id: str) -> list[dict[str, Any]]:
        result = (
            self._client.table("appeals")
            .select("*")
            .eq("auth_request_id", auth_request_id)
            .order("created_at")
            .execute()
        )
        return result.data or []

    def list_appeals(self, limit: int = 200) -> list[dict[str, Any]]:
        result = (
            self._client.table("appeals")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    def insert_zk_proof(self, data: dict[str, Any]) -> dict[str, Any]:
        result = self._client.table("zk_proofs").insert(data).execute()
        return result.data[0]

    def get_zk_proof(self, proof_id: str) -> Optional[dict[str, Any]]:
        result = (
            self._client.table("zk_proofs")
            .select("*")
            .eq("id", proof_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def update_zk_proof(
        self, proof_id: str, changes: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        result = (
            self._client.table("zk_proofs")
            .update(changes)
            .eq("id", proof_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def list_zk_proofs(self, limit: int = 200) -> list[dict[str, Any]]:
        result = (
            self._client.table("zk_proofs")
            .select("*")
            .order("generated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    def list_aria_messages_recent(self, limit: int = 10) -> list[dict[str, Any]]:
        result = (
            self._client.table("aria_messages")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    def list_audit_log_all(self, limit: int = 500) -> list[dict[str, Any]]:
        result = (
            self._client.table("audit_log")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []


def _ensure_demo_keys(repository: Repository) -> None:
    """Issue signing keys for the demo organizations.

    Imported here rather than at module scope because identity depends on this
    module.
    """
    from .identity import ensure_demo_org_keys

    ensure_demo_org_keys(
        repository, [org["id"] for org in DEMO_ORGANIZATIONS]
    )


_repository: Optional[Repository] = None
_repository_lock = threading.Lock()


def get_repository() -> Repository:
    """Return the process-wide repository, building it on first use."""
    global _repository

    with _repository_lock:
        if _repository is None:
            settings = get_settings()
            if settings.supabase_configured:
                _repository = SupabaseRepository(
                    settings.supabase_url, settings.supabase_service_role_key
                )
            else:
                _repository = InMemoryRepository()
            _repository.ensure_demo_organizations()
            _ensure_demo_keys(_repository)
        return _repository


def reset_repository(repository: Optional[Repository] = None) -> Repository:
    """Swap the repository. Used by tests to get a clean store per case."""
    global _repository

    with _repository_lock:
        _repository = repository or InMemoryRepository()
        _repository.ensure_demo_organizations()
        _ensure_demo_keys(_repository)
        return _repository
