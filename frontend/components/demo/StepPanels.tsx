"use client";

import { formatTime, shortId } from "@/lib/display";
import { formatCurrency } from "@/lib/format";
import type { DemoState } from "@/lib/demo";

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-2 py-1.5">
      <dt className="text-xs text-navy-400">{label}</dt>
      <dd className="text-sm font-medium">{value}</dd>
    </div>
  );
}

function Check({ ok, label }: { ok: boolean; label: string }) {
  return (
    <li className="flex items-start gap-2">
      <span
        className={`mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white ${
          ok ? "bg-emerald-500" : "bg-slate-400"
        }`}
        aria-hidden
      >
        {ok ? "✓" : "–"}
      </span>
      <span className="text-sm">{label}</span>
    </li>
  );
}

/** Step 1 — the ARIA envelope as it is constructed. */
export function EhrStep({ state }: { state: DemoState }) {
  const outbound = state.ariaMessages.find(
    (message) => message.payload_type === "AUTH_REQUEST"
  );

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="pavo-card p-5">
        <h3 className="text-sm font-semibold">Order received</h3>
        <dl className="mt-3 divide-y divide-slate-100">
          <Row label="Request" value={<span className="pavo-id">{shortId(state.request?.id)}</span>} />
          <Row label="Procedure (CPT)" value={state.request?.procedure_code ?? "—"} />
          <Row label="Diagnosis (ICD-10)" value={state.request?.diagnosis_code ?? "—"} />
          <Row
            label="Patient"
            value={<span className="pavo-id">hashed</span>}
          />
        </dl>
        <p className="mt-3 text-xs text-navy-400">
          The provider agent assembled a FHIR R4 bundle from the order. No
          member of staff touched this request.
        </p>
      </div>

      <div className="pavo-card overflow-hidden">
        <div className="border-b border-slate-200 px-4 py-2 text-xs font-medium text-navy-400">
          ARIA AUTH_REQUEST
        </div>
        <pre className="max-h-64 overflow-auto bg-navy-950 p-4 text-[11px] leading-relaxed text-electric-100">
{JSON.stringify(
  {
    aria_version: "1.0",
    message_id: outbound?.message_id ?? "…",
    payload_type: "AUTH_REQUEST",
    sender: { agent_id: outbound?.sender_agent_id ?? "…" },
    receiver: { agent_id: outbound?.receiver_agent_id ?? "…" },
    payload: {
      procedure_code: state.request?.procedure_code,
      diagnosis_code: state.request?.diagnosis_code,
      patient_id: state.request?.patient_id,
    },
    signature: outbound?.signature ?? "…",
  },
  null,
  2
)}
        </pre>
      </div>
    </div>
  );
}

