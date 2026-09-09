import type { AppealStats, AuthRequestRecord } from "@/lib/types";

function Stat({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight">{value}</p>
      {hint ? <p className="mt-0.5 text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
}

export function StatCards({
  requests,
  appealStats,
}: {
  requests: AuthRequestRecord[];
  appealStats: AppealStats | null;
}) {
  const approved = requests.filter((r) => r.status === "approved").length;
  const escalated = requests.filter((r) => r.status === "escalated").length;

  // Null until an appeal has actually been decided, so an untested system
  // never shows a misleading 0%.
  const winRate =
    appealStats?.win_rate === null || appealStats?.win_rate === undefined
      ? "—"
      : `${Math.round(appealStats.win_rate * 100)}%`;

  const winRateHint =
    appealStats && appealStats.decided > 0
      ? `${appealStats.counts.won} won of ${appealStats.decided} decided`
      : "No appeals decided yet";

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Stat label="Total requests" value={String(requests.length)} />
      <Stat
        label="Auto-approved"
        value={String(approved)}
        hint={
          requests.length
            ? `${Math.round((approved / requests.length) * 100)}% of all requests`
            : undefined
        }
      />
      <Stat label="Awaiting review" value={String(escalated)} />
      <Stat label="Appeals win rate" value={winRate} hint={winRateHint} />
    </div>
  );
}
