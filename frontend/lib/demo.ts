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

/** A tiny one-pixel PNG and a minimal PDF, so Insure has something to parse. */
const CARD_PNG_BASE64 =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";
const EOC_PDF_TEXT =
  "%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n";

function base64ToFile(base64: string, name: string, type: string): File {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new File([bytes], name, { type });
}

function textToFile(text: string, name: string, type: string): File {
  return new File([text], name, { type });
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
  const document = await parseInsuranceDocuments({
    cardImage: base64ToFile(CARD_PNG_BASE64, "card.png", "image/png"),
    eocPdf: textToFile(EOC_PDF_TEXT, "eoc.pdf", "application/pdf"),
  });

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
