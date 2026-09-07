import type { RequestStatus } from "@/lib/types";

const STYLES: Record<string, string> = {
  pending: "bg-slate-100 text-slate-700 ring-slate-200",
  approved: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  escalated: "bg-amber-50 text-amber-800 ring-amber-200",
  denied: "bg-rose-50 text-rose-700 ring-rose-200",
  appealed: "bg-violet-50 text-violet-700 ring-violet-200",
};

export function StatusBadge({ status }: { status: RequestStatus | string | null }) {
  const key = (status ?? "pending").toLowerCase();
  const className = STYLES[key] ?? STYLES.pending;

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ring-1 ring-inset ${className}`}
    >
      {key}
    </span>
  );
}
