import type {
  AppealResult,
  AppealStats,
  AriaMessageRecord,
  AuditLogRecord,
  AuthRequestDetail,
  AuthRequestRecord,
  CoverageRule,
  ParsedDocumentResult,
  PriceQueryResult,
  SubmitResult,
  SystemStats,
  ZkProofResult,
  ZkStatus,
  ZkVerifyResult,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/** Thrown when the backend answers with a non-2xx status. */
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      } else if (Array.isArray(body?.detail) && body.detail.length > 0) {
        // FastAPI validation errors arrive as a list.
        detail = body.detail
          .map((item: { msg?: string }) => item.msg ?? "Invalid input")
          .join("; ");
      }
    } catch {
      // Body was not JSON; keep the status-based message.
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

export function listAuthRequests(status?: string): Promise<AuthRequestRecord[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return request<AuthRequestRecord[]>(`/api/auth${query}`);
}

export function generateAppeal(
  requestId: string,
  denialReasonCode: string
): Promise<AppealResult> {
  return request<AppealResult>(`/api/auth/${requestId}/appeal`, {
    method: "POST",
    body: JSON.stringify({ denial_reason_code: denialReasonCode }),
  });
}

export function getAppealStats(): Promise<AppealStats> {
  return request<AppealStats>("/api/appeals/stats");
}

export function getAuthRequest(id: string): Promise<AuthRequestDetail> {
  return request<AuthRequestDetail>(`/api/auth/${id}`);
}

export function submitAuthRequest(body: {
  procedure_code: string;
  diagnosis_code: string;
  patient_id?: string;
}): Promise<SubmitResult> {
  return request<SubmitResult>("/api/auth/request", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function listRules(): Promise<CoverageRule[]> {
  return request<CoverageRule[]>("/api/rules");
}

/** Multipart upload. The browser sets its own Content-Type with the boundary,
 *  so this path must not set one. */
async function upload<T>(path: string, body: FormData): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body,
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Upload failed with status ${response.status}`;
    try {
      const parsed = await response.json();
      if (typeof parsed?.detail === "string") {
        detail = parsed.detail;
      } else if (Array.isArray(parsed?.detail) && parsed.detail.length > 0) {
        detail = parsed.detail
          .map((item: { msg?: string }) => item.msg ?? "Invalid input")
          .join("; ");
      }
    } catch {
      // Body was not JSON; keep the status-based message.
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

export function parseInsuranceDocuments(input: {
  cardImage: File;
  eocPdf: File;
  memberId?: string;
}): Promise<ParsedDocumentResult> {
  const body = new FormData();
  body.append("card_image", input.cardImage);
  body.append("eoc_pdf", input.eocPdf);
  if (input.memberId) {
    body.append("member_id", input.memberId);
  }
  return upload<ParsedDocumentResult>("/api/insure/parse", body);
}

export function submitPriceQuery(body: {
  procedure_name: string;
  document_id: string;
  /** Supply when the code is already known, so it is not inferred from text. */
  cpt_code?: string;
}): Promise<PriceQueryResult> {
  return request<PriceQueryResult>("/api/insure/query", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ------------------------------------------------- Zero-knowledge proofs

export function getZkStatus(): Promise<ZkStatus> {
  return request<ZkStatus>("/api/zk/status");
}

export function generateZkProof(body: {
  auth_request_id?: string;
  patient_age: number;
  diagnosis_code: string;
  deductible_met: boolean;
}): Promise<ZkProofResult> {
  return request<ZkProofResult>("/api/zk/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function verifyZkProof(body: {
  proof: Record<string, unknown>;
  public_signals: string[];
  proof_id?: string;
}): Promise<ZkVerifyResult> {
  return request<ZkVerifyResult>("/api/zk/verify", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ------------------------------------------------------------- System

export function getSystemStats(): Promise<SystemStats> {
  return request<SystemStats>("/api/system/stats");
}

export function getRecentActivity(limit = 10): Promise<AriaMessageRecord[]> {
  return request<AriaMessageRecord[]>(`/api/system/activity?limit=${limit}`);
}

export function getFullAuditTrail(filters: {
  entityType?: string;
  since?: string;
  until?: string;
} = {}): Promise<AuditLogRecord[]> {
  const params = new URLSearchParams();
  if (filters.entityType) params.set("entity_type", filters.entityType);
  if (filters.since) params.set("since", filters.since);
  if (filters.until) params.set("until", filters.until);

  const query = params.toString();
  return request<AuditLogRecord[]>(`/api/system/audit${query ? `?${query}` : ""}`);
}
