"""Authorization request routes."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..agents.appeals import generate_appeal
from ..agents.payer import (
    AriaVerificationError,
    handle_appeal,
    handle_auth_request,
)
from ..agents.provider import submit_authorization_request
from ..db import Repository, get_repository
from ..models import (
    AppealCreate,
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
    status: Optional[str] = Query(
        default=None,
        description="Filter by status: pending, approved, denied, escalated, appealed.",
    ),
    repository: Repository = Depends(get_repository),
) -> list[dict[str, Any]]:
    """List authorization requests, newest first."""
    rows = repository.list_auth_requests(limit=limit)

    if status:
        rows = [row for row in rows if row.get("status") == status]

    return rows


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
        "appeals": repository.list_appeals_for_request(request_id),
    }


@router.post("/{request_id}/appeal", status_code=201)
def appeal_auth_request(
    request_id: str,
    payload: AppealCreate,
    repository: Repository = Depends(get_repository),
) -> dict[str, Any]:
    """Generate an appeal for a denied authorization request.

    A coverage exclusion escalates without a letter. Anything else is drafted
    with supporting literature, then submitted over ARIA when confidence
    clears the threshold and escalated to a human when it does not.
    """
    auth_request = repository.get_auth_request(request_id)
    if auth_request is None:
        raise HTTPException(status_code=404, detail="Authorization request not found.")

    if auth_request.get("status") not in {"denied", "escalated"}:
        raise HTTPException(
            status_code=409,
            detail=(
                "Only a denied or escalated request can be appealed; this one is "
                f"{auth_request.get('status')!r}."
            ),
        )

    outcome = generate_appeal(
        repository,
        auth_request,
        denial_reason_code=payload.denial_reason_code,
    )

    response: dict[str, Any] = {
        "appeal": outcome["appeal"],
        "denial_reason_category": outcome["category"],
        "citations": outcome["citations"],
        "letter_source": outcome["letter_source"],
        "pubmed_error": outcome["pubmed_error"],
        "reviewer_notes": outcome["reviewer_notes"],
    }

    # A submitted appeal goes to the payer agent for a decision immediately.
    envelope = outcome.get("envelope")
    if envelope is not None:
        try:
            payer_response, decision = handle_appeal(repository, envelope)
        except AriaVerificationError as exc:
            raise HTTPException(
                status_code=502, detail=f"ARIA verification failed: {exc}"
            ) from exc

        response["decision"] = decision.model_dump()
        response["appeal"] = repository.get_appeal(outcome["appeal"]["id"])
        response["response_message_id"] = payer_response["message_id"]

    response["request"] = repository.get_auth_request(request_id)
    return response
