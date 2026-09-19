/**
 * Copy for the public pages.
 *
 * Everything here traces to something in the repository — README.md, the rule
 * engine in backend/app/rules.py, or a measured run. Nothing is aspirational.
 * If a claim on the site cannot be pointed at a file, it does not belong in
 * this module.
 */

/** One step of the authorization loop, as it actually runs in /demo. */
export type FlowStep = {
  title: string;
  body: string;
};

export const FLOW_STEPS: FlowStep[] = [
  {
    title: "EHR order fires a webhook",
    body: "A physician places an order and the webhook fires. No member of staff submits anything, and no one rekeys a fax.",
  },
  {
    title: "Both agents prove who they are",
    body: "Each organization holds an RSA-2048 key pair. Every ARIA message is signed over a SHA-256 digest of its contents, and a signature that fails verification is rejected before its payload is ever read.",
  },
  {
    title: "Criteria are proven, not disclosed",
    body: "A zero-knowledge proof shows the patient meets the payer's criteria. The age, the diagnosis code and the deductible amount never cross the boundary.",
  },
  {
    title: "A deterministic rule decides",
    body: "Five coverage rules are evaluated in order and the first match wins. A model never decides coverage — the engine cannot return an outcome without a rule ID.",
  },
  {
    title: "The decision carries its reasoning",
    body: "The outcome, the rule that produced it and the confidence are written to an append-only audit log. Anything without a definitive match escalates to a human rather than being guessed at.",
  },
  {
    title: "The member sees what they will pay",
    body: "The same authorization drives a price comparison across nearby facilities — what the member actually pays, through insurance or in cash.",
  },
];

/** The rule table, mirroring backend/app/rules.py. `GET /api/rules` returns it at runtime. */
export const COVERAGE_RULES = [
  { id: "PAVO-R001", procedure: "70553 (MRI brain)", diagnosis: "any", outcome: "APPROVED" },
  { id: "PAVO-R002", procedure: "27447 (knee replacement)", diagnosis: "M17.11", outcome: "APPROVED" },
  { id: "PAVO-R003", procedure: "27447 (knee replacement)", diagnosis: "any other", outcome: "ESCALATED" },
  { id: "PAVO-R004", procedure: "99214 (office visit)", diagnosis: "any", outcome: "APPROVED" },
  { id: "PAVO-R005", procedure: "any other", diagnosis: "any", outcome: "ESCALATED" },
] as const;

/** From README.md "Operating constraints" — these hold in code, not just on paper. */
export const OPERATING_CONSTRAINTS = [
  {
    title: "Raw PHI is never stored",
    body: "Patient identifiers are SHA-256 hashed before they reach the database. Member IDs read off an insurance card are hashed too, and the hash — never the raw value — is what appears in storage paths.",
  },
  {
    title: "Every decision carries a rule ID",
    body: "The rule engine cannot return an outcome without one, and it is written to the audit log on every decision.",
  },
  {
    title: "Ambiguity escalates",
    body: "Anything without a definitive rule match becomes escalated rather than being guessed at. The system knows what it does not know.",
  },
  {
    title: "No automated final denial",
    body: "A denial is either appealed or escalated to a human. The payer agent answers a rejected appeal with ESCALATED, never DENIED.",
  },
  {
    title: "Private keys never reach the database",
    body: "Key storage holds the public key and a digest of the private key, nothing more.",
  },
  {
    title: "Unverified messages do not act",
    body: "A signature that fails verification is rejected with a 401 before its payload is read, and the rejection is audited.",
  },
  {
    title: "Sample data is always labelled",
    body: "With no model key — or a text-only provider that cannot read the documents — the parsers return values that are obviously placeholders, and the API response names the source of each half. Nothing silently invents a member's plan.",
  },
] as const;

/**
 * From README.md "Known limitations".
 *
 * This is on the site deliberately. A panel that can tell what is a prototype
 * will find this list anyway; stating it first is the stronger position.
 */
export const WORKING_NOW = [
  "The full authorization loop, end to end, in about eleven seconds",
  "ARIA envelopes signed RSASSA-PSS over SHA-256, with an RSA-2048 key pair per organization",
  "groth16 proofs over bn128 — the circuit artifacts are committed, so proving works out of the box",
  "Five deterministic coverage rules, each decision carrying the rule that produced it",
  "An append-only audit log covering every entity, exportable as CSV",
  "Autonomous appeals with a confidence threshold below which the system escalates instead",
] as const;

export const NOT_YET = [
  {
    title: "The ZK circuit is deliberately simplified",
    body: "The approved-diagnosis check compares against a single hash, so a passing proof does tell the payer the patient carries that one diagnosis. Proving membership in a set of many codes without revealing which needs a Merkle circuit. The age and deductible criteria leak nothing.",
  },
  {
    title: "The trusted setup is local",
    body: "The build runs its own Powers of Tau ceremony, so whoever runs it knows the toxic waste. Fine for a prototype; these artifacts should never secure anything real.",
  },
  {
    title: "Facility pricing is mocked",
    body: "Prices are generated deterministically from the CPT code rather than gathered from facilities by the voice agent.",
  },
  {
    title: "NPI verification is a flag",
    body: "Not yet a lookup against the live CMS registry.",
  },
  {
    title: "Federated learning is not built",
    body: "It is described in the specification as a later phase and is not part of the running system.",
  },
] as const;

/**
 * A real public-signals array from a proof generated by this system.
 * The payer receives exactly this and nothing else.
 */
export const ZK_PUBLIC_SIGNALS = [
  "1",
  "1",
  "1",
  "18",
  "19673004205371315839122558043490202024231",
  "1",
];
