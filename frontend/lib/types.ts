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
  appeals: AppealRecord[];
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

// ----------------------------------------------------------------- Insure

export interface InsurancePlan {
  plan_name: string | null;
  insurance_company: string | null;
  group_number: string | null;
  member_id: string | null;
  network_name: string | null;
  deductible_individual: number | string | null;
  deductible_family: number | string | null;
  deductible_met: number | string | null;
  out_of_pocket_max_individual: number | string | null;
  out_of_pocket_max_family: number | string | null;
  primary_care_copay: number | string | null;
  specialist_copay: number | string | null;
  er_copay: number | string | null;
  coinsurance_percentage: number | string | null;
  covered_services: string[] | null;
  prior_auth_required_for: string[] | null;
}

/** Which parser produced each half of the plan: Claude, or labelled samples. */
export interface ParserSources {
  card: "claude" | "sample";
  eoc: "claude" | "sample";
}

export interface ParsedDocumentResult {
  document_id: string;
  member_id: string;
  insurance_plan: InsurancePlan;
  sources: ParserSources;
  card_image_url: string;
  eoc_url: string;
}

export interface CostBreakdown {
  rule: "deductible_met" | "deductible_not_met";
  formula: string;
  calculation: string;
  insurance_cost: number;
  cash_cost: number;
  coinsurance_rate: number;
  deductible_met: boolean;
  negotiated_rate: number;
}

export interface RankedFacility {
  facility_id: string;
  name: string;
  type: string;
  city: string;
  negotiated_rate: number;
  cash_price: number;
  cash_discount_percentage: number;
  quality_score: number;
  distance_miles: number;
  you_pay: number;
  payment_method: "cash" | "insurance";
  cheaper_option: "cash" | "insurance";
  savings_vs_alternative: number;
  breakdown: CostBreakdown;
  rank: number;
}

export interface PriceQueryResult {
  query_id: string;
  cpt_code: string;
  procedure_name: string;
  requested_procedure: string;
  cpt_source: "claude" | "sample";
  deductible_met: boolean | null;
  results: RankedFacility[];
}

// ---------------------------------------------------------------- Appeals

export type AppealStatus = "draft" | "submitted" | "won" | "lost" | "escalated";

export type DenialCategory =
  | "medical_necessity"
  | "not_covered"
  | "missing_info"
  | "other";

export interface PubMedCitation {
  pmid: string | null;
  title: string | null;
  authors: string[];
  journal: string | null;
  year: string | null;
  abstract: string | null;
  url: string | null;
}

export interface AppealRecord {
  id: string;
  auth_request_id: string | null;
  denial_reason_code: string | null;
  denial_reason_category: DenialCategory | null;
  appeal_letter: string | null;
  pubmed_citations: PubMedCitation[];
  confidence: number | null;
  status: AppealStatus | null;
  created_at: string | null;
  resolved_at: string | null;
}

export interface AppealResult {
  appeal: AppealRecord;
  denial_reason_category: DenialCategory;
  citations: PubMedCitation[];
  letter_source: "claude" | "sample" | "skipped";
  pubmed_error: string | null;
  reviewer_notes: string | null;
  decision?: Decision;
  response_message_id?: string;
  request: AuthRequestRecord;
}

export interface AppealStats {
  total: number;
  counts: Record<AppealStatus, number>;
  decided: number;
  win_rate: number | null;
}

// ------------------------------------------------- Zero-knowledge proofs

export interface ZkClaims {
  age_valid: boolean;
  diagnosis_valid: boolean;
  deductible_valid: boolean;
  min_age: string | null;
  deductible_required: boolean;
}

export interface ZkProofResult {
  proof_id: string;
  proof: Record<string, unknown>;
  public_signals: string[];
  proof_digest: string;
  claims: ZkClaims;
  criteria: Record<string, unknown>;
}

export interface ZkVerifyResult {
  verified: boolean;
  claims: ZkClaims;
  proof_digest: string;
}

export interface ZkStatus {
  available: boolean;
  circuit: string;
  protocol: string;
  curve: string;
}

// ------------------------------------------------------------ System

export interface SystemStats {
  authorizations_processed: number;
  requests_by_status: Record<string, number>;
  average_resolution_seconds: number | null;
  appeals_total: number;
  appeals_decided: number;
  appeals_win_rate: number | null;
  zk_proofs_generated: number;
  aria_messages_exchanged: number;
  price_queries: number;
}
