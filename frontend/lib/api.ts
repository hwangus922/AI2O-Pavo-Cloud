import type {
  AuthRequestDetail,
  AuthRequestRecord,
  CoverageRule,
  SubmitResult,
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

export function listAuthRequests(): Promise<AuthRequestRecord[]> {
  return request<AuthRequestRecord[]>("/api/auth");
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
