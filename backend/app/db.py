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
        return _repository


def reset_repository(repository: Optional[Repository] = None) -> Repository:
    """Swap the repository. Used by tests to get a clean store per case."""
    global _repository

    with _repository_lock:
        _repository = repository or InMemoryRepository()
        _repository.ensure_demo_organizations()
        return _repository
