import Link from "next/link";

import { StatusBadge } from "@/components/StatusBadge";
import type { AuthRequestRecord } from "@/lib/types";

function formatTimestamp(value: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "—" : parsed.toLocaleString();
}

export function RequestsTable({ requests }: { requests: AuthRequestRecord[] }) {
  if (requests.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
        <p className="text-sm font-medium">No authorization requests yet</p>
        <p className="mt-1 text-sm text-slate-600">
          Submit one above to watch it move through the agents.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
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
              <td className="px-4 py-3 font-mono text-xs text-slate-600">
                {request.decision_rule_id ?? "—"}
              </td>
              <td className="px-4 py-3 text-xs text-slate-600">
                {request.confidence === null
                  ? "—"
                  : `${Math.round(request.confidence * 100)}%`}
              </td>
              <td className="px-4 py-3 text-xs text-slate-600">
                {formatTimestamp(request.created_at)}
              </td>
              <td className="px-4 py-3 text-right">
                <Link
                  href={`/requests/${request.id}`}
                  className="text-xs font-medium text-slate-900 underline underline-offset-2 hover:text-slate-600"
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
