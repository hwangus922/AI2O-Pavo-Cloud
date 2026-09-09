"use client";

import { useState } from "react";

import { ApiError, submitAuthRequest } from "@/lib/api";
import type { SubmitResult } from "@/lib/types";

const EXAMPLES = [
  { label: "MRI brain — approves", procedure: "70553", diagnosis: "G43.909" },
  { label: "Knee replacement, matching Dx — approves", procedure: "27447", diagnosis: "M17.11" },
  { label: "Knee replacement, other Dx — escalates", procedure: "27447", diagnosis: "M17.12" },
  { label: "Office visit — approves", procedure: "99214", diagnosis: "Z00.00" },
  { label: "Unknown procedure — escalates", procedure: "12345", diagnosis: "Z00.00" },
];

export function NewRequestForm({ onSubmitted }: { onSubmitted: () => void }) {
  const [procedureCode, setProcedureCode] = useState("70553");
  const [diagnosisCode, setDiagnosisCode] = useState("G43.909");
  const [patientId, setPatientId] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SubmitResult | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setResult(null);

    try {
      const submitted = await submitAuthRequest({
        procedure_code: procedureCode.trim(),
        diagnosis_code: diagnosisCode.trim(),
        ...(patientId.trim() ? { patient_id: patientId.trim() } : {}),
      });
      setResult(submitted);
      onSubmitted();
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not reach the Pavo Cloud API. Is the backend running?"
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="pavo-card p-5">
      <h2 className="text-sm font-semibold">Submit an authorization request</h2>
      <p className="mt-1 text-sm text-navy-600">
        Stands in for the EHR webhook that fires when a physician places an order.
      </p>

      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-700">
              Procedure code (CPT)
            </span>
            <input
              value={procedureCode}
              onChange={(event) => setProcedureCode(event.target.value)}
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm focus:border-electric-500 focus:outline-none"
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-700">
              Diagnosis code (ICD-10)
            </span>
            <input
              value={diagnosisCode}
              onChange={(event) => setDiagnosisCode(event.target.value)}
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm focus:border-electric-500 focus:outline-none"
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-700">
              Patient ID <span className="text-slate-400">(hashed, optional)</span>
            </span>
            <input
              value={patientId}
              onChange={(event) => setPatientId(event.target.value)}
              placeholder="mrn-12345"
              className="w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm focus:border-electric-500 focus:outline-none"
            />
          </label>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-navy-400">Try:</span>
          {EXAMPLES.map((example) => (
            <button
              key={example.label}
              type="button"
              onClick={() => {
                setProcedureCode(example.procedure);
                setDiagnosisCode(example.diagnosis);
              }}
              className="rounded-full border border-slate-300 px-2.5 py-1 text-xs text-slate-700 hover:border-electric-500"
            >
              {example.label}
            </button>
          ))}
        </div>

        <button
          type="submit"
          disabled={pending}
          className="pavo-btn"
        >
          {pending ? "Submitting…" : "Submit request"}
        </button>
      </form>

      {error ? (
        <p className="mt-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">
          {error}
        </p>
      ) : null}

      {result ? (
        <div className="mt-4 rounded-md bg-slate-50 px-3 py-3 text-sm">
          <p className="font-medium">
            Decision: {result.decision.outcome} via {result.decision.rule_id}
          </p>
          <p className="mt-1 text-navy-600">{result.decision.rule_description}</p>
        </div>
      ) : null}
    </div>
  );
}
