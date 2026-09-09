"""Payer Agent.

Receives an ARIA AUTH_REQUEST, verifies the envelope signature, runs the FHIR
bundle through the deterministic rule engine, writes the decision and its
rule_id to the audit log, and returns a signed AUTH_RESPONSE.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .. import audit
from ..aria import build_message, verify_with_repository
from ..config import PAYER_AGENT_ID, PROVIDER_AGENT_ID
from ..db import Repository
from ..models import Decision
from ..rules import evaluate_request


class AriaVerificationError(Exception):
    """Raised when an inbound envelope fails signature verification."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def handle_auth_request(
    repository: Repository,
    envelope: dict[str, Any],
    *,
    persist_inbound: bool = False,
) -> tuple[dict[str, Any], Decision]:
    """Evaluate an inbound AUTH_REQUEST and return (response_envelope, decision).

    persist_inbound is set when the message arrived over the wire at
    /api/aria/receive, so the inbound copy is recorded too. In the in-process
    Phase 1 flow the Provider Agent has already stored it.
    """
    verified, reason = verify_with_repository(repository, envelope)

    payload = envelope.get("payload", {}) or {}
    auth_request_id: Optional[str] = payload.get("auth_request_id")

    if persist_inbound and auth_request_id:
        repository.insert_aria_message(
            {
                "message_id": envelope.get("message_id"),
                "auth_request_id": auth_request_id,
                "sender_agent_id": (envelope.get("sender") or {}).get("agent_id"),
                "receiver_agent_id": (envelope.get("receiver") or {}).get("agent_id"),
                "payload_type": envelope.get("payload_type"),
                "payload": payload,
                "signature": envelope.get("signature"),
                "verified": verified,
            }
        )

    if not verified:
        if auth_request_id:
            audit.record(
                repository,
                entity_type="auth_request",
                entity_id=auth_request_id,
                action="aria.verification.failed",
                actor_agent_id=PAYER_AGENT_ID,
                after_state={"reason": reason, "message_id": envelope.get("message_id")},
            )
        raise AriaVerificationError(reason or "Signature verification failed.")

    if auth_request_id:
        audit.record(
            repository,
            entity_type="auth_request",
            entity_id=auth_request_id,
            action="aria.auth_request.received",
            actor_agent_id=PAYER_AGENT_ID,
            after_state={
                "message_id": envelope.get("message_id"),
                "signature_verified": True,
            },
        )

    fhir_bundle = payload.get("fhir_bundle", {}) or {}
    decision = evaluate_request(fhir_bundle)

    auth_request = (
        repository.get_auth_request(auth_request_id) if auth_request_id else None
    )

    if auth_request is not None:
        before_state = {
            "status": auth_request.get("status"),
            "decision_rule_id": auth_request.get("decision_rule_id"),
            "confidence": auth_request.get("confidence"),
        }
        after_state = {
            "status": decision.status,
            "decision_rule_id": decision.rule_id,
            "confidence": decision.confidence,
            "rule_description": decision.rule_description,
            "outcome": decision.outcome,
        }

        repository.update_auth_request(
            auth_request_id,
            {
                "status": decision.status,
                "decision_rule_id": decision.rule_id,
                "confidence": decision.confidence,
                "resolved_at": _now_iso(),
            },
        )

        audit.record(
            repository,
            entity_type="auth_request",
            entity_id=auth_request_id,
            action="decision.rendered",
            actor_agent_id=PAYER_AGENT_ID,
            before_state=before_state,
            after_state=after_state,
        )

    response = build_message(
        payload_type="AUTH_RESPONSE",
        payload={
            "auth_request_id": auth_request_id,
            "outcome": decision.outcome,
            "status": decision.status,
            "rule_id": decision.rule_id,
            "rule_description": decision.rule_description,
            "confidence": decision.confidence,
            "evaluated_at": _now_iso(),
        },
        sender={
            "agent_id": PAYER_AGENT_ID,
            "org_id": (envelope.get("receiver") or {}).get("org_id"),
            "payer_id": (envelope.get("receiver") or {}).get("payer_id"),
        },
        receiver={
            "agent_id": PROVIDER_AGENT_ID,
            "org_id": (envelope.get("sender") or {}).get("org_id"),
            "npi": (envelope.get("sender") or {}).get("npi"),
        },
    )

    if auth_request_id:
        repository.insert_aria_message(
            {
                "message_id": response["message_id"],
                "auth_request_id": auth_request_id,
                "sender_agent_id": PAYER_AGENT_ID,
                "receiver_agent_id": PROVIDER_AGENT_ID,
                "payload_type": "AUTH_RESPONSE",
                "payload": response["payload"],
                "signature": response["signature"],
                "verified": True,
            }
        )

        audit.record(
            repository,
            entity_type="auth_request",
            entity_id=auth_request_id,
            action="aria.auth_response.sent",
            actor_agent_id=PAYER_AGENT_ID,
            after_state={
                "message_id": response["message_id"],
                "outcome": decision.outcome,
                "rule_id": decision.rule_id,
            },
        )

    return response, decision


