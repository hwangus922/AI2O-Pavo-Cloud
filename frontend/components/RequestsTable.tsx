import Link from "next/link";

import { StatusBadge } from "@/components/StatusBadge";
import { APPEAL_NOTE, DENIAL_NOTE } from "@/lib/scenarios";
import type { AuthRequestRecord } from "@/lib/types";

function formatTimestamp(value: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "—" : parsed.toLocaleString();
}

/**
 * What an empty list means depends on which filter produced it.
 *
 * "Denied" in particular is empty by design and always will be, so the
 * generic "submit one above" message was actively misleading — it invited a
 * visitor to go looking for a state the engine cannot reach.
 */
const EMPTY_STATES: Record<string, { title: string; body: string }> = {
  "": {
    title: "No authorization requests yet",
    body: "Submit one above to watch it move through the agents.",
  },
  pending: {
    title: "Nothing pending",
    body: "Requests resolve in milliseconds, so this view is almost always empty.",
  },
  approved: {
    title: "No approvals yet",
    body: "Submit one of the approving scenarios above.",
  },
  escalated: {
    title: "No escalations yet",
    body: "Try the knee replacement with a non-matching diagnosis, or an unknown procedure.",
  },
  denied: { title: "No denials — by design", body: DENIAL_NOTE },
  appealed: { title: "No appeals yet", body: APPEAL_NOTE },
};

export function RequestsTable({
  requests,
  status = "",
}: {
  requests: AuthRequestRecord[];
  /** The active status filter, so the empty state can explain itself. */
  status?: string;
}) {
  if (requests.length === 0) {
    const empty = EMPTY_STATES[status] ?? EMPTY_STATES[""];
    return (
      <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
        <p className="text-sm font-medium">{empty.title}</p>
        <p className="mx-auto mt-1 max-w-md text-sm leading-relaxed text-navy-600">
          {empty.body}
        </p>
      </div>
    );
  }

  // `relative` matters: the visually-hidden "Detail" header is absolutely
  // positioned, and without a positioned ancestor it escapes this scroll
  // container and stretches the document instead of being clipped by it.
  return (
    <div className="relative overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-navy-400">
          <tr>
            <th scope="col" className="px-4 py-3 font-medium">Status</th>
            <th scope="col" className="px-4 py-3 font-medium">Procedure</th>
            <th scope="col" className="px-4 py-3 font-medium">Diagnosis</th>
            <th scope="col" className="px-4 py-3 font-medium">Rule</th>
            <th scope="col" className="px-4 py-3 font-medium">Confidence</th>
            <th scope="col" className="px-4 py-3 font-medium">Submitted</th>
            <th scope="col" className="px-4 py-3 font-medium sr-only">Detail</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {requests.map((request) => (
            <tr key={request.id} className="hover:bg-slate-50">
              <td className="px-4 py-3">
                <StatusBadge status={request.status} />
              </td>
              <td className="px-4 py-3 font-mono text-xs">{request.procedure_code}</td>
              <td className="px-4 py-3 font-mono text-xs">{request.diagnosis_code}</td>
              <td className="px-4 py-3 font-mono text-xs text-navy-600">
                {request.decision_rule_id ?? "—"}
              </td>
              <td className="px-4 py-3 text-xs text-navy-600">
                {request.confidence === null
                  ? "—"
                  : `${Math.round(request.confidence * 100)}%`}
              </td>
              <td className="px-4 py-3 text-xs text-navy-600">
                {formatTimestamp(request.created_at)}
              </td>
              <td className="px-4 py-3 text-right">
                <Link
                  href={`/requests/${request.id}`}
                  className="text-xs font-medium text-slate-900 underline underline-offset-2 hover:text-navy-600"
                >
                  View trail
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
