import Link from "next/link";
import { notFound } from "next/navigation";

import { JsonBlock } from "@/components/JsonBlock";
import { StatusBadge } from "@/components/StatusBadge";
import { ApiError, getAuthRequest } from "@/lib/api";
import type { AriaMessageRecord, AuditLogRecord } from "@/lib/types";

export const dynamic = "force-dynamic";

function formatTimestamp(value: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "—" : parsed.toLocaleString();
}

function AriaMessage({ message }: { message: AriaMessageRecord }) {
  const outbound = message.payload_type === "AUTH_REQUEST";

  return (
    <li className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span
            className={`rounded px-2 py-0.5 text-xs font-medium ${
              outbound
                ? "bg-sky-50 text-sky-800"
                : "bg-emerald-50 text-emerald-800"
            }`}
          >
            {message.payload_type}
          </span>
          <span className="text-xs text-slate-500">
            {message.sender_agent_id} → {message.receiver_agent_id}
          </span>
        </div>
        <span className="text-xs text-slate-500">
          {message.verified ? "Signature verified" : "Unverified"} ·{" "}
          {formatTimestamp(message.created_at)}
        </span>
      </div>

      <p className="mt-2 break-all font-mono text-xs text-slate-500">
        {message.signature}
      </p>

      <details className="mt-3">
        <summary className="cursor-pointer text-xs font-medium text-slate-700">
          Payload
        </summary>
        <div className="mt-2">
          <JsonBlock value={message.payload} />
        </div>
      </details>
    </li>
  );
}

function AuditEntry({ entry }: { entry: AuditLogRecord }) {
  const ruleId =
    (entry.after_state?.decision_rule_id as string | undefined) ??
    (entry.after_state?.rule_id as string | undefined);

  return (
    <li className="border-l-2 border-slate-200 py-3 pl-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="font-mono text-xs font-medium">{entry.action}</span>
        <span className="text-xs text-slate-500">
          {formatTimestamp(entry.created_at)}
        </span>
      </div>
      <p className="mt-1 text-xs text-slate-600">by {entry.actor_agent_id}</p>
      {ruleId ? (
        <p className="mt-1 text-xs">
          <span className="text-slate-500">rule</span>{" "}
          <span className="font-mono font-medium">{ruleId}</span>
        </p>
      ) : null}
      {entry.after_state ? (
        <details className="mt-2">
          <summary className="cursor-pointer text-xs text-slate-600">
            State change
          </summary>
          <div className="mt-2 grid gap-2 lg:grid-cols-2">
            <div>
              <p className="mb-1 text-xs text-slate-500">before</p>
              <JsonBlock value={entry.before_state} />
            </div>
            <div>
              <p className="mb-1 text-xs text-slate-500">after</p>
              <JsonBlock value={entry.after_state} />
            </div>
          </div>
        </details>
      ) : null}
    </li>
  );
}

export default async function RequestDetailPage({
  params,
}: {
  params: { id: string };
}) {
  let detail;

  try {
    detail = await getAuthRequest(params.id);
  } catch (caught) {
    if (caught instanceof ApiError && caught.status === 404) {
      notFound();
    }
    return (
      <div className="rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-800">
        Could not load this request. Is the backend running?
      </div>
    );
  }

  const { request, aria_messages: ariaMessages, audit_log: auditLog } = detail;

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/dashboard"
          className="text-sm text-slate-600 underline underline-offset-2 hover:text-slate-900"
        >
          ← All requests
        </Link>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">
            {request.procedure_code} · {request.diagnosis_code}
          </h1>
          <StatusBadge status={request.status} />
        </div>
        <p className="mt-1 font-mono text-xs text-slate-500">{request.id}</p>
      </div>

      <dl className="grid gap-4 rounded-lg border border-slate-200 bg-white p-5 sm:grid-cols-4">
        <div>
          <dt className="text-xs text-slate-500">Deciding rule</dt>
          <dd className="mt-1 font-mono text-sm">{request.decision_rule_id ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Confidence</dt>
          <dd className="mt-1 text-sm">
            {request.confidence === null
              ? "—"
              : `${Math.round(request.confidence * 100)}%`}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Submitted</dt>
          <dd className="mt-1 text-sm">{formatTimestamp(request.created_at)}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Resolved</dt>
          <dd className="mt-1 text-sm">{formatTimestamp(request.resolved_at)}</dd>
        </div>
      </dl>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          ARIA message thread
        </h2>
        <ul className="space-y-3">
          {ariaMessages.map((message) => (
            <AriaMessage key={message.id} message={message} />
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Audit trail
        </h2>
        <ul className="rounded-lg border border-slate-200 bg-white px-4 py-2">
          {auditLog.map((entry) => (
            <AuditEntry key={entry.id} entry={entry} />
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          FHIR R4 bundle
        </h2>
        <JsonBlock value={request.fhir_bundle} />
      </section>
    </div>
  );
}
