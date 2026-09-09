"""Zero-knowledge proof routes."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import audit
from ..db import Repository, get_repository
from ..models import ZkGenerateRequest, ZkVerifyRequest
from ..zk.prover import (
    ZkProofError,
    ZkUnavailableError,
    artifacts_available,
    build_criteria,
    describe_signals,
    generate_proof,
    proof_digest,
    verify_proof,
)

router = APIRouter(prefix="/api/zk", tags=["zero-knowledge"])

ZK_AGENT_ID = "agent://pavo/provider/zk-prover"


@router.get("/status")
def zk_status() -> dict[str, Any]:
    """Whether the circuit artifacts are built and ready."""
    return {
        "available": artifacts_available(),
        "circuit": "patient_criteria",
        "protocol": "groth16",
        "curve": "bn128",
    }


@router.post("/generate", status_code=201)
def generate_zk_proof(
    payload: ZkGenerateRequest,
    repository: Repository = Depends(get_repository),
) -> dict[str, Any]:
    """Prove the three patient criteria without revealing the clinical data.

    The response carries the proof and its public signals only. The age,
    diagnosis code, and deductible status are consumed to build the witness
    and are never returned or stored.
    """
    if payload.auth_request_id:
        auth_request = repository.get_auth_request(payload.auth_request_id)
        if auth_request is None:
            raise HTTPException(
                status_code=404, detail="Authorization request not found."
            )

    criteria = build_criteria(
        patient_age=payload.patient_age,
        diagnosis_code=payload.diagnosis_code,
        deductible_met=payload.deductible_met,
    )

    try:
        proof, public_signals = generate_proof(criteria)
    except ZkUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ZkProofError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Only the public half of the criteria is persisted; the private witness
    # is dropped here.
    stored_criteria = {
        **criteria["public"],
        "circuit": "patient_criteria",
        "protocol": "groth16",
    }

    record = repository.insert_zk_proof(
        {
            "auth_request_id": payload.auth_request_id,
            "criteria": stored_criteria,
            "proof": json.dumps(proof),
            "public_signals": public_signals,
            "verified": None,
        }
    )

    audit.record(
        repository,
        entity_type="zk_proof",
        entity_id=record["id"],
        action="zk_proof.generated",
        actor_agent_id=ZK_AGENT_ID,
        after_state={
            "auth_request_id": payload.auth_request_id,
            "proof_digest": proof_digest(proof),
            "claims": describe_signals(public_signals),
        },
    )

    return {
        "proof_id": record["id"],
        "proof": proof,
        "public_signals": public_signals,
        "proof_digest": proof_digest(proof),
        "claims": describe_signals(public_signals),
        "criteria": stored_criteria,
    }


@router.post("/verify")
def verify_zk_proof(
    payload: ZkVerifyRequest,
    repository: Repository = Depends(get_repository),
) -> dict[str, Any]:
    """Verify a proof against the circuit's verification key."""
    try:
        verified = verify_proof(payload.proof, payload.public_signals)
    except ZkUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ZkProofError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if payload.proof_id:
        repository.update_zk_proof(payload.proof_id, {"verified": verified})

    audit.record(
        repository,
        entity_type="zk_proof",
        entity_id=payload.proof_id or "unlinked",
        action="zk_proof.verified",
        actor_agent_id="agent://pavo/payer/zk-verifier",
        after_state={
            "verified": verified,
            "proof_digest": proof_digest(payload.proof),
            "claims": describe_signals(payload.public_signals),
        },
    )

    return {
        "verified": verified,
        "claims": describe_signals(payload.public_signals),
        "proof_digest": proof_digest(payload.proof),
    }


@router.get("/proofs")
def list_zk_proofs(
    limit: int = Query(default=200, ge=1, le=500),
    repository: Repository = Depends(get_repository),
) -> list[dict[str, Any]]:
    """List generated proofs, newest first."""
    return repository.list_zk_proofs(limit=limit)
