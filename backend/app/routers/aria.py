"""ARIA protocol routes: the payer's inbound endpoint and signature checks."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..agents.payer import (
    AriaVerificationError,
    handle_appeal,
    handle_auth_request,
)
from ..aria import verify_with_repository
from ..db import Repository, get_repository
from ..models import VerifyRequest, VerifyResponse

router = APIRouter(prefix="/api/aria", tags=["aria"])


@router.post("/receive")
def receive_aria_message(
    envelope: dict[str, Any],
    repository: Repository = Depends(get_repository),
) -> dict[str, Any]:
    """Payer endpoint for inbound ARIA messages.

    Phase 1 handles AUTH_REQUEST. Other payload types are accepted and logged
    but not yet acted on.
    """
    payload_type = envelope.get("payload_type")

    handlers = {
        "AUTH_REQUEST": handle_auth_request,
        "APPEAL": handle_appeal,
    }
    handler = handlers.get(str(payload_type))

    if handler is None:
        raise HTTPException(
            status_code=422,
            detail=f"Payload type {payload_type!r} is not handled.",
        )

    try:
        response_envelope, decision = handler(
            repository, envelope, persist_inbound=True
        )
    except AriaVerificationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return {"response": response_envelope, "decision": decision.model_dump()}


@router.post("/verify", response_model=VerifyResponse)
def verify_aria_message(
    body: VerifyRequest,
    repository: Repository = Depends(get_repository),
) -> dict[str, Any]:
    """Verify an ARIA envelope against the sender's registered public key."""
    verified, reason = verify_with_repository(repository, body.message)
    return {
        "verified": verified,
        "message_id": body.message.get("message_id"),
        "reason": reason,
    }
