import Link from "next/link";

const STEPS = [
  {
    title: "EHR order fires a webhook",
    body: "A physician places an order. No staff member submits anything.",
  },
  {
    title: "Provider agent assembles FHIR",
    body: "Patient, condition and service request are built into an R4 bundle.",
  },
  {
    title: "ARIA carries the request",
    body: "A signed AUTH_REQUEST crosses the organizational boundary.",
  },
  {
    title: "Payer agent decides",
    body: "A deterministic rule engine returns an outcome and the rule behind it.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-12">
      <section className="space-y-4">
        <p className="text-sm font-medium uppercase tracking-wide text-slate-500">
          Phase 1 — Core loop
        </p>
        <h1 className="max-w-3xl text-4xl font-semibold tracking-tight">
          Prior authorization that resolves in minutes, not weeks.
        </h1>
        <p className="max-w-2xl text-base leading-relaxed text-slate-600">
          Provider and payer agents negotiate authorization directly over ARIA.
          Clear cases resolve automatically. Ambiguous ones escalate to a human
          with the full record already assembled.
        </p>
        <div className="pt-2">
          <Link
            href="/dashboard"
            className="inline-flex rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
          >
            Open the dashboard
          </Link>
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">
          How a request flows
        </h2>
        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, index) => (
            <li
              key={step.title}
              className="rounded-lg border border-slate-200 bg-white p-4"
            >
              <div className="mb-2 text-xs font-semibold text-slate-400">
                {String(index + 1).padStart(2, "0")}
              </div>
              <h3 className="mb-1 text-sm font-semibold">{step.title}</h3>
              <p className="text-sm leading-relaxed text-slate-600">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