# Prototype rule: an appeal this well-supported is granted outright. A real
# payer would run the clinical review; the threshold stands in for it.
APPEAL_AUTO_APPROVE_CONFIDENCE = 0.85


def handle_appeal(
    repository: Repository,
    envelope: dict[str, Any],
    *,
    persist_inbound: bool = False,
) -> tuple[dict[str, Any], Decision]:
    """Evaluate an inbound ARIA APPEAL and return (response_envelope, decision).

    The signature is verified before the appeal is read, exactly as with an
    authorization request.
    """
    verified, reason = verify_with_repository(repository, envelope)

    payload = envelope.get("payload", {}) or {}
    auth_request_id: Optional[str] = payload.get("auth_request_id")
    appeal_id: Optional[str] = payload.get("appeal_id")

    if persist_inbound and auth_request_id:
        repository.insert_aria_message(
            {
                "message_id": envelope.get("message_id"),
                "auth_request_id": auth_request_id,
                "sender_agent_id": (envelope.get("sender") or {}).get("agent_id"),
                "receiver_agent_id": (envelope.get("receiver") or {}).get("agent_id"),
                "payload_type": envelope.get("payload_type"),
                "payload": payload,
                "signature": envelope.get("signature"),
                "verified": verified,
            }
        )

    if not verified:
        if appeal_id:
            audit.record(
                repository,
                entity_type="appeal",
                entity_id=appeal_id,
                action="aria.verification.failed",
                actor_agent_id=PAYER_AGENT_ID,
                after_state={"reason": reason, "message_id": envelope.get("message_id")},
            )
        raise AriaVerificationError(reason or "Signature verification failed.")

    confidence = float(payload.get("confidence") or 0.0)
    granted = confidence > APPEAL_AUTO_APPROVE_CONFIDENCE

    if granted:
        decision = Decision(
            outcome="APPROVED",
            rule_id="PAVO-A001",
            rule_description=(
                "Appeal granted: supporting clinical evidence exceeded the "
                f"{APPEAL_AUTO_APPROVE_CONFIDENCE} review threshold."
            ),
            confidence=confidence,
        )
        appeal_status = "won"
    else:
        # A denied appeal never ends the matter automatically — the request is
        # escalated so a human makes the final call.
        decision = Decision(
            outcome="ESCALATED",
            rule_id="PAVO-A002",
            rule_description=(
                "Appeal not granted on review; routed to a human reviewer rather "
                "than issuing a final denial."
            ),
            confidence=confidence,
        )
        appeal_status = "lost"

    if appeal_id:
        appeal = repository.get_appeal(appeal_id)
        before_state = {"status": (appeal or {}).get("status")}

        repository.update_appeal(
            appeal_id, {"status": appeal_status, "resolved_at": _now_iso()}
        )

        audit.record(
            repository,
            entity_type="appeal",
            entity_id=appeal_id,
            action="appeal.decided",
            actor_agent_id=PAYER_AGENT_ID,
            before_state=before_state,
            after_state={
                "status": appeal_status,
                "outcome": decision.outcome,
                "rule_id": decision.rule_id,
                "confidence": confidence,
                "auth_request_id": auth_request_id,
            },
        )

    if auth_request_id:
        auth_request = repository.get_auth_request(auth_request_id)
        if auth_request is not None:
            repository.update_auth_request(
                auth_request_id,
                {
                    "status": decision.status,
                    "decision_rule_id": decision.rule_id,
                    "confidence": confidence,
                    "resolved_at": _now_iso(),
                },
            )

            audit.record(
                repository,
                entity_type="auth_request",
                entity_id=auth_request_id,
                action="decision.rendered",
                actor_agent_id=PAYER_AGENT_ID,
                before_state={"status": auth_request.get("status")},
                after_state={
                    "status": decision.status,
                    "decision_rule_id": decision.rule_id,
                    "confidence": confidence,
                    "rule_description": decision.rule_description,
                    "outcome": decision.outcome,
                    "source": "appeal",
                },
            )

    response = build_message(
        payload_type="AUTH_RESPONSE",
        payload={
            "auth_request_id": auth_request_id,
            "appeal_id": appeal_id,
            "outcome": decision.outcome,
            "status": decision.status,
            "rule_id": decision.rule_id,
            "rule_description": decision.rule_description,
            "confidence": confidence,
            "appeal_status": appeal_status,
            "evaluated_at": _now_iso(),
        },
        sender={
            "agent_id": PAYER_AGENT_ID,
            "org_id": (envelope.get("receiver") or {}).get("org_id"),
        },
        receiver={
            "agent_id": (envelope.get("sender") or {}).get("agent_id"),
            "org_id": (envelope.get("sender") or {}).get("org_id"),
        },
    )

    if auth_request_id:
        repository.insert_aria_message(
            {
                "message_id": response["message_id"],
                "auth_request_id": auth_request_id,
                "sender_agent_id": PAYER_AGENT_ID,
                "receiver_agent_id": (envelope.get("sender") or {}).get("agent_id"),
                "payload_type": "AUTH_RESPONSE",
                "payload": response["payload"],
                "signature": response["signature"],
                "verified": True,
            }
        )

    return response, decision
