"use client";

import { useCallback, useEffect, useState } from "react";

import { ActivityFeed } from "@/components/ActivityFeed";
import { NewRequestForm } from "@/components/NewRequestForm";
import { RequestsTable } from "@/components/RequestsTable";
import { SystemStatsRow } from "@/components/SystemStatsRow";
import { getRecentActivity, getSystemStats, listAuthRequests } from "@/lib/api";
import type {
  AriaMessageRecord,
  AuthRequestRecord,
  SystemStats,
} from "@/lib/types";

// The backend is the source of truth for every counter, so the page polls
// rather than holding its own derived state.
const POLL_INTERVAL_MS = 10000;

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
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [activity, setActivity] = useState<AriaMessageRecord[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [filtered, systemStats, feed] = await Promise.all([
        listAuthRequests(status || undefined),
        getSystemStats(),
        getRecentActivity(10),
      ]);

      setRequests(filtered);
      setStats(systemStats);
      setActivity(feed);
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
        <p className="mt-1 text-sm text-navy-600">
          Every decision below records the rule that produced it. Counters
          refresh every 10 seconds.
        </p>
      </div>

      <SystemStatsRow stats={stats} />

      <NewRequestForm onSubmitted={refresh} />

      {error ? (
        <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">
          {error}
        </p>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]">
        <div>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className="text-xs text-navy-400">Filter:</span>
            {STATUS_FILTERS.map((filter) => (
              <button
                key={filter.value || "all"}
                type="button"
                onClick={() => setStatus(filter.value)}
                aria-pressed={status === filter.value}
                className={`rounded-full border px-2.5 py-1 text-xs transition ${
                  status === filter.value
                    ? "border-electric-600 bg-electric-600 text-white"
                    : "border-slate-300 text-navy-600 hover:border-electric-500"
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>

          {loaded ? (
            <RequestsTable requests={requests} />
          ) : (
            <p className="text-sm text-navy-400">Loading requests…</p>
          )}
        </div>

        <ActivityFeed messages={activity} />
      </div>
    </div>
  );
}
