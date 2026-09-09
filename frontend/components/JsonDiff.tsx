/** Side-by-side before/after view of an audit entry's state. */

function pretty(value: unknown): string {
  if (value === null || value === undefined) return "—";
  return JSON.stringify(value, null, 2);
}

/** Keys present in either object, so an added field is still visible. */
function unionKeys(
  before: Record<string, unknown> | null,
  after: Record<string, unknown> | null
): string[] {
  return Array.from(
    new Set([...Object.keys(before ?? {}), ...Object.keys(after ?? {})])
  ).sort();
}

function changed(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) !== JSON.stringify(b);
}

export function JsonDiff({
  before,
  after,
}: {
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
}) {
  const keys = unionKeys(before, after);

  if (keys.length === 0) {
    return <p className="text-xs text-navy-400">No state was recorded.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[32rem] text-left text-xs">
        <thead className="text-navy-400">
          <tr>
            <th scope="col" className="py-1 pr-4 font-medium">Field</th>
            <th scope="col" className="py-1 pr-4 font-medium">Before</th>
            <th scope="col" className="py-1 font-medium">After</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 align-top">
          {keys.map((key) => {
            const from = before?.[key];
            const to = after?.[key];
            const isChanged = changed(from, to);

            return (
              <tr key={key} className={isChanged ? "bg-electric-100/40" : ""}>
                <td className="py-1.5 pr-4 font-mono font-medium">{key}</td>
                <td className="py-1.5 pr-4">
                  <pre className="whitespace-pre-wrap font-mono text-[11px] text-navy-600">
                    {pretty(from)}
                  </pre>
                </td>
                <td className="py-1.5">
                  <pre
                    className={`whitespace-pre-wrap font-mono text-[11px] ${
                      isChanged ? "font-semibold text-navy-900" : "text-navy-600"
                    }`}
                  >
                    {pretty(to)}
                  </pre>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
