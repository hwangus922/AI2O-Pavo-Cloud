"""Audit trail routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ..db import Repository, get_repository
from ..models import AuditLogRecord

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/{entity_id}", response_model=list[AuditLogRecord])
def get_audit_trail(
    entity_id: str,
    repository: Repository = Depends(get_repository),
) -> list[dict[str, Any]]:
    """Full audit trail for any entity, oldest first."""
    return repository.list_audit_log(entity_id)
