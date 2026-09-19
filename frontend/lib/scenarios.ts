/**
 * The scenarios the running system can actually produce.
 *
 * One list, shared by the demo's scenario picker and the dashboard's submit
 * form, so the two cannot drift and every rule in backend/app/rules.py has a
 * one-click way to reach it.
 *
 * Note there is no denial scenario, and that is deliberate rather than a gap:
 * the rule engine only ever returns APPROVED or ESCALATED. A final denial is
 * never issued automatically — see DENIAL_NOTE below.
 */
export type Outcome = "approves" | "escalates";

export type Scenario = {
  label: string;
  /** What a judge should notice, shown under the picker once selected. */
  detail: string;
  procedure: string;
  diagnosis: string;
  outcome: Outcome;
  ruleId: string;
};

export const SCENARIOS: Scenario[] = [
  {
    label: "MRI brain",
    detail: "Covered for any diagnosis, so it settles without a human.",
    procedure: "70553",
    diagnosis: "G43.909",
    outcome: "approves",
    ruleId: "PAVO-R001",
  },
  {
    label: "Knee replacement, matching Dx",
    detail: "The specific knee rule matches first and approves.",
    procedure: "27447",
    diagnosis: "M17.11",
    outcome: "approves",
    ruleId: "PAVO-R002",
  },
  {
    label: "Knee replacement, other Dx",
    detail:
      "Same procedure, different diagnosis. No definitive match, so it escalates to a human with the record already assembled.",
    procedure: "27447",
    diagnosis: "M17.12",
    outcome: "escalates",
    ruleId: "PAVO-R003",
  },
  {
    label: "Office visit",
    detail: "A routine visit, approved outright.",
    procedure: "99214",
    diagnosis: "Z00.00",
    outcome: "approves",
    ruleId: "PAVO-R004",
  },
  {
    label: "Unknown procedure",
    detail:
      "Nothing in the table covers it. The catch-all escalates rather than guessing.",
    procedure: "12345",
    diagnosis: "Z00.00",
    outcome: "escalates",
    ruleId: "PAVO-R005",
  },
];

/** Why the Denied filter is always empty, in the places a visitor asks. */
export const DENIAL_NOTE =
  "The rule engine returns APPROVED or ESCALATED and nothing else. A final denial is never issued automatically — see the appeals path instead.";

/** How to reach the appeal flow, which is the closest thing to a denial case. */
export const APPEAL_NOTE =
  "Appeals start from a payer's denial reason. Run an escalating scenario, open its trail, and generate an appeal against one of the four reason codes.";
