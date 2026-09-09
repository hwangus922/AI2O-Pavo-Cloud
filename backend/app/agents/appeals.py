"""Appeals Agent.

Wakes on a denied authorization, classifies the denial, gathers clinical
evidence, drafts an appeal, and either submits it over ARIA or escalates it to
a human reviewer.

Two rules hold regardless of what the model returns:
  * A "not_covered" denial is never appealed automatically — coverage is a
    contract question, so it goes straight to a human.
  * Nothing below the confidence threshold is submitted to a payer.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .. import audit
from ..appeals.classifier import classify_denial
from ..appeals.letter import generate_appeal_letter
from ..appeals.pubmed import find_supporting_evidence
from ..aria import build_message
from ..config import PAYER_AGENT_ID, PROVIDER_AGENT_ID, get_settings
from ..db import Repository
from ..fhir import CPT_DISPLAY, ICD10_DISPLAY

APPEALS_AGENT_ID = "agent://pavo/provider/appeals"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _reviewer_notes(
    *,
    reason: str,
    auth_request: dict[str, Any],
    category: str,
    denial_reason_code: str,
    confidence: float,
    citations: list[dict[str, Any]],
) -> str:
    """Pre-populate the context a human reviewer needs to act."""
    procedure = auth_request.get("procedure_code") or ""
    diagnosis = auth_request.get("diagnosis_code") or ""

    lines = [
        f"Escalation reason: {reason}",
        "",
        f"Authorization request: {auth_request.get('id')}",
        f"Procedure: {procedure} — {CPT_DISPLAY.get(procedure, 'no description on file')}",
        f"Diagnosis: {diagnosis} — {ICD10_DISPLAY.get(diagnosis, 'no description on file')}",
        f"Denial reason code: {denial_reason_code}",
        f"Denial category: {category}",
        f"Appeal confidence: {confidence:.2f}",
        f"Supporting citations retrieved: {len(citations)}",
    ]

    if citations:
        lines.append("")
        lines.append("Evidence on file:")
        for citation in citations:
            lines.append(
                f"  - PMID {citation.get('pmid')}: {citation.get('title')}"
            )

    return "\n".join(lines)


def generate_appeal(
    repository: Repository,
    auth_request: dict[str, Any],
    *,
    denial_reason_code: str,
    http_client: Optional[Any] = None,
) -> dict[str, Any]:
    """Run the appeal flow for one denied authorization request.

    Returns the stored appeal row, plus the reviewer notes when escalated.
    """
    settings = get_settings()
    auth_request_id = auth_request["id"]
    procedure_code = auth_request.get("procedure_code") or ""
    diagnosis_code = auth_request.get("diagnosis_code") or ""

    category = classify_denial(denial_reason_code)

    audit.record(
        repository,
        entity_type="auth_request",
        entity_id=auth_request_id,
        action="appeal.denial_classified",
        actor_agent_id=APPEALS_AGENT_ID,
        after_state={
            "denial_reason_code": denial_reason_code,
            "denial_reason_category": category,
        },
    )

    # Coverage exclusions are a contract question, not a clinical one. No
    # letter is drafted; a human decides.
    if category == "not_covered":
        appeal = repository.insert_appeal(
            {
                "auth_request_id": auth_request_id,
                "denial_reason_code": denial_reason_code,
                "denial_reason_category": category,
                "appeal_letter": None,
                "pubmed_citations": [],
                "confidence": 0.0,
                "status": "escalated",
            }
        )
        notes = _reviewer_notes(
            reason=(
                "The procedure is excluded from the plan. Coverage exclusions are "
                "not appealable on clinical grounds, so no letter was drafted."
            ),
            auth_request=auth_request,
            category=category,
            denial_reason_code=denial_reason_code,
            confidence=0.0,
            citations=[],
        )

        repository.update_auth_request(auth_request_id, {"status": "appealed"})

        audit.record(
            repository,
            entity_type="appeal",
            entity_id=appeal["id"],
            action="appeal.escalated",
            actor_agent_id=APPEALS_AGENT_ID,
            after_state={
                "auth_request_id": auth_request_id,
                "reason": "not_covered",
                "confidence": 0.0,
                "status": "escalated",
            },
        )

        return {
            "appeal": appeal,
            "category": category,
            "reviewer_notes": notes,
            "citations": [],
            "letter_source": "skipped",
            "pubmed_error": None,
        }

    # Everything else gets evidence gathering and a drafted letter.
    procedure_label = CPT_DISPLAY.get(procedure_code, procedure_code)
    diagnosis_label = ICD10_DISPLAY.get(diagnosis_code, diagnosis_code)

    citations, pubmed_error = find_supporting_evidence(
        procedure_label, diagnosis_label, client=http_client
    )

    audit.record(
        repository,
        entity_type="auth_request",
        entity_id=auth_request_id,
        action="appeal.evidence_retrieved",
        actor_agent_id=APPEALS_AGENT_ID,
        after_state={
            "citations": len(citations),
            "pmids": [c.get("pmid") for c in citations],
            "error": pubmed_error,
        },
    )

    drafted, letter_source = generate_appeal_letter(
        denial_reason_code=denial_reason_code,
        procedure_code=procedure_code,
        diagnosis_code=diagnosis_code,
        fhir_bundle=auth_request.get("fhir_bundle") or {},
        citations=citations,
    )

    confidence = drafted["confidence"]
    threshold = settings.appeal_confidence_threshold
    submitting = confidence >= threshold

    appeal = repository.insert_appeal(
        {
            "auth_request_id": auth_request_id,
            "denial_reason_code": denial_reason_code,
            "denial_reason_category": category,
            "appeal_letter": drafted["letter"],
            "pubmed_citations": citations,
            "confidence": confidence,
            "status": "submitted" if submitting else "escalated",
        }
    )

    reviewer_notes: Optional[str] = None

    if submitting:
        repository.update_auth_request(auth_request_id, {"status": "appealed"})

        envelope = build_message(
            payload_type="APPEAL",
            payload={
                "auth_request_id": auth_request_id,
                "appeal_id": appeal["id"],
                "denial_reason_code": denial_reason_code,
                "denial_reason_category": category,
                "procedure_code": procedure_code,
                "diagnosis_code": diagnosis_code,
                "confidence": confidence,
                "key_arguments": drafted["key_arguments"],
                "appeal_letter": drafted["letter"],
                "pubmed_citations": citations,
            },
            sender={
                "agent_id": APPEALS_AGENT_ID,
                "org_id": auth_request.get("provider_org_id"),
            },
            receiver={
                "agent_id": PAYER_AGENT_ID,
                "org_id": auth_request.get("payer_org_id"),
            },
        )

        repository.insert_aria_message(
            {
                "message_id": envelope["message_id"],
                "auth_request_id": auth_request_id,
                "sender_agent_id": APPEALS_AGENT_ID,
                "receiver_agent_id": PAYER_AGENT_ID,
                "payload_type": "APPEAL",
                "payload": envelope["payload"],
                "signature": envelope["signature"],
                "verified": True,
            }
        )

        audit.record(
            repository,
            entity_type="appeal",
            entity_id=appeal["id"],
            action="appeal.submitted",
            actor_agent_id=APPEALS_AGENT_ID,
            after_state={
                "auth_request_id": auth_request_id,
                "confidence": confidence,
                "threshold": threshold,
                "message_id": envelope["message_id"],
                "status": "submitted",
                "letter_source": letter_source,
            },
        )

        return {
            "appeal": appeal,
            "category": category,
            "reviewer_notes": None,
            "citations": citations,
            "letter_source": letter_source,
            "pubmed_error": pubmed_error,
            "envelope": envelope,
        }

    # Below threshold: a human reads it before anything reaches the payer.
    reviewer_notes = _reviewer_notes(
        reason=(
            f"Appeal confidence {confidence:.2f} is below the {threshold:.2f} "
            "submission threshold."
        ),
        auth_request=auth_request,
        category=category,
        denial_reason_code=denial_reason_code,
        confidence=confidence,
        citations=citations,
    )

    repository.update_auth_request(auth_request_id, {"status": "appealed"})

    audit.record(
        repository,
        entity_type="appeal",
        entity_id=appeal["id"],
        action="appeal.escalated",
        actor_agent_id=APPEALS_AGENT_ID,
        after_state={
            "auth_request_id": auth_request_id,
            "reason": "below_confidence_threshold",
            "confidence": confidence,
            "threshold": threshold,
            "status": "escalated",
            "letter_source": letter_source,
        },
    )

    return {
        "appeal": appeal,
        "category": category,
        "reviewer_notes": reviewer_notes,
        "citations": citations,
        "letter_source": letter_source,
        "pubmed_error": pubmed_error,
    }
