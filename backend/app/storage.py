"""File storage for Insure uploads.

Uploads go to the `insure-documents` bucket in Supabase Storage. Without
Supabase credentials the files are kept in process memory instead, so the
upload flow works in the demo and under test; those objects are addressed by
the same key shape and are lost on restart.
"""
from __future__ import annotations

import threading
import uuid
from abc import ABC, abstractmethod
from typing import Optional

from .config import get_settings

BUCKET = "insure-documents"


class FileStore(ABC):
    """Somewhere to put an uploaded document."""

    @abstractmethod
    def upload(self, *, key: str, data: bytes, content_type: str) -> str:
        """Store the bytes and return a reference URL."""

    @property
    @abstractmethod
    def backend_name(self) -> str: ...


class InMemoryFileStore(FileStore):
    """Process-local store, used when Supabase is not configured."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._objects: dict[str, tuple[bytes, str]] = {}

    @property
    def backend_name(self) -> str:
        return "in-memory"

    def upload(self, *, key: str, data: bytes, content_type: str) -> str:
        with self._lock:
            self._objects[key] = (data, content_type)
        return f"memory://{BUCKET}/{key}"

    def get(self, key: str) -> Optional[tuple[bytes, str]]:
        with self._lock:
            return self._objects.get(key)


class SupabaseFileStore(FileStore):
    """Supabase Storage, using the service-role key."""

    def __init__(self, url: str, service_role_key: str) -> None:
        from supabase import create_client

        self._client = create_client(url, service_role_key)

    @property
    def backend_name(self) -> str:
        return "supabase"

    def upload(self, *, key: str, data: bytes, content_type: str) -> str:
        bucket = self._client.storage.from_(BUCKET)
        bucket.upload(
            path=key,
            file=data,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        # The bucket is private, so hand back the storage path rather than a
        # public URL. Signed URLs are minted on read.
        return f"{BUCKET}/{key}"


def build_object_key(*, member_id: str, kind: str, filename: str) -> str:
    """Storage key for one upload.

    member_id is already hashed by the caller, so no raw identifier reaches
    the object path.
    """
    suffix = ""
    if "." in filename:
        suffix = "." + filename.rsplit(".", 1)[-1].lower()

    return f"{member_id}/{kind}-{uuid.uuid4()}{suffix}"


_file_store: Optional[FileStore] = None
_file_store_lock = threading.Lock()


def get_file_store() -> FileStore:
    """Return the process-wide file store, building it on first use."""
    global _file_store

    with _file_store_lock:
        if _file_store is None:
            settings = get_settings()
            if settings.supabase_configured:
                _file_store = SupabaseFileStore(
                    settings.supabase_url, settings.supabase_service_role_key
                )
            else:
                _file_store = InMemoryFileStore()
        return _file_store


def reset_file_store(store: Optional[FileStore] = None) -> FileStore:
    """Swap the file store. Used by tests."""
    global _file_store

    with _file_store_lock:
        _file_store = store or InMemoryFileStore()
        return _file_store
