import type { Metadata } from "next";
import Link from "next/link";

import { Container } from "@/components/site/Container";
import { Prose } from "@/components/site/Prose";
import { Section } from "@/components/site/Section";
import { SectionHeading } from "@/components/site/SectionHeading";
import { NOT_YET, WORKING_NOW } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "About — Pavo Cloud",
  description:
    "Why prior authorization is broken, why the answer is signed agents and cryptography rather than a language model, and what is built today versus later.",
};

const ROADMAP = [
  {
    horizon: "Built",
    title: "The authorization loop",
    body: "Signed agent-to-agent messaging, a deterministic rule engine, zero-knowledge proofs over patient criteria, autonomous appeals, and an append-only audit trail.",
  },
  {
    horizon: "Next",
    title: "Real pricing, real registries",
    body: "Replace the deterministic price generator with facility rates gathered by the voice agent, and turn NPI verification from a flag into a lookup against the live CMS registry.",
  },
  {
    horizon: "Later",
    title: "A circuit that hides the set",
    body: "A Merkle circuit, so a proof shows the diagnosis is one of a payer's covered conditions without revealing which one, plus a real multi-party trusted setup.",
  },
  {
    horizon: "Later",
    title: "Federated learning",
    body: "Described in the specification and not built. Payers would improve a shared model of what escalates without raw records leaving any payer's node.",
  },
];

export default function AboutPage() {
  return (
    <>
      <Container className="py-16 sm:py-20">
        <p className="text-sm font-medium uppercase tracking-wide text-electric-600">
          About the project
        </p>
        <h1 className="mt-3 max-w-3xl text-4xl font-semibold tracking-tight">
          Prior authorization is a protocol problem wearing a paperwork costume.
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-navy-600">
          Pavo Cloud was built for the AI2O finals as a working system rather
          than a pitch — every claim on this site can be traced to code in the
          repository or to a measured run.
        </p>
      </Container>

      {/* The thesis -------------------------------------------------------- */}
      <Section tone="panel">
        <SectionHeading
          eyebrow="The thesis"
          title="The data already exists. The two sides just cannot talk."
        />
        <Prose className="mt-6">
          <p>
            When a physician orders an MRI, the clinical record already contains
            every fact the payer will ask for. The delay does not come from
            missing information. It comes from the absence of a channel: the
            provider&apos;s system and the payer&apos;s system have no way to
            exchange a question and an answer, so a human transcribes one into a
            fax and another transcribes it back out.
          </p>
          <p>
            Three to fourteen days and $35 billion a year go into that
            transcription. For the cases that are clear-cut — and most are — no
            judgement is being exercised at any point in the chain.
          </p>
          <p>
            So the problem is not that the decision is hard. It is that there is
            no protocol. Build the channel, make both ends prove who they are,
            and the clear cases settle themselves.
          </p>
        </Prose>
      </Section>

      {/* Why not an LLM ---------------------------------------------------- */}
      <Section>
        <SectionHeading
          eyebrow="The approach"
          title="Why this is not a language model deciding coverage."
        />
        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          <div className="pavo-card p-5">
            <h3 className="text-sm font-semibold">Decisions are rules</h3>
            <p className="mt-2 text-sm leading-relaxed text-navy-600">
              Coverage is a contract. A model that is right 95% of the time is
              not acceptable when the other 5% is someone&apos;s surgery, and it
              cannot tell you which rule it applied. Pavo&apos;s engine cannot
              return an outcome without naming one.
            </p>
          </div>
          <div className="pavo-card p-5">
            <h3 className="text-sm font-semibold">Identity is cryptographic</h3>
            <p className="mt-2 text-sm leading-relaxed text-navy-600">
              Two organizations that have never met need more than a shared API
              key. Every message is signed, and an unverified one is rejected
              before its payload is read.
            </p>
          </div>
          <div className="pavo-card p-5">
            <h3 className="text-sm font-semibold">
              Privacy is structural
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-navy-600">
              Rather than sending the chart and promising to be careful with it,
              the provider proves the criteria hold and sends nothing else.
            </p>
          </div>
        </div>
        <Prose className="mt-8">
          <p>
            Models do the work models are good at — reading an insurance card,
            mapping a plain-language procedure to a CPT code, drafting an appeal
            letter from the clinical record. None of them decides whether a
            patient is covered.
          </p>
        </Prose>
      </Section>

      {/* Where it stands ---------------------------------------------------- */}
      <Section tone="panel">
        <SectionHeading
          eyebrow="Where it stands"
          title="Built, next, later."
          lede="Stated at the level of detail a reviewer would want, including the parts that are not done."
        />
        <div className="mt-10 space-y-6">
          {ROADMAP.map((item) => (
            <div
              key={item.title}
              className="grid gap-2 border-t border-slate-200 pt-6 sm:grid-cols-[7rem_1fr] sm:gap-6"
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-navy-400">
                {item.horizon}
              </p>
              <div>
                <h3 className="text-sm font-semibold">{item.title}</h3>
                <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-navy-600">
                  {item.body}
                </p>
              </div>
            </div>
          ))}
        </div>
        <p className="mt-8 text-sm leading-relaxed text-navy-600">
          {WORKING_NOW.length} subsystems run today; {NOT_YET.length} known
          limitations are listed in full on the{" "}
          <Link href="/" className="text-electric-600 underline">
            home page
          </Link>{" "}
          and in the repository README.
        </p>
      </Section>

      {/* Close -------------------------------------------------------------- */}
      <Section>
        <div className="max-w-2xl">
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            The fastest way to judge it is to run it.
          </h2>
          <p className="mt-3 text-base leading-relaxed text-navy-600">
            The demo executes against the same agents, rules, signatures and
            circuit as everything else here. Nothing on that page is a
            recording.
          </p>
          <div className="flex flex-wrap gap-3 pt-6">
            <Link href="/demo" className="pavo-btn">
              Run the demo
            </Link>
            <Link href="/how-it-works" className="pavo-btn-quiet">
              How it works
            </Link>
          </div>
        </div>
      </Section>
    </>
  );
}
