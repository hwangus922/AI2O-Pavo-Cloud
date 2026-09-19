import Link from "next/link";

import { JsonBlock } from "@/components/JsonBlock";
import { Container } from "@/components/site/Container";
import { Section } from "@/components/site/Section";
import { SectionHeading } from "@/components/site/SectionHeading";
import { Stat } from "@/components/site/Stat";
import {
  COVERAGE_RULES,
  FLOW_STEPS,
  NOT_YET,
  WORKING_NOW,
  ZK_PUBLIC_SIGNALS,
} from "@/lib/site-content";

const OUTCOME_STYLES: Record<string, string> = {
  APPROVED: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  ESCALATED: "bg-amber-50 text-amber-800 ring-amber-200",
};

export default function HomePage() {
  return (
    <>
      {/* Hero ------------------------------------------------------------ */}
      <Container className="py-16 sm:py-24">
        <p className="text-sm font-medium uppercase tracking-wide text-electric-600">
          Autonomous healthcare authorization
        </p>
        <h1 className="mt-3 max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
          Prior authorization that resolves in minutes, not weeks.
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-navy-600">
          Provider and payer agents negotiate authorization directly over ARIA.
          Clear cases resolve automatically. Ambiguous ones escalate to a human
          with the full record already assembled.
        </p>
        <div className="flex flex-wrap gap-3 pt-6">
          <Link href="/demo" className="pavo-btn">
            Run the demo
          </Link>
          <Link href="/how-it-works" className="pavo-btn-quiet">
            How it works
          </Link>
        </div>

        <div className="mt-12 grid gap-4 sm:grid-cols-3">
          <Stat label="End to end" value="11s" hint="measured, order to price" />
          <Stat label="Median decision" value="46ms" hint="created to resolved" />
          <Stat
            label="Decisions with a rule ID"
            value="100%"
            hint="the engine cannot return one without"
          />
        </div>
      </Container>

      {/* The problem ----------------------------------------------------- */}
      <Section tone="panel">
        <SectionHeading
          eyebrow="The problem"
          title="A fax sits in a queue for two weeks while a patient waits."
          lede="Prior authorization is the friction tax on American healthcare. It runs on fax machines, phone trees and staff rekeying the same clinical data into a second system."
        />
        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          <div className="pavo-card p-5">
            <p className="text-3xl font-semibold tracking-tight">3–14 days</p>
            <p className="mt-2 text-sm leading-relaxed text-navy-600">
              The typical wait for a decision that, for a clear-cut case, needs
              no human judgement at all.
            </p>
          </div>
          <div className="pavo-card p-5">
            <p className="text-3xl font-semibold tracking-tight">$35B</p>
            <p className="mt-2 text-sm leading-relaxed text-navy-600">
              Spent every year on the administrative overhead of asking
              permission and answering the question.
            </p>
          </div>
          <div className="pavo-card p-5">
            <p className="text-3xl font-semibold tracking-tight">Two systems</p>
            <p className="mt-2 text-sm leading-relaxed text-navy-600">
              The clinical record already holds every fact the payer needs. It
              is re-entered by hand because the two sides cannot talk.
            </p>
          </div>
        </div>
      </Section>

      {/* How a request flows ---------------------------------------------- */}
      <Section>
        <SectionHeading
          eyebrow="How a request flows"
          title="Six steps, no human in the loop until one is needed."
          lede="Every step below is a real subsystem, not a diagram. The demo runs all six against the same agents, rules, signatures and circuit the rest of the app uses."
        />
        <ol className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FLOW_STEPS.map((step, index) => (
            <li key={step.title} className="pavo-card p-5">
              <div className="text-xs font-semibold text-electric-500">
                {String(index + 1).padStart(2, "0")}
              </div>
              <h3 className="mt-2 text-sm font-semibold">{step.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-navy-600">
                {step.body}
              </p>
            </li>
          ))}
        </ol>
        <div className="mt-8">
          <Link href="/demo" className="pavo-btn">
            Watch it run
          </Link>
        </div>
      </Section>

      {/* Zero-knowledge --------------------------------------------------- */}
      <Section tone="dark">
        <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
          <div>
            <SectionHeading
              invert
              eyebrow="Zero-knowledge"
              title="The payer learns whether you qualify. Not why."
              lede="A payer needs three facts about a patient. It does not need the chart to know them. The provider sends a mathematical proof instead."
            />
            <ul className="mt-8 space-y-4">
              {[
                ["Patient meets the age floor", "the age itself is never sent"],
                [
                  "Diagnosis matches the covered condition",
                  "the code is never sent",
                ],
                [
                  "Deductible requirement is satisfied",
                  "no amount is ever sent",
                ],
              ].map(([claim, caveat]) => (
                <li key={claim} className="flex gap-3">
                  <span
                    aria-hidden
                    className="mt-1.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-electric-400"
                  />
                  <p className="text-sm leading-relaxed text-navy-200">
                    <span className="font-medium text-white">{claim}</span> —{" "}
                    {caveat}
                  </p>
                </li>
              ))}
            </ul>
            <p className="mt-8 text-sm leading-relaxed text-navy-200">
              groth16 over bn128. The circuit artifacts are committed, so
              proving works out of the box — a proof returns in well under a
              second.
            </p>
          </div>
          <div>
            <p className="mb-3 text-xs font-medium uppercase tracking-wide text-navy-200">
              Public signals — everything the payer receives
            </p>
            <JsonBlock value={ZK_PUBLIC_SIGNALS} />
            <p className="mt-3 text-xs leading-relaxed text-navy-200">
              Three satisfied criteria, the age floor that was tested, the
              hashed condition, and a validity flag. The chart stays where it
              was.
            </p>
          </div>
        </div>
      </Section>

      {/* Deterministic rules ---------------------------------------------- */}
      <Section tone="panel">
        <SectionHeading
          eyebrow="Deterministic, not a black box"
          title="A model never decides coverage."
          lede="Rules are evaluated in order and the first match wins, so the specific knee rule is checked before the general one. Every decision records the rule that produced it, and the table is returned by the API at runtime."
        />
        <div className="mt-10 overflow-x-auto">
          <table className="w-full min-w-[34rem] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-navy-400">
                <th className="py-2 pr-4 font-medium">Rule</th>
                <th className="py-2 pr-4 font-medium">Procedure</th>
                <th className="py-2 pr-4 font-medium">Diagnosis</th>
                <th className="py-2 font-medium">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {COVERAGE_RULES.map((rule) => (
                <tr key={rule.id} className="border-b border-slate-200">
                  <td className="py-3 pr-4">
                    <span className="pavo-id">{rule.id}</span>
                  </td>
                  <td className="py-3 pr-4 text-navy-600">{rule.procedure}</td>
                  <td className="py-3 pr-4 text-navy-600">{rule.diagnosis}</td>
                  <td className="py-3">
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
                        OUTCOME_STYLES[rule.outcome]
                      }`}
                    >
                      {rule.outcome}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-6 max-w-2xl text-sm leading-relaxed text-navy-600">
          Two of the five escalate. That is the point: the system is built to
          hand over the cases it cannot settle, with the record already
          assembled, rather than to produce a confident answer to a question it
          was never equipped to decide.
        </p>
      </Section>

      {/* Insure ----------------------------------------------------------- */}
      <Section>
        <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
          <div>
            <SectionHeading
              eyebrow="Insure"
              title="The same authorization tells the patient what they will pay."
              lede="Upload an insurance card and an Evidence of Coverage, ask for a procedure in plain language, and get what you would actually pay at each facility nearby."
            />
            <p className="mt-6 max-w-2xl text-sm leading-relaxed text-navy-600">
              Cash prices run well below negotiated rates. Before a deductible
              is met, paying cash is frequently cheaper than using the
              insurance you already pay for — and nobody tells the member that.
            </p>
            <div className="mt-8">
              <Link href="/insure" className="pavo-btn-quiet">
                Try a price comparison
              </Link>
            </div>
          </div>
          <div className="pavo-card p-6">
            <p className="text-xs uppercase tracking-wide text-navy-400">
              Knee replacement · CPT 27447 · deductible not met
            </p>
            <p className="mt-4 text-sm font-semibold">
              Northgate Community Hospital
            </p>
            <p className="mt-1 text-3xl font-semibold tracking-tight tabular-nums">
              $5,296
            </p>
            <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-xs text-navy-400">Negotiated rate</dt>
                <dd className="tabular-nums text-navy-600">$26,482</dd>
              </div>
              <div>
                <dt className="text-xs text-navy-400">Cash price</dt>
                <dd className="tabular-nums text-navy-600">$7,176</dd>
              </div>
            </dl>
            <p className="mt-4 text-xs leading-relaxed text-navy-400">
              One of five facilities returned for this procedure.
            </p>
          </div>
        </div>
      </Section>

      {/* What's real ------------------------------------------------------ */}
      <Section tone="panel">
        <SectionHeading
          eyebrow="What's real today"
          title="A prototype that says which parts are prototype."
          lede="Everything below the fold on most demos is a claim. Here is the line between what runs and what does not, so you can judge the rest of this site knowing where it sits."
        />
        <div className="mt-10 grid gap-8 lg:grid-cols-2">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-navy-400">
              Running now
            </h3>
            <ul className="mt-4 space-y-3">
              {WORKING_NOW.map((item) => (
                <li key={item} className="flex gap-3">
                  <span
                    aria-hidden
                    className="mt-1.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500"
                  />
                  <p className="text-sm leading-relaxed text-navy-600">{item}</p>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-navy-400">
              Not yet
            </h3>
            <ul className="mt-4 space-y-4">
              {NOT_YET.map((item) => (
                <li key={item.title}>
                  <p className="text-sm font-medium">{item.title}</p>
                  <p className="mt-1 text-sm leading-relaxed text-navy-600">
                    {item.body}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Section>

      {/* Close ------------------------------------------------------------ */}
      <Section tone="dark">
        <div className="max-w-2xl">
          <h2 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
            Watch one order go start to finish.
          </h2>
          <p className="mt-3 text-base leading-relaxed text-navy-200">
            Six steps, live against the running system — signed messages, a real
            proof, a deterministic decision and the audit trail it wrote. About
            eleven seconds.
          </p>
          <div className="flex flex-wrap gap-3 pt-6">
            <Link href="/demo" className="pavo-btn">
              Run the demo
            </Link>
            <Link
              href="/audit"
              className="inline-flex items-center justify-center rounded-md border border-navy-700 px-3 py-1.5 text-sm font-medium text-navy-200 transition hover:border-navy-600 hover:text-white"
            >
              Read the audit trail
            </Link>
          </div>
        </div>
      </Section>
    </>
  );
}
