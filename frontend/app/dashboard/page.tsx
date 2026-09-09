"use client";

import { useCallback, useEffect, useState } from "react";

import { NewRequestForm } from "@/components/NewRequestForm";
import { RequestsTable } from "@/components/RequestsTable";
import { StatCards } from "@/components/StatCards";
import { getAppealStats, listAuthRequests } from "@/lib/api";
import type { AppealStats, AuthRequestRecord } from "@/lib/types";

// The table polls so decisions from other agents appear without a reload.
const POLL_INTERVAL_MS = 5000;

const STATUS_FILTERS = [
  { value: "", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "escalated", label: "Escalated" },
  { value: "denied", label: "Denied" },
  { value: "appealed", label: "Appealed" },
];

export default function DashboardPage() {
  const [requests, setRequests] = useState<AuthRequestRecord[]>([]);
  const [allRequests, setAllRequests] = useState<AuthRequestRecord[]>([]);
  const [appealStats, setAppealStats] = useState<AppealStats | null>(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    try {
      // The stat cards summarize everything, so they always read the full set.
      const [filtered, everything, stats] = await Promise.all([
        listAuthRequests(status || undefined),
        status ? listAuthRequests() : Promise.resolve(null),
        getAppealStats(),
      ]);

      setRequests(filtered);
      setAllRequests(everything ?? filtered);
      setAppealStats(stats);
      setError(null);
    } catch {
      setError(
        "Could not reach the Pavo Cloud API. Start the backend with: uvicorn app.main:app --reload --port 8000"
      );
    } finally {
      setLoaded(true);
    }
  }, [status]);

  useEffect(() => {
    void refresh();
    const timer = setInterval(() => void refresh(), POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [refresh]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Authorization requests
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Every decision below records the rule that produced it.
        </p>
      </div>

      <StatCards requests={allRequests} appealStats={appealStats} />

      <NewRequestForm onSubmitted={refresh} />

      {error ? (
        <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p>
      ) : null}

      <div>
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500">Filter:</span>
          {STATUS_FILTERS.map((filter) => (
            <button
              key={filter.value || "all"}
              type="button"
              onClick={() => setStatus(filter.value)}
              aria-pressed={status === filter.value}
              className={`rounded-full border px-2.5 py-1 text-xs transition ${
                status === filter.value
                  ? "border-slate-900 bg-slate-900 text-white"
                  : "border-slate-300 text-slate-700 hover:border-slate-900"
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>

        {loaded ? (
          <RequestsTable requests={requests} />
        ) : (
          <p className="text-sm text-slate-500">Loading requests…</p>
        )}
      </div>
    </div>
  );
}
