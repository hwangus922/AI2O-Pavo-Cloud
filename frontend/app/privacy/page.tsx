import type { Metadata } from "next";
import Link from "next/link";

import { JsonBlock } from "@/components/JsonBlock";
import { Container } from "@/components/site/Container";
import { Prose } from "@/components/site/Prose";
import { Section } from "@/components/site/Section";
import { SectionHeading } from "@/components/site/SectionHeading";
import {
  NOT_YET,
  OPERATING_CONSTRAINTS,
  ZK_PUBLIC_SIGNALS,
} from "@/lib/site-content";

export const metadata: Metadata = {
  title: "Privacy — Pavo Cloud",
  description:
    "Zero-knowledge proofs over patient criteria, SHA-256 hashed identifiers, and the operating constraints that hold in code rather than on paper.",
};

// The circuit's limitation is stated on this page rather than hidden; pull the
// two ZK entries out of the shared list so they sit next to the claim.
const ZK_CAVEATS = NOT_YET.filter(
  (item) =>
    item.title === "The ZK circuit is deliberately simplified" ||
    item.title === "The trusted setup is local",
);

export default function PrivacyPage() {
  return (
    <>
      <Container className="py-16 sm:py-20">
        <p className="text-sm font-medium uppercase tracking-wide text-electric-600">
          Privacy
        </p>
        <h1 className="mt-3 max-w-3xl text-4xl font-semibold tracking-tight">
          The cheapest way to protect a record is not to send it.
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-navy-600">
          Prior authorization normally works by handing the payer the chart and
          trusting them with it. Pavo answers the payer&apos;s question without
          the chart ever crossing the boundary.
        </p>
      </Container>

      {/* The circuit ------------------------------------------------------ */}
      <Section tone="dark">
        <div className="grid gap-12 lg:grid-cols-2 lg:items-start">
          <div>
            <SectionHeading
              invert
              eyebrow="The circuit"
              title="Three criteria, proven, none disclosed."
            />
            <div className="mt-8 space-y-5">
              {[
                [
                  "The patient meets the age floor",
                  "A comparison inside the circuit. The age itself is never transmitted.",
                ],
                [
                  "The diagnosis matches the covered condition",
                  "Checked against a hash. The code is never transmitted.",
                ],
                [
                  "The deductible requirement is satisfied",
                  "A threshold check. No amount is ever transmitted.",
                ],
              ].map(([claim, detail]) => (
                <div key={claim}>
                  <p className="text-sm font-medium text-white">{claim}</p>
                  <p className="mt-1 text-sm leading-relaxed text-navy-200">
                    {detail}
                  </p>
                </div>
              ))}
            </div>
            <p className="mt-8 text-sm leading-relaxed text-navy-200">
              groth16 over the bn128 curve, built with circom and snarkjs. The
              proving artifacts are committed to the repository, so a proof
              returns in well under a second with no setup step.
            </p>
          </div>
          <div>
            <p className="mb-3 text-xs font-medium uppercase tracking-wide text-navy-200">
              Public signals — the complete payload the payer receives
            </p>
            <JsonBlock value={ZK_PUBLIC_SIGNALS} />
            <p className="mt-3 text-xs leading-relaxed text-navy-200">
              Three satisfied criteria, the age floor that was tested, the
              hashed condition, and a validity flag. Everything else stays in
              the provider&apos;s system.
            </p>
          </div>
        </div>
      </Section>

      {/* Honest about the circuit ----------------------------------------- */}
      <Section tone="panel">
        <SectionHeading
          eyebrow="What this circuit does not do"
          title="Two limits worth stating before anyone asks."
          lede="A prototype that oversells its cryptography is worse than one that has none, because it invites the wrong kind of trust."
        />
        <div className="mt-8 grid gap-4 lg:grid-cols-2">
          {ZK_CAVEATS.map((item) => (
            <div key={item.title} className="pavo-card p-5">
              <h3 className="text-sm font-semibold">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-navy-600">
                {item.body}
              </p>
            </div>
          ))}
        </div>
      </Section>

      {/* Operating constraints -------------------------------------------- */}
      <Section>
        <SectionHeading
          eyebrow="Operating constraints"
          title="These hold in code, not just on paper."
          lede="Each of these is enforced at the point where it would otherwise be violated, and each has a test that fails if it stops being true."
        />
        <div className="mt-10 grid gap-x-10 gap-y-8 lg:grid-cols-2">
          {OPERATING_CONSTRAINTS.map((constraint) => (
            <div key={constraint.title}>
              <h3 className="text-sm font-semibold">{constraint.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-navy-600">
                {constraint.body}
              </p>
            </div>
          ))}
        </div>
      </Section>

      {/* Before real data -------------------------------------------------- */}
      <Section tone="panel">
        <SectionHeading
          eyebrow="Before any real data"
          title="Nothing here has touched a real patient record."
        />
        <Prose className="mt-6">
          <p>
            Every figure in this build is synthetic. The demo patients are
            fixtures, the facility prices are generated deterministically from
            the CPT code, and the insurance documents are labelled samples.
          </p>
          <p>
            A HIPAA business associate agreement is a prerequisite before any
            real data flows through the system, and the operating constraints
            above are the reason the architecture is ready for that
            conversation rather than something to be retrofitted after it.
          </p>
        </Prose>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/demo" className="pavo-btn">
            See a proof generated
          </Link>
          <Link href="/audit" className="pavo-btn-quiet">
            Read the audit trail
          </Link>
        </div>
      </Section>
    </>
  );
}
