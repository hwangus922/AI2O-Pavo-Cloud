/**
 * A single measured figure.
 *
 * Extracted from SystemStatsRow so the dashboard's live counters and the
 * marketing pages' measured numbers cannot drift apart visually — there is one
 * definition of what a stat looks like.
 */
export function Stat({
  label,
  value,
  hint,
  invert = false,
}: {
  label: string;
  value: string;
  hint?: string;
  /** Set on a dark section, where the card and muted text have to flip. */
  invert?: boolean;
}) {
  return (
    <div
      className={
        invert
          ? "rounded-lg border border-navy-700 bg-navy-800 p-4"
          : "pavo-card p-4"
      }
    >
      <p className={invert ? "text-xs text-navy-200" : "text-xs text-navy-400"}>
        {label}
      </p>
      <p
        className={`mt-1 text-2xl font-semibold tracking-tight tabular-nums${
          invert ? " text-white" : ""
        }`}
      >
        {value}
      </p>
      {hint ? (
        <p
          className={
            invert ? "mt-0.5 text-xs text-navy-200" : "mt-0.5 text-xs text-navy-400"
          }
        >
          {hint}
        </p>
      ) : null}
    </div>
  );
}
