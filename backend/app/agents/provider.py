"""Provider Agent.

Wakes on the EHR webhook, assembles a FHIR R4 bundle from the order, and sends
a signed ARIA AUTH_REQUEST to the payer agent. No human initiates any of this.
"""
from __future__ import annotations

from typing import Any, Optional

from .. import audit
from ..aria import build_message
from ..config import (
    DEMO_PAYER_ORG_ID,
    DEMO_PROVIDER_ORG_ID,
    PAYER_AGENT_ID,
    PROVIDER_AGENT_ID,
)
from ..db import Repository
from ..fhir import build_fhir_bundle, hash_patient_id
from ..models import AuthRequestCreate


def _sender_identity(repository: Repository, provider_org_id: str) -> dict[str, Any]:
    org = repository.get_organization(provider_org_id)
    return {
        "agent_id": PROVIDER_AGENT_ID,
        "org_id": provider_org_id,
        "npi": (org or {}).get("npi"),
        # Phase 1 trusts the demo NPI. Phase 3 verifies it live against the
        # CMS enrollment API before the flag is set.
        "verified": bool((org or {}).get("npi")),
    }


def _receiver_identity(repository: Repository, payer_org_id: str) -> dict[str, Any]:
    org = repository.get_organization(payer_org_id)
    return {
        "agent_id": PAYER_AGENT_ID,
        "org_id": payer_org_id,
        "payer_id": (org or {}).get("payer_id"),
    }


def submit_authorization_request(
    repository: Repository,
    payload: AuthRequestCreate,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create the auth request and the outbound ARIA AUTH_REQUEST.

    Returns (auth_request_row, aria_envelope).
    """
    provider_org_id = payload.provider_org_id or DEMO_PROVIDER_ORG_ID
    payer_org_id = payload.payer_org_id or DEMO_PAYER_ORG_ID

    provider_org = repository.get_organization(provider_org_id)
    hashed_patient_id = hash_patient_id(payload.patient_id)

    fhir_bundle = build_fhir_bundle(
        procedure_code=payload.procedure_code,
        diagnosis_code=payload.diagnosis_code,
        hashed_patient_id=hashed_patient_id,
        provider_npi=(provider_org or {}).get("npi"),
    )

    auth_request = repository.create_auth_request(
        {
            "provider_org_id": provider_org_id,
            "payer_org_id": payer_org_id,
            "patient_id": hashed_patient_id,
            "procedure_code": payload.procedure_code.strip().upper(),
            "diagnosis_code": payload.diagnosis_code.strip().upper(),
            "fhir_bundle": fhir_bundle,
            "status": "pending",
            "decision_rule_id": None,
            "confidence": None,
        }
    )

    audit.record(
        repository,
        entity_type="auth_request",
        entity_id=auth_request["id"],
        action="auth_request.created",
        actor_agent_id=PROVIDER_AGENT_ID,
        before_state=None,
        after_state={
            "status": "pending",
            "procedure_code": auth_request["procedure_code"],
            "diagnosis_code": auth_request["diagnosis_code"],
            "source": "ehr_webhook",
        },
    )

    envelope = build_message(
        payload_type="AUTH_REQUEST",
        payload={
            "auth_request_id": auth_request["id"],
            "procedure_code": auth_request["procedure_code"],
            "diagnosis_code": auth_request["diagnosis_code"],
            "patient_id": hashed_patient_id,
            "fhir_bundle": fhir_bundle,
        },
        sender=_sender_identity(repository, provider_org_id),
        receiver=_receiver_identity(repository, payer_org_id),
    )

    repository.insert_aria_message(
        {
            "message_id": envelope["message_id"],
            "auth_request_id": auth_request["id"],
            "sender_agent_id": PROVIDER_AGENT_ID,
            "receiver_agent_id": PAYER_AGENT_ID,
            "payload_type": "AUTH_REQUEST",
            "payload": envelope["payload"],
            "signature": envelope["signature"],
            "verified": True,
        }
    )

    audit.record(
        repository,
        entity_type="auth_request",
        entity_id=auth_request["id"],
        action="aria.auth_request.sent",
        actor_agent_id=PROVIDER_AGENT_ID,
        after_state={
            "message_id": envelope["message_id"],
            "receiver_agent_id": PAYER_AGENT_ID,
        },
    )

    return auth_request, envelope
