import {
  generateZkProof,
  getAuthRequest,
  getZkStatus,
  parseInsuranceDocuments,
  submitAuthRequest,
  submitPriceQuery,
  verifyZkProof,
} from "@/lib/api";
import type {
  AriaMessageRecord,
  AuditLogRecord,
  AuthRequestRecord,
  PriceQueryResult,
  RankedFacility,
  ZkProofResult,
  ZkVerifyResult,
} from "@/lib/types";

/** Everything the demo accumulates as it runs. All of it comes from the API. */
export interface DemoState {
  request: AuthRequestRecord | null;
  decision: { outcome: string; rule_id: string; rule_description: string } | null;
  ariaMessages: AriaMessageRecord[];
  auditLog: AuditLogRecord[];
  zk: ZkProofResult | null;
  zkVerification: ZkVerifyResult | null;
  zkAvailable: boolean;
  priceQuery: PriceQueryResult | null;
  bestFacility: RankedFacility | null;
}

export const EMPTY_DEMO_STATE: DemoState = {
  request: null,
  decision: null,
  ariaMessages: [],
  auditLog: [],
  zk: null,
  zkVerification: null,
  zkAvailable: false,
  priceQuery: null,
  bestFacility: null,
};

export const DEMO_STEPS = [
  { id: "ehr", title: "EHR trigger", blurb: "A physician places an order." },
  {
    id: "identity",
    title: "Identity",
    blurb: "Both agents prove who they are.",
  },
  { id: "zk", title: "Zero-knowledge", blurb: "Criteria proven, PHI withheld." },
  { id: "rules", title: "Rule engine", blurb: "A deterministic rule decides." },
  { id: "decision", title: "Decision", blurb: "The outcome and its audit trail." },
  { id: "insure", title: "Insure", blurb: "What the patient would actually pay." },
] as const;

export type DemoStepId = (typeof DEMO_STEPS)[number]["id"];

/** The sample documents Insure parses during the demo.
 *
 *  They are real files served from /public/demo — a rendered insurance card
 *  and a one-page Evidence of Coverage — so the flow behaves the same whether
 *  Claude reads them or the sample parser stands in. */
const SAMPLE_CARD_URL = "/demo/sample-card.png";
const SAMPLE_EOC_URL = "/demo/sample-eoc.pdf";

async function fetchAsFile(url: string, name: string, type: string): Promise<File> {
  const response = await fetch(url, { cache: "force-cache" });
  if (!response.ok) {
    throw new Error(`Could not load the sample document ${name} (${response.status}).`);
  }
  return new File([await response.blob()], name, { type });
}

/** Step 1: submit the order and capture the decision the agents reached. */
export async function runEhrStep(
  procedureCode: string,
  diagnosisCode: string
): Promise<Partial<DemoState>> {
  const submitted = await submitAuthRequest({
    procedure_code: procedureCode,
    diagnosis_code: diagnosisCode,
  });

  const detail = await getAuthRequest(submitted.request.id);

  return {
    request: detail.request,
    decision: submitted.decision,
    ariaMessages: detail.aria_messages,
    auditLog: detail.audit_log,
  };
}

/** Step 3: prove the patient criteria, then verify the proof. */
export async function runZkStep(
  state: DemoState,
  patientAge: number
): Promise<Partial<DemoState>> {
  const status = await getZkStatus();
  if (!status.available) {
    return { zkAvailable: false };
  }

  const proof = await generateZkProof({
    auth_request_id: state.request?.id,
    patient_age: patientAge,
    diagnosis_code: state.request?.diagnosis_code ?? "",
    deductible_met: true,
  });

  const verification = await verifyZkProof({
    proof: proof.proof,
    public_signals: proof.public_signals,
    proof_id: proof.proof_id,
  });

  return { zk: proof, zkVerification: verification, zkAvailable: true };
}

/** Step 6: price the same procedure through Insure. */
export async function runInsureStep(
  state: DemoState
): Promise<Partial<DemoState>> {
  const [cardImage, eocPdf] = await Promise.all([
    fetchAsFile(SAMPLE_CARD_URL, "sample-card.png", "image/png"),
    fetchAsFile(SAMPLE_EOC_URL, "sample-eoc.pdf", "application/pdf"),
  ]);
  const document = await parseInsuranceDocuments({ cardImage, eocPdf });

  // The authorization already carries the CPT code, so pass it through
  // rather than having the mapper infer one from a description.
  const procedureCode = state.request?.procedure_code ?? "";
  const priceQuery = await submitPriceQuery({
    procedure_name: `CPT ${procedureCode}`,
    cpt_code: procedureCode,
    document_id: document.document_id,
  });

  return {
    priceQuery,
    bestFacility: priceQuery.results[0] ?? null,
  };
}

/** Refresh the audit trail so the decision step shows the full record. */
export async function refreshTrail(
  state: DemoState
): Promise<Partial<DemoState>> {
  if (!state.request) return {};
  const detail = await getAuthRequest(state.request.id);
  return {
    request: detail.request,
    ariaMessages: detail.aria_messages,
    auditLog: detail.audit_log,
  };
}
