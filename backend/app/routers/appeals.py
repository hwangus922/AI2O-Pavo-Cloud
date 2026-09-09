"""Appeal listing and outcome statistics."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ..db import Repository, get_repository
from ..models import AppealRecord

router = APIRouter(prefix="/api/appeals", tags=["appeals"])


@router.get("", response_model=list[AppealRecord])
def list_appeals(
    limit: int = Query(default=200, ge=1, le=500),
    repository: Repository = Depends(get_repository),
) -> list[dict[str, Any]]:
    """List appeals, newest first."""
    return repository.list_appeals(limit=limit)


@router.get("/stats")
def appeal_stats(
    repository: Repository = Depends(get_repository),
) -> dict[str, Any]:
    """Appeal outcome counts and win rate.

    Win rate is won / (won + lost). It is null until at least one appeal has
    been decided, so the dashboard shows no rate rather than a misleading 0%.
    """
    appeals = repository.list_appeals(limit=500)

    counts = {"draft": 0, "submitted": 0, "won": 0, "lost": 0, "escalated": 0}
    for appeal in appeals:
        status = appeal.get("status")
        if status in counts:
            counts[status] += 1

    decided = counts["won"] + counts["lost"]

    return {
        "total": len(appeals),
        "counts": counts,
        "decided": decided,
        "win_rate": (counts["won"] / decided) if decided else None,
    }


@router.get("/{appeal_id}", response_model=AppealRecord)
def get_appeal(
    appeal_id: str,
    repository: Repository = Depends(get_repository),
) -> dict[str, Any]:
    """Retrieve one appeal."""
    appeal = repository.get_appeal(appeal_id)
    if appeal is None:
        raise HTTPException(status_code=404, detail="Appeal not found.")
    return appeal
