"""System-wide statistics, activity feed, and the full audit trail."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from ..db import Repository, get_repository

router = APIRouter(prefix="/api/system", tags=["system"])


def _parse_timestamp(value: Any) -> Optional[datetime]:
    """Parse an ISO timestamp from either storage backend."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def average_resolution_seconds(requests: list[dict[str, Any]]) -> Optional[float]:
    """Mean seconds from created_at to resolved_at across resolved requests."""
    durations: list[float] = []

    for request in requests:
        created = _parse_timestamp(request.get("created_at"))
        resolved = _parse_timestamp(request.get("resolved_at"))
        if created and resolved and resolved >= created:
            durations.append((resolved - created).total_seconds())

    return sum(durations) / len(durations) if durations else None


@router.get("/stats")
def system_stats(
    repository: Repository = Depends(get_repository),
) -> dict[str, Any]:
    """Live counters for the dashboard."""
    requests = repository.list_auth_requests(limit=500)
    appeals = repository.list_appeals(limit=500)
    proofs = repository.list_zk_proofs(limit=500)
    messages = repository.list_aria_messages_recent(limit=500)

    won = sum(1 for appeal in appeals if appeal.get("status") == "won")
    lost = sum(1 for appeal in appeals if appeal.get("status") == "lost")
    decided = won + lost

    by_status: dict[str, int] = {}
    for request in requests:
        status = str(request.get("status") or "unknown")
        by_status[status] = by_status.get(status, 0) + 1

    return {
        "authorizations_processed": len(requests),
        "requests_by_status": by_status,
        "average_resolution_seconds": average_resolution_seconds(requests),
        "appeals_total": len(appeals),
        "appeals_decided": decided,
        "appeals_win_rate": (won / decided) if decided else None,
        "zk_proofs_generated": len(proofs),
        "aria_messages_exchanged": len(messages),
        "price_queries": len(repository.list_price_queries(limit=500)),
    }


@router.get("/activity")
def recent_activity(
    limit: int = Query(default=10, ge=1, le=50),
    repository: Repository = Depends(get_repository),
) -> list[dict[str, Any]]:
    """The most recent ARIA messages, newest first."""
    return repository.list_aria_messages_recent(limit=limit)


@router.get("/audit")
def full_audit_trail(
    entity_type: Optional[str] = Query(default=None),
    since: Optional[str] = Query(
        default=None, description="ISO date or timestamp lower bound."
    ),
    until: Optional[str] = Query(
        default=None, description="ISO date or timestamp upper bound."
    ),
    limit: int = Query(default=500, ge=1, le=1000),
    repository: Repository = Depends(get_repository),
) -> list[dict[str, Any]]:
    """Every audit entry across the system, newest first."""
    rows = repository.list_audit_log_all(limit=limit)

    if entity_type:
        rows = [row for row in rows if row.get("entity_type") == entity_type]

    since_at = _parse_timestamp(since)
    until_at = _parse_timestamp(until)

    if since_at or until_at:
        filtered: list[dict[str, Any]] = []
        for row in rows:
            created = _parse_timestamp(row.get("created_at"))
            if created is None:
                continue
            # Compare naive against naive so a date-only bound still works.
            reference = created.replace(tzinfo=None)
            if since_at and reference < since_at.replace(tzinfo=None):
                continue
            if until_at and reference > until_at.replace(tzinfo=None):
                continue
            filtered.append(row)
        rows = filtered

    return rows