/** Step 2 — signing and verification. */
export function IdentityStep({ state }: { state: DemoState }) {
  const messages = state.ariaMessages;
  const allVerified = messages.length > 0 && messages.every((m) => m.verified);

  return (
    <div className="space-y-4">
      <div className="pavo-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-semibold">Signature verification</h3>
          {allVerified ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-800 ring-1 ring-inset ring-emerald-200">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" aria-hidden />
              verified: true
            </span>
          ) : (
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-navy-400">
              awaiting messages
            </span>
          )}
        </div>

        <p className="mt-2 text-sm text-navy-600">
          Each organization holds an RSA-2048 key pair. Pavo stores only the
          public key — the private key never reaches the database. Every
          message is signed over a SHA-256 digest of its contents and checked
          against the sender&apos;s registered key before its payload is read.
        </p>

        <ul className="mt-4 space-y-3">
          {messages.map((message) => (
            <li
              key={message.id}
              className="rounded-md border border-slate-200 p-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-medium">
                  {message.payload_type}
                </span>
                <span
                  className={`text-xs font-medium ${
                    message.verified ? "text-emerald-700" : "text-rose-700"
                  }`}
                >
                  {message.verified ? "signature verified" : "unverified"}
                </span>
              </div>
              <p className="mt-1 break-all font-mono text-[11px] text-navy-400">
                {message.signature}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

/** Step 3 — the zero-knowledge proof, explained for a non-cryptographer. */
export function ZkStep({ state }: { state: DemoState }) {
  if (!state.zkAvailable) {
    return (
      <div className="pavo-card p-5">
        <p className="text-sm font-medium">Circuit artifacts are not built</p>
        <p className="mt-1 text-sm text-navy-600">
          Run <code className="font-mono text-xs">zk/build.sh</code> to compile
          the circuit and generate the proving key, then re-run this step.
        </p>
      </div>
    );
  }

  const claims = state.zk?.claims;
  const verified = state.zkVerification?.verified;

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="pavo-card p-5">
        <h3 className="text-sm font-semibold">What is being proven</h3>
        <p className="mt-2 text-sm text-navy-600">
          The payer needs to know three things about this patient. It does not
          need the underlying data to know them. The provider sends a
          mathematical proof instead of the chart.
        </p>

        <ul className="mt-4 space-y-2.5">
          <Check
            ok={Boolean(claims?.age_valid)}
            label={`Patient is at least ${claims?.min_age ?? 18} — the age itself is never sent`}
          />
          <Check
            ok={Boolean(claims?.diagnosis_valid)}
            label="Diagnosis matches the covered condition — the code is never sent"
          />
          <Check
            ok={Boolean(claims?.deductible_valid)}
            label="Deductible requirement is satisfied — no amount is ever sent"
          />
        </ul>

        <p className="mt-4 rounded-md bg-electric-100 px-3 py-2 text-xs text-navy-800">
          Patient criteria verified without revealing PHI. The payer learns
          only whether each criterion holds.
        </p>
      </div>

      <div className="pavo-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-semibold">The proof</h3>
          {verified === true ? (
            <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-800 ring-1 ring-inset ring-emerald-200">
              verified
            </span>
          ) : verified === false ? (
            <span className="rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-medium text-rose-800 ring-1 ring-inset ring-rose-200">
              rejected
            </span>
          ) : null}
        </div>

        <dl className="mt-3 divide-y divide-slate-100">
          <Row label="Protocol" value="groth16 · bn128" />
          <Row label="Proof" value={<span className="pavo-id">{shortId(state.zk?.proof_id)}</span>} />
        </dl>

        <p className="mt-3 text-xs text-navy-400">Proof digest</p>
        <p className="mt-1 break-all font-mono text-[11px] text-navy-600">
          {state.zk?.proof_digest ?? "—"}
        </p>

        <p className="mt-3 text-xs text-navy-400">
          Public signals (everything the payer receives)
        </p>
        <pre className="mt-1 overflow-auto rounded-md bg-navy-950 p-3 text-[11px] text-electric-100">
{JSON.stringify(state.zk?.public_signals ?? [], null, 2)}
        </pre>
      </div>
    </div>
  );
}

/** Step 4 — the deterministic rule that fired. */
export function RulesStep({ state }: { state: DemoState }) {
  return (
    <div className="pavo-card p-5">
      <h3 className="text-sm font-semibold">Deterministic rule engine</h3>
      <p className="mt-2 text-sm text-navy-600">
        The payer agent evaluates the FHIR bundle against published coverage
        rules. The first match wins, and the decision carries the rule that
        produced it.
      </p>

      <div className="mt-4 rounded-md border-2 border-electric-400 bg-electric-100 p-4 animate-pulse-ring">
        <p className="font-mono text-sm font-semibold text-electric-600">
          {state.decision?.rule_id ?? "—"}
        </p>
        <p className="mt-1 text-sm text-navy-800">
          {state.decision?.rule_description ?? "—"}
        </p>
      </div>

      <dl className="mt-4 divide-y divide-slate-100">
        <Row label="Outcome" value={state.decision?.outcome ?? "—"} />
        <Row
          label="Confidence"
          value={state.request?.confidence != null ? `${Math.round(state.request.confidence * 100)}%` : "—"}
        />
      </dl>
    </div>
  );
}

/** Step 5 — the decision and the audit trail behind it. */
export function DecisionStep({ state }: { state: DemoState }) {
  const approved = state.request?.status === "approved";

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="pavo-card p-5">
        <h3 className="text-sm font-semibold">Decision</h3>
        <p
          className={`mt-3 text-3xl font-semibold tracking-tight ${
            approved ? "text-emerald-600" : "text-amber-600"
          }`}
        >
          {(state.request?.status ?? "—").toUpperCase()}
        </p>
        <dl className="mt-3 divide-y divide-slate-100">
          <Row label="Deciding rule" value={<span className="font-mono text-xs">{state.request?.decision_rule_id ?? "—"}</span>} />
          <Row label="Resolved" value={formatTime(state.request?.resolved_at)} />
        </dl>
        <p className="mt-3 text-xs text-navy-400">
          {approved
            ? "Resolved automatically. No human was in the path."
            : "Routed to a human reviewer with the full record assembled."}
        </p>
      </div>

      <div className="pavo-card p-5">
        <h3 className="text-sm font-semibold">Audit trail</h3>
        <ol className="mt-3 space-y-2.5">
          {state.auditLog.map((entry) => (
            <li key={entry.id} className="border-l-2 border-electric-400 pl-3">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="font-mono text-xs font-medium">
                  {entry.action}
                </span>
                <span className="text-[11px] text-navy-400">
                  {formatTime(entry.created_at)}
                </span>
              </div>
              <p className="text-[11px] text-navy-400">{entry.actor_agent_id}</p>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}

/** Step 6 — the same procedure priced through Insure. */
export function InsureStep({ state }: { state: DemoState }) {
  const results = state.priceQuery?.results ?? [];

  return (
    <div className="space-y-4">
      <div className="pavo-card p-5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="text-sm font-semibold">
            {state.priceQuery?.procedure_name ?? "Pricing"}
          </h3>
          <p className="text-xs text-navy-400">
            CPT <span className="font-mono">{state.priceQuery?.cpt_code ?? "—"}</span>
            {" · "}deductible {state.priceQuery?.deductible_met ? "met" : "not met"}
          </p>
        </div>
        <p className="mt-2 text-sm text-navy-600">
          The same authorization now drives a price comparison for the member —
          what they would actually pay, at each facility, through insurance or
          in cash.
        </p>
      </div>

      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {results.slice(0, 3).map((facility) => (
          <li key={facility.facility_id} className="pavo-card p-4">
            <p className="text-xs text-navy-400">#{facility.rank}</p>
            <p className="mt-0.5 truncate text-sm font-semibold">
              {facility.name}
            </p>
            <p className="mt-2 text-2xl font-semibold tracking-tight">
              {formatCurrency(facility.you_pay)}
            </p>
            <p className="mt-1 text-xs text-navy-400">
              negotiated {formatCurrency(facility.negotiated_rate)} · cash{" "}
              {formatCurrency(facility.cash_price)}
            </p>
            <span
              className={`mt-2 inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium ${
                facility.cheaper_option === "cash"
                  ? "bg-emerald-50 text-emerald-800"
                  : "bg-electric-100 text-electric-600"
              }`}
            >
              {facility.cheaper_option === "cash" ? "cash cheaper" : "insurance cheaper"}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
