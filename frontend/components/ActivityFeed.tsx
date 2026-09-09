import { formatTime, shortId } from "@/lib/display";
import type { AriaMessageRecord } from "@/lib/types";

const PAYLOAD_STYLES: Record<string, string> = {
  AUTH_REQUEST: "bg-electric-100 text-electric-600",
  AUTH_RESPONSE: "bg-emerald-50 text-emerald-800",
  APPEAL: "bg-amber-50 text-amber-800",
};

export function ActivityFeed({
  messages,
}: {
  messages: AriaMessageRecord[];
}) {
  return (
    <aside className="pavo-card p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">Live ARIA feed</h2>
        <span
          className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse-ring"
          aria-hidden
        />
      </div>
      <p className="mt-0.5 text-xs text-navy-400">Last {messages.length} messages</p>

      {messages.length === 0 ? (
        <p className="mt-4 text-xs text-navy-400">
          No traffic yet. Submit a request to see messages arrive.
        </p>
      ) : (
        <ol className="mt-3 space-y-2.5">
          {messages.map((message) => (
            <li
              key={message.id}
              className="animate-fade-up border-l-2 border-electric-400 pl-3"
            >
              <div className="flex flex-wrap items-center gap-1.5">
                <span
                  className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                    PAYLOAD_STYLES[message.payload_type ?? ""] ??
                    "bg-slate-100 text-navy-600"
                  }`}
                >
                  {message.payload_type}
                </span>
                <span className="text-[11px] tabular-nums text-navy-400">
                  {formatTime(message.created_at)}
                </span>
                {message.verified ? (
                  <span className="text-[11px] text-emerald-700">verified</span>
                ) : (
                  <span className="text-[11px] text-rose-700">unverified</span>
                )}
              </div>
              <p className="mt-0.5 truncate text-[11px] text-navy-400">
                request {shortId(message.auth_request_id)}
              </p>
            </li>
          ))}
        </ol>
      )}
    </aside>
  );
}
