"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  DecisionStep,
  EhrStep,
  IdentityStep,
  InsureStep,
  RulesStep,
  ZkStep,
} from "@/components/demo/StepPanels";
import { ApiError } from "@/lib/api";
import {
  DEMO_STEPS,
  EMPTY_DEMO_STATE,
  refreshTrail,
  runEhrStep,
  runInsureStep,
  runZkStep,
  type DemoState,
} from "@/lib/demo";

// Auto-advance pacing. Six steps at 2s of dwell plus the work itself keeps
// the whole run comfortably inside the 30-second budget.
const AUTO_ADVANCE_MS = 2000;

const DEFAULT_PROCEDURE = "27447";
const DEFAULT_DIAGNOSIS = "M17.11";
const DEFAULT_PATIENT_AGE = 42;

type Phase = "idle" | "running" | "done" | "error";

export default function DemoPage() {
  const [procedureCode, setProcedureCode] = useState(DEFAULT_PROCEDURE);
  const [diagnosisCode, setDiagnosisCode] = useState(DEFAULT_DIAGNOSIS);

  const [state, setState] = useState<DemoState>(EMPTY_DEMO_STATE);
  const [stepIndex, setStepIndex] = useState(-1);
  const [phase, setPhase] = useState<Phase>("idle");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRun, setAutoRun] = useState(false);
  const [elapsed, setElapsed] = useState<number | null>(null);

  // Guards against a timer firing after the component unmounts.
  const mounted = useRef(true);
  const startedAt = useRef<number>(0);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const fail = useCallback((caught: unknown) => {
    setError(
      caught instanceof ApiError
        ? caught.message
        : "Could not reach the Pavo Cloud API. Is the backend running on port 8000?"
    );
    setPhase("error");
    setAutoRun(false);
    setBusy(false);
  }, []);

  /** Run the work for one step, then reveal it. */
  const runStep = useCallback(
    async (index: number, current: DemoState): Promise<DemoState | null> => {
      setBusy(true);
      setError(null);

      try {
        let patch: Partial<DemoState> = {};

        switch (DEMO_STEPS[index].id) {
          case "ehr":
            patch = await runEhrStep(procedureCode.trim(), diagnosisCode.trim());
            break;
          case "zk":
            patch = await runZkStep(current, DEFAULT_PATIENT_AGE);
            break;
          case "decision":
            patch = await refreshTrail(current);
            break;
          case "insure":
            patch = await runInsureStep(current);
            break;
          // Identity and rules read from what earlier steps already fetched.
          default:
            patch = {};
        }

        const next = { ...current, ...patch };
        if (!mounted.current) return null;

        setState(next);
        setStepIndex(index);
        setBusy(false);
        return next;
      } catch (caught) {
        if (mounted.current) fail(caught);
        return null;
      }
    },
    [diagnosisCode, fail, procedureCode]
  );

  /** Manual advance. */
  const next = useCallback(async () => {
    const index = stepIndex + 1;
    if (index >= DEMO_STEPS.length) return;
    await runStep(index, state);
    if (index === DEMO_STEPS.length - 1) setPhase("done");
  }, [runStep, state, stepIndex]);

  /** Full auto-advance run — no manual steps once this starts. */
  const runFullDemo = useCallback(async () => {
    setState(EMPTY_DEMO_STATE);
    setStepIndex(-1);
    setError(null);
    setElapsed(null);
    setPhase("running");
    setAutoRun(true);
    startedAt.current = Date.now();

    let current = EMPTY_DEMO_STATE;

    for (let index = 0; index < DEMO_STEPS.length; index += 1) {
      const result = await runStep(index, current);
      if (!result || !mounted.current) return;
      current = result;

      if (index < DEMO_STEPS.length - 1) {
        await new Promise((resolve) => setTimeout(resolve, AUTO_ADVANCE_MS));
        if (!mounted.current) return;
      }
    }

    setElapsed((Date.now() - startedAt.current) / 1000);
    setPhase("done");
    setAutoRun(false);
  }, [runStep]);

  const retry = useCallback(async () => {
    const index = Math.max(stepIndex + 1, 0);
    setPhase("running");
    await runStep(index, state);
  }, [runStep, state, stepIndex]);

  const activeStep = stepIndex >= 0 ? DEMO_STEPS[stepIndex] : null;

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium uppercase tracking-wide text-electric-600">
          End-to-end demo
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">
          One order, start to finish
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-navy-600">
          Every panel below is live data from the running system — the same
          agents, rules, signatures, and circuit the rest of the app uses.
        </p>
      </header>

      {/* Controls */}
      <div className="pavo-card p-4 sm:p-5">
        <div className="flex flex-wrap items-end gap-3">
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-navy-600">
              Procedure (CPT)
            </span>
            <input
              value={procedureCode}
              onChange={(event) => setProcedureCode(event.target.value)}
              disabled={autoRun || busy}
              className="w-32 rounded-md border border-slate-300 px-3 py-2 font-mono text-sm focus:border-electric-500 focus:outline-none"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-navy-600">
              Diagnosis (ICD-10)
            </span>
            <input
              value={diagnosisCode}
              onChange={(event) => setDiagnosisCode(event.target.value)}
              disabled={autoRun || busy}
              className="w-36 rounded-md border border-slate-300 px-3 py-2 font-mono text-sm focus:border-electric-500 focus:outline-none"
            />
          </label>

          <button
            type="button"
            onClick={runFullDemo}
            disabled={autoRun || busy}
            className="pavo-btn"
          >
            {autoRun ? "Running…" : "Run Full Demo"}
          </button>

          <button
            type="button"
            onClick={next}
            disabled={autoRun || busy || stepIndex >= DEMO_STEPS.length - 1}
            className="pavo-btn-quiet"
          >
            {stepIndex < 0 ? "Start" : "Next"}
          </button>

          {elapsed !== null ? (
            <span className="text-xs text-navy-400">
              completed in {elapsed.toFixed(1)}s
            </span>
          ) : null}
        </div>
      </div>

      {/* Step rail */}
      <ol className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        {DEMO_STEPS.map((step, index) => {
          const done = index < stepIndex;
          const active = index === stepIndex;
          return (
            <li
              key={step.id}
              className={`rounded-md border p-3 transition ${
                active
                  ? "border-electric-500 bg-electric-100"
                  : done
                    ? "border-slate-200 bg-white"
                    : "border-dashed border-slate-300 bg-white/60"
              }`}
            >
              <div className="flex items-center gap-1.5">
                <span
                  className={`inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold ${
                    done
                      ? "bg-emerald-500 text-white"
                      : active
                        ? "bg-electric-600 text-white"
                        : "bg-slate-200 text-navy-400"
                  }`}
                  aria-hidden
                >
                  {done ? "✓" : index + 1}
                </span>
                <span className="truncate text-xs font-medium">{step.title}</span>
              </div>
              <p className="mt-1 text-[11px] leading-snug text-navy-400">
                {step.blurb}
              </p>
            </li>
          );
        })}
      </ol>

      {/* Error with retry, rather than a broken panel */}
      {phase === "error" ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-5">
          <p className="text-sm font-semibold text-rose-900">
            This step did not complete
          </p>
          <p className="mt-1 text-sm text-rose-800">{error}</p>
          <button type="button" onClick={retry} className="pavo-btn mt-3">
            Retry this step
          </button>
        </div>
      ) : null}

      {/* Active panel */}
      {busy && stepIndex < 0 ? (
        <div className="pavo-card p-8 text-center">
          <p className="text-sm text-navy-400">Submitting the order…</p>
        </div>
      ) : null}

      {activeStep && phase !== "error" ? (
        <section key={activeStep.id} className="animate-fade-up space-y-3">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-navy-400">
              Step {stepIndex + 1} — {activeStep.title}
            </h2>
            {busy ? (
              <span className="text-xs text-navy-400">working…</span>
            ) : null}
          </div>

          {activeStep.id === "ehr" ? <EhrStep state={state} /> : null}
          {activeStep.id === "identity" ? <IdentityStep state={state} /> : null}
          {activeStep.id === "zk" ? <ZkStep state={state} /> : null}
          {activeStep.id === "rules" ? <RulesStep state={state} /> : null}
          {activeStep.id === "decision" ? <DecisionStep state={state} /> : null}
          {activeStep.id === "insure" ? <InsureStep state={state} /> : null}
        </section>
      ) : null}

      {stepIndex < 0 && phase === "idle" ? (
        <div className="pavo-card p-8 text-center">
          <p className="text-sm font-medium">Ready</p>
          <p className="mt-1 text-sm text-navy-600">
            Press Run Full Demo to watch an order travel from the EHR to a
            decision, a proof, and a price — with no manual steps.
          </p>
        </div>
      ) : null}
    </div>
  );
}
