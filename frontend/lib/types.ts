export type RequestStatus =
  | "pending"
  | "approved"
  | "denied"
  | "escalated"
  | "appealed";

export interface AuthRequestRecord {
  id: string;
  provider_org_id: string | null;
  payer_org_id: string | null;
  patient_id: string | null;
  procedure_code: string | null;
  diagnosis_code: string | null;
  fhir_bundle: Record<string, unknown> | null;
  status: RequestStatus | null;
  decision_rule_id: string | null;
  confidence: number | null;
  created_at: string | null;
  resolved_at: string | null;
}

export interface AriaMessageRecord {
  id: string;
  message_id: string;
  auth_request_id: string | null;
  sender_agent_id: string | null;
  receiver_agent_id: string | null;
  payload_type: string | null;
  payload: Record<string, unknown>;
  signature: string | null;
  verified: boolean | null;
  created_at: string | null;
}

export interface AuditLogRecord {
  id: string;
  entity_type: string | null;
  entity_id: string | null;
  action: string | null;
  actor_agent_id: string | null;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  created_at: string | null;
}

export interface AuthRequestDetail {
  request: AuthRequestRecord;
  aria_messages: AriaMessageRecord[];
  audit_log: AuditLogRecord[];
}

export interface Decision {
  outcome: "APPROVED" | "DENIED" | "ESCALATED";
  rule_id: string;
  rule_description: string;
  confidence: number;
  is_definitive: boolean;
}

export interface SubmitResult {
  request: AuthRequestRecord;
  decision: Decision;
  aria: {
    request_message_id: string;
    response_message_id: string;
  };
}

export interface CoverageRule {
  rule_id: string;
  description: string;
  procedure_code: string;
  diagnosis_code: string;
  outcome: string;
}
