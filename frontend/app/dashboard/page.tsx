"use client";

import { useCallback, useEffect, useState } from "react";

import { NewRequestForm } from "@/components/NewRequestForm";
import { RequestsTable } from "@/components/RequestsTable";
import { listAuthRequests } from "@/lib/api";
import type { AuthRequestRecord } from "@/lib/types";

// The table polls so decisions from other agents appear without a reload.
const POLL_INTERVAL_MS = 5000;

export default function DashboardPage() {
  const [requests, setRequests] = useState<AuthRequestRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setRequests(await listAuthRequests());
      setError(null);
    } catch {
      setError(
        "Could not reach the Pavo Cloud API. Start the backend with: uvicorn app.main:app --reload --port 8000"
      );
    } finally {
      setLoaded(true);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = setInterval(() => void refresh(), POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [refresh]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Authorization requests</h1>
        <p className="mt-1 text-sm text-slate-600">
          Every decision below records the rule that produced it.
        </p>
      </div>

      <NewRequestForm onSubmitted={refresh} />

      {error ? (
        <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p>
      ) : null}

      {loaded ? (
        <RequestsTable requests={requests} />
      ) : (
        <p className="text-sm text-slate-500">Loading requests…</p>
      )}
    </div>
  );
}
