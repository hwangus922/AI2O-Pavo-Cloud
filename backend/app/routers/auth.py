"""Authorization request routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ..agents.payer import AriaVerificationError, handle_auth_request
from ..agents.provider import submit_authorization_request
from ..db import Repository, get_repository
from ..models import (
    AriaMessageRecord,
    AuditLogRecord,
    AuthRequestCreate,
    AuthRequestDetail,
    AuthRequestRecord,
)

router = APIRouter(prefix="/api/auth", tags=["authorization"])


@router.post("/request", status_code=201)
def create_auth_request(
    payload: AuthRequestCreate,
    repository: Repository = Depends(get_repository),
) -> dict[str, Any]:
    """Mock EHR webhook.

    Assembles a FHIR bundle via the Provider Agent, hands it to the Payer
    Agent, and returns the decision. The whole round trip is synchronous so the
    dashboard can show a decision immediately.
    """
    auth_request, request_envelope = submit_authorization_request(repository, payload)

    try:
        response_envelope, decision = handle_auth_request(repository, request_envelope)
    except AriaVerificationError as exc:
        raise HTTPException(
            status_code=502, detail=f"ARIA verification failed: {exc}"
        ) from exc

    resolved = repository.get_auth_request(auth_request["id"]) or auth_request

    return {
        "request": resolved,
        "decision": decision.model_dump(),
        "aria": {
            "request_message_id": request_envelope["message_id"],
            "response_message_id": response_envelope["message_id"],
        },
    }


@router.get("", response_model=list[AuthRequestRecord])
def list_auth_requests(
    limit: int = Query(default=100, ge=1, le=500),
    repository: Repository = Depends(get_repository),
) -> list[dict[str, Any]]:
    """List authorization requests, newest first."""
    return repository.list_auth_requests(limit=limit)


@router.get("/{request_id}", response_model=AuthRequestDetail)
def get_auth_request(
    request_id: str,
    repository: Repository = Depends(get_repository),
) -> dict[str, Any]:
    """One request with its full ARIA thread and audit trail."""
    request = repository.get_auth_request(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Authorization request not found.")

    return {
        "request": request,
        "aria_messages": repository.list_aria_messages(request_id),
        "audit_log": repository.list_audit_log(request_id),
    }
