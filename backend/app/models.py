"""Pydantic request/response models for the Pavo Cloud API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# Statuses persisted on auth_requests. These match the CHECK constraint in
# supabase/migrations/0001_init.sql.
RequestStatus = Literal["pending", "approved", "denied", "escalated", "appealed"]

# Outcomes the rule engine can return.
Outcome = Literal["APPROVED", "DENIED", "ESCALATED"]

# ARIA payload types carried in the envelope.
PayloadType = Literal[
    "AUTH_REQUEST",
    "AUTH_RESPONSE",
    "APPEAL",
    "PRICE_QUERY",
    "PRICE_RESPONSE",
]


class AuthRequestCreate(BaseModel):
    """Body of the mock EHR webhook: POST /api/auth/request."""

    procedure_code: str = Field(
        ..., min_length=1, description="CPT procedure code, e.g. 70553"
    )
    diagnosis_code: str = Field(
        ..., min_length=1, description="ICD-10 diagnosis code, e.g. M17.11"
    )
    patient_id: Optional[str] = Field(
        default=None,
        description=(
            "Patient identifier. Hashed before storage — raw PHI is never persisted."
        ),
    )
    provider_org_id: Optional[str] = None
    payer_org_id: Optional[str] = None


class Decision(BaseModel):
    """Result of a rule-engine evaluation. Every decision carries its rule_id."""

    outcome: Outcome
    rule_id: str
    rule_description: str
    confidence: float
    is_definitive: bool = True

    @property
    def status(self) -> RequestStatus:
        """Map an engine outcome onto a persisted request status."""
        return {
            "APPROVED": "approved",
            "DENIED": "denied",
            "ESCALATED": "escalated",
        }[self.outcome]


class AriaMessage(BaseModel):
    """ARIA v1.0 envelope."""

    aria_version: str
    message_id: str
    timestamp: str
    sender: dict[str, Any]
    receiver: dict[str, Any]
    payload_type: PayloadType
    payload: dict[str, Any]
    signature: str


class AriaMessageRecord(BaseModel):
    """An ARIA message as stored, with its verification result."""

    id: str
    message_id: str
    auth_request_id: Optional[str] = None
    sender_agent_id: Optional[str] = None
    receiver_agent_id: Optional[str] = None
    payload_type: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    signature: Optional[str] = None
    verified: Optional[bool] = None
    created_at: Optional[datetime] = None


class AuditLogRecord(BaseModel):
    """One immutable audit-trail entry."""

    id: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    action: Optional[str] = None
    actor_agent_id: Optional[str] = None
    before_state: Optional[dict[str, Any]] = None
    after_state: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None


class AuthRequestRecord(BaseModel):
    """An authorization request row."""

    id: str
    provider_org_id: Optional[str] = None
    payer_org_id: Optional[str] = None
    patient_id: Optional[str] = None
    procedure_code: Optional[str] = None
    diagnosis_code: Optional[str] = None
    fhir_bundle: Optional[dict[str, Any]] = None
    status: Optional[str] = None
    decision_rule_id: Optional[str] = None
    confidence: Optional[float] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class AuthRequestDetail(BaseModel):
    """A request plus its full ARIA thread and audit trail."""

    request: AuthRequestRecord
    aria_messages: list[AriaMessageRecord] = Field(default_factory=list)
    audit_log: list[AuditLogRecord] = Field(default_factory=list)


class VerifyRequest(BaseModel):
    """Body of POST /api/aria/verify."""

    message: dict[str, Any]


class VerifyResponse(BaseModel):
    verified: bool
    message_id: Optional[str] = None
    reason: Optional[str] = None
