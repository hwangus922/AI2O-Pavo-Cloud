import type { AppealRecord, AuditLogRecord, AuthRequestRecord } from "@/lib/types";

interface TimelineStep {
  key: string;
  label: string;
  detail: string;
  timestamp: string | null;
  tone: "neutral" | "good" | "warn" | "bad";
}

const TONE_STYLES: Record<TimelineStep["tone"], string> = {
  neutral: "bg-slate-300",
  good: "bg-emerald-500",
  warn: "bg-amber-500",
  bad: "bg-rose-500",
};

function findEntry(
  auditLog: AuditLogRecord[],
  action: string
): AuditLogRecord | undefined {
  return auditLog.find((entry) => entry.action === action);
}

/** Build the request → denial → appeal → resolution sequence from the record. */
function buildSteps(
  request: AuthRequestRecord,
  auditLog: AuditLogRecord[],
  appeals: AppealRecord[]
): TimelineStep[] {
  const steps: TimelineStep[] = [];

  const created = findEntry(auditLog, "auth_request.created");
  steps.push({
    key: "created",
    label: "Request submitted",
    detail: `${request.procedure_code} · ${request.diagnosis_code}`,
    timestamp: created?.created_at ?? request.created_at,
    tone: "neutral",
  });

  const decided = auditLog.filter((entry) => entry.action === "decision.rendered");
  const firstDecision = decided[0];
  if (firstDecision) {
    const outcome = String(firstDecision.after_state?.outcome ?? "").toUpperCase();
    steps.push({
      key: "decision",
      label: `Decision: ${outcome || "rendered"}`,
      detail: String(
        firstDecision.after_state?.rule_description ??
          firstDecision.after_state?.decision_rule_id ??
          ""
      ),
      timestamp: firstDecision.created_at,
      tone: outcome === "APPROVED" ? "good" : outcome === "DENIED" ? "bad" : "warn",
    });
  }

  const classified = findEntry(auditLog, "appeal.denial_classified");
  if (classified) {
    steps.push({
      key: "classified",
      label: "Denial classified",
      detail: String(classified.after_state?.denial_reason_category ?? ""),
      timestamp: classified.created_at,
      tone: "neutral",
    });
  }

  const evidence = findEntry(auditLog, "appeal.evidence_retrieved");
  if (evidence) {
    const count = Number(evidence.after_state?.citations ?? 0);
    steps.push({
      key: "evidence",
      label: "Evidence gathered",
      detail: `${count} PubMed citation${count === 1 ? "" : "s"}`,
      timestamp: evidence.created_at,
      tone: count > 0 ? "good" : "warn",
    });
  }

  for (const appeal of appeals) {
    const escalated = appeal.status === "escalated";
    steps.push({
      key: `appeal-${appeal.id}`,
      label: escalated ? "Appeal escalated to human" : "Appeal submitted",
      detail: `confidence ${(100 * (appeal.confidence ?? 0)).toFixed(0)}%`,
      timestamp: appeal.created_at,
      tone: escalated ? "warn" : "neutral",
    });

    if (appeal.status === "won" || appeal.status === "lost") {
      steps.push({
        key: `appeal-resolved-${appeal.id}`,
        label: `Appeal ${appeal.status}`,
        detail:
          appeal.status === "won"
            ? "Authorization approved on appeal"
            : "Not granted; routed to a human reviewer",
        timestamp: appeal.resolved_at,
        tone: appeal.status === "won" ? "good" : "warn",
      });
    }
  }

  // A decision rendered after the appeal is the final resolution.
  const lastDecision = decided[decided.length - 1];
  if (lastDecision && lastDecision !== firstDecision) {
    const outcome = String(lastDecision.after_state?.outcome ?? "").toUpperCase();
    steps.push({
      key: "resolution",
      label: `Resolution: ${outcome}`,
      detail: String(lastDecision.after_state?.rule_description ?? ""),
      timestamp: lastDecision.created_at,
      tone: outcome === "APPROVED" ? "good" : "warn",
    });
  }

  return steps;
}

export function RequestTimeline({
  request,
  auditLog,
  appeals,
}: {
  request: AuthRequestRecord;
  auditLog: AuditLogRecord[];
  appeals: AppealRecord[];
}) {
  const steps = buildSteps(request, auditLog, appeals);

  return (
    <ol className="relative space-y-5 border-l border-slate-200 pl-6">
      {steps.map((step) => (
        <li key={step.key} className="relative">
          <span
            className={`absolute -left-[1.83rem] top-1.5 h-2.5 w-2.5 rounded-full ring-4 ring-white ${
              TONE_STYLES[step.tone]
            }`}
            aria-hidden
          />
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p className="text-sm font-medium">{step.label}</p>
            <p className="text-xs text-slate-500">
              {step.timestamp ? new Date(step.timestamp).toLocaleString() : "—"}
            </p>
          </div>
          {step.detail ? (
            <p className="mt-0.5 text-xs text-slate-600">{step.detail}</p>
          ) : null}
        </li>
      ))}
    </ol>
  );
}
