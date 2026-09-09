import { formatDuration, formatPercent } from "@/lib/display";
import type { SystemStats } from "@/lib/types";

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
    <div className="pavo-card p-4">
      <p className="text-xs text-navy-400">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight tabular-nums">
        {value}
      </p>
      {hint ? <p className="mt-0.5 text-xs text-navy-400">{hint}</p> : null}
    </div>
  );
}

export function SystemStatsRow({ stats }: { stats: SystemStats | null }) {
  if (!stats) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, index) => (
          <div key={index} className="pavo-card p-4">
            <div className="h-3 w-20 animate-pulse rounded bg-slate-200" />
            <div className="mt-2 h-7 w-12 animate-pulse rounded bg-slate-200" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
      <Stat
        label="Authorizations processed"
        value={String(stats.authorizations_processed)}
        hint={`${stats.requests_by_status.approved ?? 0} auto-approved`}
      />
      <Stat
        label="Average resolution"
        value={formatDuration(stats.average_resolution_seconds)}
        hint="created to resolved"
      />
      <Stat
        label="Appeals win rate"
        value={formatPercent(stats.appeals_win_rate)}
        hint={
          stats.appeals_decided > 0
            ? `${stats.appeals_decided} decided`
            : "none decided yet"
        }
      />
      <Stat
        label="ZK proofs generated"
        value={String(stats.zk_proofs_generated)}
      />
      <Stat
        label="ARIA messages"
        value={String(stats.aria_messages_exchanged)}
        hint="signed and verified"
      />
    </div>
  );
}
