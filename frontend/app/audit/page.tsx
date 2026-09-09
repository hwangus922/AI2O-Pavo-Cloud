"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { JsonDiff } from "@/components/JsonDiff";
import { ApiError, getFullAuditTrail } from "@/lib/api";
import { downloadCsv, toCsv } from "@/lib/csv";
import { formatTimestamp, shortId } from "@/lib/display";
import type { AuditLogRecord } from "@/lib/types";

const ENTITY_TYPES = [
  { value: "", label: "All" },
  { value: "auth_request", label: "Authorizations" },
  { value: "appeal", label: "Appeals" },
  { value: "price_query", label: "Price queries" },
  { value: "zk_proof", label: "ZK proofs" },
  { value: "insurance_document", label: "Documents" },
];

const ENTITY_STYLES: Record<string, string> = {
  auth_request: "bg-electric-100 text-electric-600",
  appeal: "bg-amber-50 text-amber-800",
  price_query: "bg-emerald-50 text-emerald-800",
  zk_proof: "bg-violet-50 text-violet-800",
  insurance_document: "bg-slate-100 text-navy-600",
};

export default function AuditPage() {
  const [entityType, setEntityType] = useState("");
  const [since, setSince] = useState("");
  const [until, setUntil] = useState("");

  const [entries, setEntries] = useState<AuditLogRecord[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setEntries(
        await getFullAuditTrail({
          entityType: entityType || undefined,
          since: since || undefined,
          // Include the whole end day rather than stopping at midnight.
          until: until ? `${until}T23:59:59` : undefined,
        })
      );
      setError(null);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not reach the Pavo Cloud API. Is the backend running?"
      );
    } finally {
      setLoading(false);
    }
  }, [entityType, since, until]);

  useEffect(() => {
    void load();
  }, [load]);

  const exportCsv = useMemo(
    () => () => {
      const csv = toCsv(
        [
          "timestamp",
          "entity_type",
          "entity_id",
          "action",
          "actor_agent_id",
          "before_state",
          "after_state",
        ],
        entries.map((entry) => [
          entry.created_at,
          entry.entity_type,
          entry.entity_id,
          entry.action,
          entry.actor_agent_id,
          entry.before_state,
          entry.after_state,
        ])
      );
      downloadCsv(
        `pavo-audit-${new Date().toISOString().slice(0, 10)}.csv`,
        csv
      );
    },
    [entries]
  );

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Audit trail</h1>
          <p className="mt-1 text-sm text-navy-600">
            Every event across the system, newest first. Nothing here is
            editable — the log is append-only.
          </p>
        </div>
        <button
          type="button"
          onClick={exportCsv}
          disabled={entries.length === 0}
          className="pavo-btn-quiet"
        >
          Export CSV
        </button>
      </header>

      {/* Filters */}
      <div className="pavo-card p-4 sm:p-5">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <span className="mb-1.5 block text-xs font-medium text-navy-600">
              Entity type
            </span>
            <div className="flex flex-wrap gap-2">
              {ENTITY_TYPES.map((option) => (
                <button
                  key={option.value || "all"}
                  type="button"
                  onClick={() => setEntityType(option.value)}
                  aria-pressed={entityType === option.value}
                  className={`rounded-full border px-2.5 py-1 text-xs transition ${
                    entityType === option.value
                      ? "border-electric-600 bg-electric-600 text-white"
                      : "border-slate-300 text-navy-600 hover:border-electric-500"
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <label className="block">
            <span className="mb-1 block text-xs font-medium text-navy-600">From</span>
            <input
              type="date"
              value={since}
              onChange={(event) => setSince(event.target.value)}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-electric-500 focus:outline-none"
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-xs font-medium text-navy-600">To</span>
            <input
              type="date"
              value={until}
              onChange={(event) => setUntil(event.target.value)}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-electric-500 focus:outline-none"
            />
          </label>

          {since || until ? (
            <button
              type="button"
              onClick={() => {
                setSince("");
                setUntil("");
              }}
              className="text-xs text-navy-400 underline underline-offset-2 hover:text-navy-800"
            >
              clear dates
            </button>
          ) : null}
        </div>
      </div>

      {error ? (
        <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p className="text-sm text-navy-400">Loading the trail…</p>
      ) : entries.length === 0 ? (
        <div className="pavo-card border-dashed p-8 text-center">
          <p className="text-sm font-medium">No matching events</p>
          <p className="mt-1 text-sm text-navy-600">
            Widen the filters, or run the demo to generate activity.
          </p>
        </div>
      ) : (
        <>
          <p className="text-xs text-navy-400">{entries.length} events</p>
          <ol className="space-y-2">
            {entries.map((entry) => {
              const open = expanded === entry.id;
              return (
                <li key={entry.id} className="pavo-card">
                  <button
                    type="button"
                    onClick={() => setExpanded(open ? null : entry.id)}
                    aria-expanded={open}
                    className="flex w-full flex-wrap items-center gap-x-4 gap-y-1.5 p-4 text-left"
                  >
                    <span className="text-xs tabular-nums text-navy-400">
                      {formatTimestamp(entry.created_at)}
                    </span>
                    <span
                      className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${
                        ENTITY_STYLES[entry.entity_type ?? ""] ??
                        "bg-slate-100 text-navy-600"
                      }`}
                    >
                      {entry.entity_type}
                    </span>
                    <span className="font-mono text-xs font-medium">
                      {entry.action}
                    </span>
                    <span className="pavo-id">{shortId(entry.entity_id)}</span>
                    <span className="ml-auto truncate text-[11px] text-navy-400">
                      {entry.actor_agent_id}
                    </span>
                  </button>

                  {open ? (
                    <div className="animate-fade-up border-t border-slate-100 p-4">
                      <JsonDiff
                        before={entry.before_state}
                        after={entry.after_state}
                      />
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ol>
        </>
      )}
    </div>
  );
}
