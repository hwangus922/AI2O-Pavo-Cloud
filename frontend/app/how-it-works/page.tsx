import type { Metadata } from "next";
import Link from "next/link";

import { JsonBlock } from "@/components/JsonBlock";
import { Container } from "@/components/site/Container";
import { Prose } from "@/components/site/Prose";
import { Section } from "@/components/site/Section";
import { SectionHeading } from "@/components/site/SectionHeading";
import { COVERAGE_RULES } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "How it works — Pavo Cloud",
  description:
    "The ARIA protocol, cryptographic identity between organizations, and the deterministic rule engine behind every authorization decision.",
};

/**
 * A representative ARIA envelope. The shape matches what the provider agent
 * actually sends; the identifiers are truncated the way the UI truncates them.
 */
const ARIA_ENVELOPE = {
  protocol: "ARIA/1.0",
  message_id: "6a1c3698-...",
  message_type: "AUTH_REQUEST",
  sender: "agent://pavo/provider/metro-valley",
  recipient: "agent://pavo/payer/meridian",
  issued_at: "2026-09-19T00:35:53Z",
  payload: {
    procedure_code: "27447",
    diagnosis_code: "M17.11",
    patient_ref: "sha256:9f2b...",
    fhir_bundle_ref: "Bundle/ebc5500e",
  },
  signature: {
    algorithm: "RSASSA-PSS",
    digest: "SHA-256",
    value: "MEUCIQDf...",
  },
};

const AGENTS = [
  {
    name: "Provider agent",
    body: "Watches for the EHR webhook, assembles a FHIR R4 bundle from the order, and signs an AUTH_REQUEST. It never asks a human to assemble anything.",
  },
  {
    name: "Payer agent",
    body: "Verifies the signature, evaluates the coverage rules, and returns an AUTH_RESPONSE carrying the outcome and the rule that produced it.",
  },
  {
    name: "Escalation agent",
    body: "Takes anything without a definitive rule match and hands it to a human reviewer with the record already assembled — the bundle, the proof, the rule that failed to match.",
  },
];

export default function HowItWorksPage() {
  return (
    <>
      <Container className="py-16 sm:py-20">
        <p className="text-sm font-medium uppercase tracking-wide text-electric-600">
          How it works
        </p>
        <h1 className="mt-3 max-w-3xl text-4xl font-semibold tracking-tight">
          Two agents, one signed protocol, and a rule that can be read.
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-navy-600">
          ARIA — the Autonomous Request and Intelligence Architecture — is the
          envelope that carries an authorization across an organizational
          boundary. It is deliberately boring: signed JSON, a verified sender,
          and a payload that cannot be acted on until the signature checks out.
        </p>
      </Container>

      {/* The envelope ----------------------------------------------------- */}
      <Section tone="panel">
        <div className="grid gap-10 lg:grid-cols-2 lg:items-start [&>*]:min-w-0">
          <div>
            <SectionHeading
              eyebrow="The envelope"
              title="Every message states who sent it and proves it."
            />
            <Prose className="mt-6">
              <p>
                Each organization holds an RSA-2048 key pair. Pavo stores only
                the public key — the private key is returned once, at
                provisioning, and never reaches the database.
              </p>
              <p>
                Every message is signed over a SHA-256 digest of its canonical
                contents using RSASSA-PSS, and checked against the sender&apos;s
                registered key <em>before</em> its payload is read. A signature
                that fails verification is rejected with a 401 and the rejection
                is written to the audit log.
              </p>
              <p>
                Sender and recipient are addresses, not strings —
                <span className="pavo-id break-all">
                  {" "}
                  agent://pavo/payer/meridian
                </span>{" "}
                —
                so every row in the audit trail names the agent that produced
                it.
              </p>
            </Prose>
          </div>
          <div>
            <p className="mb-3 text-xs font-medium uppercase tracking-wide text-navy-400">
              AUTH_REQUEST
            </p>
            <JsonBlock value={ARIA_ENVELOPE} />
          </div>
        </div>
      </Section>

      {/* The agents ------------------------------------------------------- */}
      <Section>
        <SectionHeading
          eyebrow="The agents"
          title="Three roles, and one of them is knowing when to stop."
        />
        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {AGENTS.map((agent) => (
            <div key={agent.name} className="pavo-card p-5">
              <h3 className="text-sm font-semibold">{agent.name}</h3>
              <p className="mt-2 text-sm leading-relaxed text-navy-600">
                {agent.body}
              </p>
            </div>
          ))}
        </div>
      </Section>

      {/* The rule engine -------------------------------------------------- */}
      <Section tone="panel">
        <SectionHeading
          eyebrow="The rule engine"
          title="First match wins, and the match is recorded."
          lede="Five rules ship today. They are evaluated in order, so the specific knee rule is checked before the general one, and the engine cannot return an outcome without naming the rule behind it."
        />
        <div className="mt-8 overflow-x-auto">
          <table className="w-full min-w-[30rem] text-left text-sm">
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
                  <td className="py-3 font-medium">{rule.outcome}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Prose className="mt-8">
          <p>
            Adding a payer means adding rules, not retraining anything. The
            table is returned by{" "}
            <span className="pavo-id">GET /api/rules</span> at runtime, so what
            the engine will do is inspectable before you send it a request.
          </p>
        </Prose>
      </Section>

      {/* Escalation and appeals ------------------------------------------- */}
      <Section>
        <SectionHeading
          eyebrow="When it doesn't resolve"
          title="The system never issues a final denial on its own."
          lede="This is a design constraint, not a limitation of the current build."
        />
        <div className="mt-8 grid gap-4 lg:grid-cols-2">
          <div className="pavo-card p-5">
            <h3 className="text-sm font-semibold">Escalation</h3>
            <p className="mt-2 text-sm leading-relaxed text-navy-600">
              Anything without a definitive rule match becomes{" "}
              <span className="pavo-id">escalated</span> rather than guessed at.
              A human picks it up with the FHIR bundle, the proof and the rule
              that failed to match already in front of them — the assembly work
              is done, only the judgement is left.
            </p>
          </div>
          <div className="pavo-card p-5">
            <h3 className="text-sm font-semibold">Appeals</h3>
            <p className="mt-2 text-sm leading-relaxed text-navy-600">
              A denial is either appealed or escalated. The appeal agent drafts
              from the clinical record and cited literature, and below a
              confidence threshold it escalates instead of filing. A{" "}
              <span className="pavo-id">not_covered</span> denial is never
              appealed automatically — coverage is a contract question, not a
              clinical one.
            </p>
          </div>
        </div>
        <div className="mt-10 flex flex-wrap gap-3">
          <Link href="/demo" className="pavo-btn">
            Watch it run
          </Link>
          <Link href="/privacy" className="pavo-btn-quiet">
            How PHI is handled
          </Link>
        </div>
      </Section>
    </>
  );
}
