"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  DecisionStep,
  EhrStep,
  IdentityStep,
  InsureStep,
  RulesStep,
  ZkProving,
  ZkStep,
} from "@/components/demo/StepPanels";
import {
  DEMO_STEPS,
  EMPTY_DEMO_STATE,
  refreshTrail,
  runEhrStep,
  runInsureStep,
  runZkStep,
  type DemoState,
} from "@/lib/demo";
import { Container } from "@/components/site/Container";
import { SCENARIOS } from "@/lib/scenarios";
import type { Scenario } from "@/lib/scenarios";

const DEFAULT_PROCEDURE = "27447";
const DEFAULT_DIAGNOSIS = "M17.11";
const DEFAULT_PATIENT_AGE = 42;

type Phase = "idle" | "running" | "done";

export default function DemoPage() {
  const [procedureCode, setProcedureCode] = useState(DEFAULT_PROCEDURE);
  const [diagnosisCode, setDiagnosisCode] = useState(DEFAULT_DIAGNOSIS);

  const [state, setState] = useState<DemoState>(EMPTY_DEMO_STATE);
  const [stepIndex, setStepIndex] = useState(-1);
  const [phase, setPhase] = useState<Phase>("idle");
  const [busy, setBusy] = useState(false);
  const [autoRun, setAutoRun] = useState(false);
  // True only while step 3 is waiting on a proof that has not landed yet.
  const [proving, setProving] = useState(false);
  const [elapsed, setElapsed] = useState<number | null>(null);

  // Which preset the current codes correspond to, if any. Typing a code by
  // hand simply deselects — the inputs stay authoritative.
  const selectedScenario = SCENARIOS.find(
    (scenario) =>
      scenario.procedure === procedureCode && scenario.diagnosis === diagnosisCode
  );

  function applyScenario(scenario: Scenario) {
    setProcedureCode(scenario.procedure);
    setDiagnosisCode(scenario.diagnosis);
  }

  // Guards against a timer firing after the component unmounts.
  const mounted = useRef(true);
  const startedAt = useRef<number>(0);

  /**
   * The zero-knowledge proof, started early.
   *
   * Every step does its work and only then reveals its panel, which means a
   * step's latency is spent with the *previous* step on screen. For five of
   * the six that is invisible — they cost milliseconds. The proof does not:
   * it is a groth16 prove over bn128, around a second on a developer machine
   * and far longer on a small shared instance. All of it was being spent
   * looking at the identity panel.
   *
   * Nothing about the proof depends on steps 2 or 3 having run: it needs only
   * the request that step 1 returns. So it starts the moment step 1 lands and
   * computes while identity and its dwell play out, and step 3 awaits a
   * promise that is usually already settled.
   */
  const zkProof = useRef<Promise<Partial<DemoState>> | null>(null);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  /**
   * A step that cannot complete simply stops the run.
   *
   * Whatever already succeeded stays on screen and the controls return to
   * rest, so pressing Run Full Demo again is the whole recovery. A backend
   * that was asleep is usually awake by the second press.
   */
  const stop = useCallback(() => {
    setProving(false);
    setPhase("idle");
    setAutoRun(false);
    setBusy(false);
  }, []);

  /** Run the work for one step, then reveal it. */
  const runStep = useCallback(
    async (index: number, current: DemoState): Promise<DemoState | null> => {
      setBusy(true);

      try {
        let patch: Partial<DemoState> = {};

        switch (DEMO_STEPS[index].id) {
          case "ehr": {
            patch = await runEhrStep(procedureCode.trim(), diagnosisCode.trim());
            const afterEhr = { ...current, ...patch };
            const pending = runZkStep(afterEhr, DEFAULT_PATIENT_AGE);
            // Keep a rejection from going unhandled in the gap before step 3
            // awaits it. The awaited promise still rejects, so a real failure
            // stops the run exactly as it did before.
            pending.catch(() => {});
            zkProof.current = pending;
            break;
          }
          case "zk": {
            // Stepping through by hand can reach this without step 1 having
            // started one.
            const pending =
              zkProof.current ?? runZkStep(current, DEFAULT_PATIENT_AGE);
            zkProof.current = null;
            // Reveal this step before awaiting, so a proof that outlasts its
            // head start is waited for on the zero-knowledge panel rather
            // than behind the identity one. When it has already landed the
            // await settles in a microtask and nothing flashes.
            setStepIndex(index);
            setProving(true);
            try {
              patch = await pending;
            } finally {
              if (mounted.current) setProving(false);
            }
            break;
          }
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
      } catch {
        if (mounted.current) stop();
        return null;
      }
    },
    [diagnosisCode, procedureCode, stop]
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
    setElapsed(null);
    setProving(false);
    zkProof.current = null;
    setPhase("running");
    setAutoRun(true);
    startedAt.current = Date.now();

    let current = EMPTY_DEMO_STATE;

    for (let index = 0; index < DEMO_STEPS.length; index += 1) {
      const result = await runStep(index, current);
      if (!result || !mounted.current) return;
      current = result;

      // Pacing lives with each step in lib/demo.ts, so a panel that renders
      // from data already fetched does not sit there for as long as one the
      // viewer is meant to read.
      const dwell = DEMO_STEPS[index].dwellMs;
      if (index < DEMO_STEPS.length - 1 && dwell > 0) {
        await new Promise((resolve) => setTimeout(resolve, dwell));
        if (!mounted.current) return;
      }
    }

    setElapsed((Date.now() - startedAt.current) / 1000);
    setPhase("done");
    setAutoRun(false);
  }, [runStep]);

  const activeStep = stepIndex >= 0 ? DEMO_STEPS[stepIndex] : null;

  return (
    <Container className="space-y-6 py-8 sm:py-10">
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
        {/* Every rule in the engine, reachable in one click. Typing a CPT code
          still works, but nobody should have to know one to see the system
          escalate rather than approve. */}
        <div className="mb-4">
          <p className="mb-2 text-xs font-medium text-navy-600">Scenario</p>
          <div className="flex flex-wrap gap-2">
            {SCENARIOS.map((scenario) => {
              const active = scenario === selectedScenario;
              return (
                <button
                  key={scenario.ruleId}
                  type="button"
                  disabled={autoRun || busy}
                  onClick={() => applyScenario(scenario)}
                  className={`rounded-full border px-2.5 py-1 text-xs transition disabled:cursor-not-allowed disabled:opacity-50 ${
                    active
                      ? "border-electric-600 bg-electric-600 text-white"
                      : "border-slate-300 text-navy-600 hover:border-navy-600"
                  }`}
                >
                  {scenario.label} — {scenario.outcome}
                </button>
              );
            })}
          </div>
          {selectedScenario ? (
            <p className="mt-2 max-w-2xl text-xs leading-relaxed text-navy-400">
              <span className="pavo-id">{selectedScenario.ruleId}</span>{" "}
              {selectedScenario.detail}
            </p>
          ) : null}
        </div>

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

      {/* Active panel */}
      {busy && stepIndex < 0 ? (
        <div className="pavo-card p-8 text-center">
          <p className="text-sm text-navy-400">Submitting the order…</p>
        </div>
      ) : null}

      {activeStep ? (
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
          {activeStep.id === "zk" ? (
            proving ? <ZkProving /> : <ZkStep state={state} />
          ) : null}
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
    </Container>
  );
}
