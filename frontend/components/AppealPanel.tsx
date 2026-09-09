"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError, generateAppeal } from "@/lib/api";
import type { AppealRecord, AppealResult, PubMedCitation } from "@/lib/types";

const DENIAL_REASONS = [
  { code: "MN-001", label: "Not medically necessary", category: "medical_necessity" },
  { code: "MI-001", label: "Missing clinical documentation", category: "missing_info" },
  { code: "NC-001", label: "Not covered under the plan", category: "not_covered" },
  { code: "ZZ-999", label: "Other / unclassified", category: "other" },
];

const CATEGORY_LABELS: Record<string, string> = {
  medical_necessity: "Medical necessity",
  not_covered: "Not covered",
  missing_info: "Missing information",
  other: "Other",
};

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-slate-100 text-slate-700 ring-slate-200",
  submitted: "bg-sky-50 text-sky-800 ring-sky-200",
  won: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  lost: "bg-rose-50 text-rose-800 ring-rose-200",
  escalated: "bg-amber-50 text-amber-800 ring-amber-200",
};

function AppealStatusBadge({ status }: { status: string | null }) {
  const key = status ?? "draft";
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ring-1 ring-inset ${
        STATUS_STYLES[key] ?? STATUS_STYLES.draft
      }`}
    >
      {key}
    </span>
  );
}

function Citations({ citations }: { citations: PubMedCitation[] }) {
  if (citations.length === 0) {
    return (
      <p className="text-xs text-navy-400">
        No supporting literature was retrieved for this appeal.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {citations.map((citation) => (
        <li key={citation.pmid} className="text-xs">
          <a
            href={citation.url ?? "#"}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-slate-900 underline underline-offset-2 hover:text-navy-600"
          >
            {citation.title ?? "Untitled"}
          </a>
          <p className="mt-0.5 text-navy-600">
            {(citation.authors ?? []).join(", ") || "Unknown authors"} ·{" "}
            {citation.journal ?? "Unknown journal"} ({citation.year ?? "n.d."}) · PMID{" "}
            {citation.pmid}
          </p>
          {citation.abstract ? (
            <details className="mt-1">
              <summary className="cursor-pointer text-navy-400">Abstract</summary>
              <p className="mt-1 whitespace-pre-wrap leading-relaxed text-slate-700">
                {citation.abstract}
              </p>
            </details>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

export function AppealDetail({
  appeal,
  reviewerNotes,
}: {
  appeal: AppealRecord;
  reviewerNotes?: string | null;
}) {
  const confidence = appeal.confidence ?? 0;
  const needsReview = appeal.status === "escalated";

  return (
    <div className="pavo-card p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold">Appeal</h3>
          <AppealStatusBadge status={appeal.status} />
        </div>
        <p className="text-xs text-navy-400">
          {CATEGORY_LABELS[appeal.denial_reason_category ?? "other"]} ·{" "}
          <span className="font-mono">{appeal.denial_reason_code}</span>
        </p>
      </div>

      {needsReview ? (
        <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm font-semibold text-amber-900">
            Requires human review
          </p>
          {reviewerNotes ? (
            <pre className="mt-2 whitespace-pre-wrap font-sans text-xs leading-relaxed text-amber-900">
              {reviewerNotes}
            </pre>
          ) : (
            <p className="mt-1 text-xs text-amber-900">
              This appeal was not submitted automatically. A reviewer decides next.
            </p>
          )}
        </div>
      ) : null}

      <dl className="mt-4 grid gap-4 border-t border-slate-100 pt-4 sm:grid-cols-3">
        <div>
          <dt className="text-xs text-navy-400">Confidence</dt>
          <dd className="mt-0.5 text-sm font-medium">
            {(confidence * 100).toFixed(0)}%
          </dd>
        </div>
        <div>
          <dt className="text-xs text-navy-400">Citations</dt>
          <dd className="mt-0.5 text-sm">{appeal.pubmed_citations?.length ?? 0}</dd>
        </div>
        <div>
          <dt className="text-xs text-navy-400">Resolved</dt>
          <dd className="mt-0.5 text-sm">
            {appeal.resolved_at
              ? new Date(appeal.resolved_at).toLocaleString()
              : "—"}
          </dd>
        </div>
      </dl>

      {appeal.appeal_letter ? (
        <details className="mt-4 border-t border-slate-100 pt-4">
          <summary className="cursor-pointer text-xs font-medium text-slate-700">
            Appeal letter
          </summary>
          <pre className="mt-2 max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-slate-50 p-4 font-sans text-xs leading-relaxed">
            {appeal.appeal_letter}
          </pre>
        </details>
      ) : null}

      <div className="mt-4 border-t border-slate-100 pt-4">
        <p className="mb-2 text-xs font-medium text-slate-700">
          Supporting evidence
        </p>
        <Citations citations={appeal.pubmed_citations ?? []} />
      </div>
    </div>
  );
}

export function GenerateAppealForm({ requestId }: { requestId: string }) {
  const router = useRouter();
  const [reasonCode, setReasonCode] = useState(DENIAL_REASONS[0].code);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AppealResult | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);

    try {
      const generated = await generateAppeal(requestId, reasonCode);
      setResult(generated);
      // Pull the server's updated view of the request and its trail.
      router.refresh();
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not generate an appeal. Is the backend running?"
      );
    } finally {
      setPending(false);
    }
  }

  if (result) {
    return (
      <div className="space-y-4">
        {result.decision ? (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-sm">
            Payer decision: <strong>{result.decision.outcome}</strong> via{" "}
            <span className="font-mono">{result.decision.rule_id}</span>
          </p>
        ) : null}
        {result.pubmed_error ? (
          <p className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-900">
            Evidence lookup did not complete: {result.pubmed_error}
          </p>
        ) : null}
        <AppealDetail appeal={result.appeal} reviewerNotes={result.reviewer_notes} />
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="pavo-card p-5"
    >
      <h3 className="text-sm font-semibold">Generate an appeal</h3>
      <p className="mt-1 text-sm text-navy-600">
        The appeals agent classifies the denial, gathers clinical evidence, and
        drafts a letter. Coverage exclusions go straight to a human.
      </p>

      <div className="mt-4 flex flex-wrap items-end gap-3">
        <label className="block">
          <span className="mb-1 block text-xs font-medium text-slate-700">
            Denial reason
          </span>
          <select
            value={reasonCode}
            onChange={(event) => setReasonCode(event.target.value)}
            disabled={pending}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-electric-500 focus:outline-none"
          >
            {DENIAL_REASONS.map((reason) => (
              <option key={reason.code} value={reason.code}>
                {reason.code} — {reason.label}
              </option>
            ))}
          </select>
        </label>

        <button
          type="submit"
          disabled={pending}
          className="pavo-btn"
        >
          {pending ? "Drafting appeal…" : "Generate Appeal"}
        </button>
      </div>

      {error ? (
        <p className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">
          {error}
        </p>
      ) : null}
    </form>
  );
}
