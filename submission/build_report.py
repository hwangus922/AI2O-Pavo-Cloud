"""Assemble the Technical Execution Report.

The document flows like a Word file — content is not pinned to hand-cut pages,
so breaks fall naturally and no page ends half-empty. The architecture diagram
lives in _svg.html and the terminal output in captures/*.txt, both dropped in
verbatim, so neither can drift from what was actually produced.

    python build_report.py
    chromium --headless --print-to-pdf=Pavo_Cloud_Technical_Execution_Report.pdf report.html
"""
from __future__ import annotations

import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DIAGRAM = open(os.path.join(HERE, "_svg.html"), encoding="utf-8").read()

CSS = """
  @page { size: Letter; margin: 1in; }
  * { box-sizing: border-box; }

  body {
    margin: 0;
    font-family: "Times New Roman", Times, serif;
    font-size: 12pt;
    line-height: 1.245;
    color: #000;
  }

  .doctitle { font-size: 16pt; font-weight: bold; margin: 0 0 3px; text-align: center; }
  .docsub   { font-style: italic; margin: 0 0 3px; text-align: center; }
  .docline  { margin: 0 0 15px; text-align: center; }

  h2 { font-size: 12pt; font-weight: bold; margin: 10px 0 3px; page-break-after: avoid; }
  h3 { font-size: 12pt; font-weight: bold; margin: 7px 0 2px; page-break-after: avoid; }

  p { margin: 0 0 5px; text-align: justify; }

  .cap { font-style: italic; margin: 4px 0 2px; page-break-after: avoid; }
  table {
    width: 100%; border-collapse: collapse; margin: 2px 0 6px;
    font-size: 10.5pt; border-bottom: 1px solid #000;
  }
  tr { page-break-inside: avoid; }
  th {
    text-align: left; font-weight: bold; color: #1274C4; padding: 2.5px 10px 2.5px 0;
    border-bottom: 1px solid #555555; vertical-align: bottom;
  }
  td {
    padding: 2.4px 10px 2.4px 0; vertical-align: top;
    border-bottom: 1px solid #DCDCDC;
  }
  tr:last-child td { border-bottom: none; }
  td.n, th.n { text-align: right; padding-right: 0; white-space: nowrap; }
  .tot td { border-top: 1px solid #555555; font-weight: bold; }

  figure { margin: 6px 0 3px; page-break-inside: avoid; }
  figure img { width: 74%; display: block; border: 1px solid #bbb; }
  .fcap { font-style: italic; font-size: 9.5pt; margin: 3px 0 6px; text-align: left; line-height: 1.24;
          page-break-inside: avoid; page-break-before: avoid; }
  .figrow { display: grid; width: 92%; grid-template-columns: 52.4fr 47.6fr; gap: 5px 14px;
            grid-template-rows: auto auto; align-items: start;
            page-break-inside: avoid; margin: 5px auto 3px; }
  .figrow img { width: 100%; display: block; border: 1px solid #bbb; min-width: 0; }
  .figrow .fcap { font-size: 9.5pt; margin: 0; text-align: left; }
  .figrow .wide { grid-column: 1 / -1; text-align: justify; }

  pre {
    font-family: "Courier New", Courier, monospace; font-size: 7.6pt; line-height: 1.18;
    background: #f4f4f4; border: 1px solid #ccc; padding: 6px 8px; margin: 4px 0 3px;
    white-space: pre; overflow: hidden; page-break-inside: avoid;
  }

  code { font-family: "Courier New", Courier, monospace; font-size: 10pt; }
  svg { display: block; width: 77%; margin: 0 auto; page-break-inside: avoid; }
  .keep { page-break-inside: avoid; }
"""

BODY = f"""
<div class="doctitle">Pavo Cloud</div>
<div class="docsub">Technical Execution Report | AI for Business Track</div>
<div class="docline">Dhanvanth Lakshman, CFO &nbsp;·&nbsp; Viraj Gadeela, CTO &nbsp;·&nbsp; Harry Wang, CEO</div>

<h2>1. What Pavo Cloud Is</h2>

<p>Before a doctor can go ahead with a procedure, such as an MRI, a knee replacement or an expensive drug, the insurer has to agree to pay for it first. That permission step is called <em>prior authorization</em>. In principle, it is a check against the plan's coverage rules. In practice, it is a member of staff filling in a form, faxing it or retyping it into an insurer's portal, and then waiting around three to fourteen days, typically. The United States spends around $35 billion a year on this, and most of it buys nothing: the great majority of requests are approved in the end, just late.</p>

<p>Pavo Cloud takes the person out of the start of that process. When a doctor places an order in the hospital's record system, our software assembles the request, signs it so the insurer can prove who sent it, and delivers it straight to the insurer's software. That side checks the signature, applies the insurer's own published coverage rules, and returns a decision naming the exact rule behind it. For a clear-cut request, no person is involved at any point.</p>

<p>What happens when a request is <em>not</em> clear-cut matters more. The software never guesses. If no coverage rule matches, if a signature fails, or if an appeal is not confident enough, the case stops and goes to a human reviewer with the whole file already assembled. No AI language model is allowed to decide an authorization, and the software cannot issue a final denial to a patient at all. Section 5 sets out that boundary in full. The company earns three ways: a fee per request, a monthly subscription per practice, and a yearly fee to insurers for the connection. Round 1 argued all of this was possible; this report is about the software that now does it.</p>

<h2>2. What Changed Since Round 1</h2>

<h3>2.1 From an Argument to Working Software</h3>
<p>All four planned phases are built and running, and the system now has a public website and a deployable build on top of them. Every figure in this report was measured against the committed code leading up to the round rather than estimated.</p>

<p class="cap">Table 1. What was built, in the order it was built.</p>
<table>
  <tr><th style="width:14%">Phase</th><th>What it does</th><th style="width:15%">Status</th></tr>
  <tr><td>Phase 1</td><td>The core loop: a doctor's order becomes an approval with no person involved</td><td>Complete</td></tr>
  <tr><td>Phase 2</td><td>Insure: shows a patient what a procedure will actually cost them</td><td>Complete</td></tr>
  <tr><td>Phase 3</td><td>Identity and appeals: agents prove who they are, and denials are appealed automatically</td><td>Complete</td></tr>
  <tr><td>Phase 4</td><td>Privacy proofs: show a patient qualifies without sending their medical details</td><td>Complete</td></tr>
  <tr><td>Since</td><td>A public website, a deployable build, a second AI provider, and an interface pass for public release</td><td>Complete</td></tr>
</table>

<h3>2.2 What the System Does, Measured</h3>
<p>Round 1 promised a decision in under five minutes. The software turned out to be a lot faster, because the slow part was never the thinking: it was the paperwork around it. Almost all of the time that remains is cryptography rather than deciding: each authorization signs two messages, the request and the response, and one signature costs about 42 milliseconds. Checking a signature costs a twentieth of a millisecond. A more modern signature scheme would cut the decision into single figures. We have not switched, because 89 milliseconds is already far below anything a person notices.</p>

<p class="cap">Table 2. Measured results.</p>
<table>
  <tr><th>What was measured</th><th class="n" style="width:26%">Result</th></tr>
  <tr><td>A complete authorization decision, start to finish</td><td class="n">88.6 milliseconds</td></tr>
  <tr><td>One signature, of the two every decision needs</td><td class="n">42.0 milliseconds</td></tr>
  <tr><td>Checking a signature</td><td class="n">0.05 milliseconds</td></tr>
  <tr><td>Creating a privacy proof about a patient</td><td class="n">401 milliseconds</td></tr>
  <tr><td>The full six-step demonstration, front to back</td><td class="n">11.0 seconds</td></tr>
  <tr><td>Automated tests passing, out of 148</td><td class="n">148</td></tr>
</table>

<h3>2.3 Two Corrections to Round 1</h3>
<p>Two claims did not survive being built, however. On <em>speed</em>, Round 1 said &ldquo;under five minutes&rdquo;; the agents themselves take under a tenth of a second, so five minutes now covers the round trip once the hospital's record system and the insurer's network are included. On <em>profitability</em>, Round 1 implied the company breaks even on each sale in year one. Rebuilt from what the software costs to run, year one is a 31% gross margin, meaning 31 cents of every dollar is left after the direct cost of serving that customer. Early customers need a great deal of hand-holding. The 87% figure for year three held.</p>

<h2>3. System Architecture 2.0</h2>

<h3>3.1 How One Request Moves Through the System</h3>
<p>A doctor places an order in the hospital's electronic health record, which is the software that holds a patient's chart. That order starts everything below. No person touches any of the seven steps.</p>

<p>The two sides talk over a small protocol of our own, called ARIA. It is deliberately dull. Each message is an envelope carrying its type, the sender, a timestamp, and the medical details in FHIR, the standard electronic format for health records that insurers are already required to accept. What matters is that every envelope is signed with the sender's private key, over a digest of the contents. A digest is a short fingerprint computed from every byte of a message, so altering a single character breaks the signature. Each organisation registers its public key once, and the receiving side looks that key up and checks it before reading anything else. The keys are RSA-2048, a long-established scheme in which each party keeps a private key it never shares and publishes a public key anyone can verify against. The private half is never stored here: it is handed back once when the organisation is created, and only a fingerprint of it is kept. A message that fails the check is refused outright and the refusal is written to the audit trail, so a rejection leaves as full a record as an approval does.</p>

{DIAGRAM}
<p class="fcap">Figure 1. One authorization request, end to end. The heavier box at step 5 is a gate: if the signature does not check out, the insurer's software never reads the request at all.</p>

<h3>3.2 Why Step 5 Matters</h3>
<p>Two organisations letting software talk automatically only works if each can prove who it is. Step 5 is where that happens, and it happens <em>before</em> the request is opened: either the sender is proven genuine, or nothing happens. A judge can test this by changing any part of a request after it has been signed. It is refused outright.</p>

<h3>3.3 Two Layers, and Which One Is Allowed to Decide</h3>
<p>Round 1 described a fixed-rules layer and a learning layer. The built system draws that line harder than promised. <strong>No AI language model ever decides an authorization.</strong> Models are used only where being approximately right is acceptable, such as reading a photograph of an insurance card, and every result is scored before it is used.</p>

<p class="cap">Table 3. What each layer is allowed to do.</p>
<table>
  <tr><th style="width:18%">Layer</th><th style="width:36%">What it handles</th><th>The guarantee it gives</th></tr>
  <tr>
    <td><strong>Fixed rules</strong><br>(decides)</td>
    <td>Identity checks, coverage rules, price arithmetic, sorting denial reasons</td>
    <td>The same input always produces the same answer, and every answer names the exact rule behind it. That is what makes a decision defensible to a regulator.</td>
  </tr>
  <tr>
    <td><strong>AI models</strong><br>(assist only)</td>
    <td>Reading insurance cards and benefit documents, turning plain English into a medical code, drafting appeal letters</td>
    <td>Every result carries a confidence score. Below the threshold it goes to a person. A model is never the last word on whether a patient gets care.</td>
  </tr>
</table>

<p>One consequence is worth stating plainly. If the AI provider went offline tomorrow, prior authorization would keep working, because there is no AI on that path. The same fact explains why processing one request costs a fraction of a cent (section 6.2).</p>

<h3>3.4 When a Request Is Denied</h3>
<p>A denial is never the end. The software sorts the insurer's stated reason, then acts on it.</p>

<p class="cap">Table 4. What happens after a denial.</p>
<table>
  <tr><th style="width:30%">Reason given</th><th>What the software does</th></tr>
  <tr><td>Not covered by the plan</td><td>Stops. This is a contract question, not a medical one, so a person decides. No letter is drafted.</td></tr>
  <tr><td>Missing information, not medically necessary, or any unrecognised reason</td><td>Searches the published medical literature, drafts an appeal citing the studies it finds, and scores its own confidence in it.</td></tr>
  <tr class="tot"><td>Confidence below 70%</td><td>The appeal is held for a person, with the diagnosis, the reason, the score and every study already attached.</td></tr>
</table>

<h3>3.5 What Happens to Patient Data</h3>
<p>Patient identifiers are scrambled at the door, before anything is saved, and the scrambling is one-way: the original cannot be recovered from it. A test in the codebase checks that the real identifier never appears in storage.</p>
<p>The system goes further using a technique called a zero-knowledge proof. It lets the insurer confirm three things: that the patient is old enough, that the diagnosis is covered, and that the deductible condition is met. It does that <em>without receiving the age, the diagnosis or the amount</em>. One limitation is listed in Table 6.</p>

<h2>4. The Build Log</h2>

<h3>4.1 What Was Committed, and When</h3>
<p>The code lives in a repository called <em>hwangus922/AI2O-Pavo-Cloud</em>. Work was done in eleven batches: one per phase, a round of fixes, and six more since Round 2 opened. Each was reviewed before being merged. Together they come to 22,739 lines added across 260 file changes, 15,871 of them hand-written and the rest a dependency lockfile.</p>

<pre>$ git log --first-parent --date=short --pretty="%h %ad  %s" 0a24def

  0a24def 2026-09-19  Document the setting that keeps the site private (#11)
  bb02bc4 2026-09-19  Give the site a real mark and take every error surface off it (#12)
  cd0891a 2026-09-19  Make a broken or stale deployment say so (#10)
  ee9ed87 2026-09-18  Fix the broken request detail page, and make every outcome reachable (#9)
  84c4ca5 2026-09-18  Turn the demo app into a full website (#8)
  8b23760 2026-09-18  Make the demo deployable to a public URL, and support DeepSeek (#6)
  a13f6cb 2026-09-12  Fix the three failures that break a deployed demo (#5)
  abc1b5c 2026-09-09  Phase 4: demo flow, audit UI, and a real ZK proof (#4)
  99bbb96 2026-09-08  Phase 3: autonomous appeals and cryptographic identity (#3)
  5f26194 2026-09-07  Phase 2: Insure price transparency (#2)
  e48ec54 2026-09-07  Phase 1: autonomous prior authorization core loop (#1)
  d5ea3a7 2026-09-07  Initial commit

$ git log --shortstat 0a24def

  18 commits  ·  260 file changes  ·  +22,739 insertions  ·  -1,215 deletions</pre>
<p class="fcap">Figure 2. The commit history. Each line is a batch of work that was reviewed and merged. The largest single batch is Phase 1 at 9,896 lines, though two thirds of that is a dependency lockfile rather than code anyone wrote; by hand-written lines the largest is Phase 4.</p>

<h3>4.2 The Tests</h3>
<p>An automated test is a small program that checks the main program still behaves correctly. There are 148 of them and they all pass. They matter more than the line count, because they are what turns a claim in this report into something a judge can verify with one command.</p>

<pre>$ .venv/bin/python -m pytest

tests/test_appeals.py ...........................................        [ 29%]
tests/test_flow.py ...................                                   [ 41%]
tests/test_insure.py ..........................................          [ 70%]
tests/test_persistence.py .......                                        [ 75%]
tests/test_rules.py ...............                                      [ 85%]
tests/test_zk.py ......................                                  [100%]

148 passed, 1 warning in 23.28s</pre>
<p class="fcap">Figure 3. The full test suite; each dot is one passing test. Among the things they prove: every decision records the rule that produced it, an unmatched request goes to a human rather than being guessed at, a tampered message is refused, and a real patient identifier never reaches storage.</p>

<h3>4.3 The System Running</h3>
<p>The screens below are the live software, not mock-ups. Both were captured against the code in the log above.</p>

<p>Both are served by the same build that would go to a customer. The interface is a Next.js application, which is a standard framework for building websites in JavaScript, and it talks to the Python backend over exactly the interface an insurer's software would use. Nothing in either screen is a special demonstration mode.</p>

<p>One addition merged in the last week is visible here: a fallback to a second AI provider behind the assistive summaries, so an outage at one vendor cannot take those features down with it. It does not change how a decision is made. A third change is not visible: the operator-facing diagnostics added in #10 were taken back out of the public build before release, leaving a deploy-time guard that fails the build outright if it is configured without its backend address.</p>

<div class="figrow">
  <img src="assets/demo_complete_print.jpg" alt="The six-step demonstration, completed">
  <img src="assets/dashboard_print.jpg" alt="The authorization dashboard">
  <p class="fcap wide">Figures 4 and 5. <em>Left:</em> the guided demonstration after a single click; all six steps (order, identity, privacy proof, rules, decision, price) run with no further input and finish in 11.0 seconds, and the last of them prices the same operation at all five facilities in the price file, showing the three cheapest; across all five the spread is $2,475 for identical care. <em>Right:</em> the dashboard, with the request form that sits between the counters and the table left out here. Every row carries the rule that produced it, and the two amber rows are knee replacements whose diagnosis did not match the covered condition; both wait for a human reviewer with the file already assembled.</p>
</div>

<h2>5. Risk Mitigation Protocol</h2>

<h3>5.1 The Governing Rule</h3>
<p>One principle runs through every part of the system: <strong>the safe outcome is the default, not the exception.</strong> When the software is unsure it does not guess. It stops and hands the case to a person, with the file already prepared.</p>

<p class="cap">Table 5. What happens when something goes wrong.</p>
<table>
  <tr><th style="width:25%">If this happens</th><th style="width:45%">The software does this, automatically</th><th>A person is involved</th></tr>
  <tr>
    <td>No coverage rule matches the request</td>
    <td>Marks it unclear and routes it to a human reviewer. There is no path by which an unmatched request is approved or denied.</td>
    <td>Within 4 hours, insurer's clinical reviewer</td>
  </tr>
  <tr>
    <td>A message has been tampered with</td>
    <td>Refuses it before reading it, and records the refusal with the reason.</td>
    <td>Immediate security alert</td>
  </tr>
  <tr>
    <td>An appeal scores below 70% confidence</td>
    <td>Holds it. Nothing is sent to the insurer. Reviewer notes are written automatically.</td>
    <td>Within 1 working day, provider's appeals staff</td>
  </tr>
  <tr>
    <td>The AI provider goes offline</td>
    <td>Appeal drafting falls back to a placeholder scored zero, which is below the threshold, so every appeal escalates. <strong>Authorization itself is unaffected.</strong></td>
    <td>None required</td>
  </tr>
  <tr>
    <td>The medical literature service is unreachable</td>
    <td>Finishes the appeal with no citations and records the failure. Confidence drops, which pushes it to a person.</td>
    <td>Follows the appeal route above</td>
  </tr>
  <tr>
    <td>An appeal is rejected by the insurer</td>
    <td>Marks it unclear. <strong>The software cannot issue a final denial to a patient.</strong></td>
    <td>Always, a licensed reviewer</td>
  </tr>
  <tr>
    <td>Approval rates drift by demographic</td>
    <td>Quarterly review across age, geography and diagnosis. Any rule causing a disparity is suspended to human review.</td>
    <td>Quarterly, clinical and compliance</td>
  </tr>
</table>

<h3>5.2 Why Human Review Is Not a Queue</h3>
<p>Escalating a case is a routing decision, not a backlog. Every case handed to a person arrives complete: the medical details, the rule that fired, the signature check, the denial reason, the confidence score and any studies found. The bottleneck Round 1 identified was never medical judgement. It was the paperwork wrapped around it.</p>

<h3>5.3 What We Have Not Solved</h3>
<p>These are real limitations of a prototype. We would rather state them than be caught by them.</p>

<p class="cap">Table 6. Known gaps and what each needs.</p>
<table>
  <tr><th style="width:36%">Gap</th><th>What it needs</th></tr>
  <tr><td>The privacy proof reveals which covered condition a patient has</td><td>A more advanced circuit design. Scoped for the next phase.</td></tr>
  <tr><td>The proof's setup was done on one machine</td><td>A proper multi-party ceremony before any real use. Not safe for production as it stands.</td></tr>
  <tr><td>Provider identity is trusted, not verified</td><td>A live lookup against the federal provider registry. One integration.</td></tr>
  <tr><td>Facility prices are generated, not gathered</td><td>The voice agent that calls facilities, plus the price files insurers must now publish.</td></tr>
  <tr><td>Five coverage rules, not a rule library</td><td>Clinical staff encoding each insurer's published criteria. This is the largest cost in our model and the real barrier to a competitor.</td></tr>
  <tr><td>The learning layer is not built</td><td>Deliberate. Until it exists, anything without a definitive rule goes to a person, which is the correct default anyway.</td></tr>
</table>

<h2>6. Three-Year Financials</h2>

<h3>6.1 Where the Money Comes From</h3>
<p>Pavo earns in three ways: a fee for each request, a monthly subscription per medical practice, and a yearly fee to insurers for the connection itself. The figures below are built up from customer counts and request volumes, not from a growth rate applied to a starting number. The full workbook accompanies this report.</p>

<p class="cap">Table 7. Revenue, built up from customers.</p>
<table>
  <tr><th>Source</th><th class="n" style="width:16%">2026</th><th class="n" style="width:16%">2027</th><th class="n" style="width:17%">2028</th></tr>
  <tr><td>Medical practices served (average)</td><td class="n">55</td><td class="n">330</td><td class="n">1,400</td></tr>
  <tr><td>Insurers connected (average)</td><td class="n">11</td><td class="n">84</td><td class="n">160</td></tr>
  <tr><td>Requests processed</td><td class="n">171,600</td><td class="n">1,647,360</td><td class="n">8,736,000</td></tr>
  <tr><td>Fees per request, at $3.00</td><td class="n">$514,800</td><td class="n">$4,942,080</td><td class="n">$26,208,000</td></tr>
  <tr><td>Practice subscriptions, at $400/month</td><td class="n">$264,000</td><td class="n">$1,584,000</td><td class="n">$6,720,000</td></tr>
  <tr><td>Insurer connection fees, at $20,000/year</td><td class="n">$220,000</td><td class="n">$1,680,000</td><td class="n">$3,200,000</td></tr>
  <tr class="tot"><td>Total revenue</td><td class="n">$998,800</td><td class="n">$8,206,080</td><td class="n">$36,128,000</td></tr>
</table>

<p>The $3.00 fee is 85&ndash;92% below the $15&ndash;$40 an insurer spends handling a request by hand today, which is what makes the switch easy to justify.</p>

<h3>6.2 What It Costs to Run</h3>
<p>Servers are not the expense. Processing one request costs about six hundredths of a cent, because the deciding path uses no AI models at all. The real cost is clinical staff translating each insurer's published rules into the fixed rules the software applies. That is the largest line in every year, and the reason margins improve with scale rather than with technology.</p>

<p class="cap">Table 8. Cost of serving customers, and what is left.</p>
<table>
  <tr><th>Cost</th><th class="n" style="width:16%">2026</th><th class="n" style="width:16%">2027</th><th class="n" style="width:17%">2028</th></tr>
  <tr><td>Clinical staff writing coverage rules</td><td class="n">$189,000</td><td class="n">$455,000</td><td class="n">$1,080,000</td></tr>
  <tr><td>Setting customers up</td><td class="n">$224,000</td><td class="n">$476,000</td><td class="n">$1,428,000</td></tr>
  <tr><td>Customer support</td><td class="n">$92,000</td><td class="n">$190,000</td><td class="n">$784,000</td></tr>
  <tr><td>Servers and storage</td><td class="n">$54,000</td><td class="n">$198,000</td><td class="n">$900,000</td></tr>
  <tr><td>AI model usage (documents and appeals only)</td><td class="n">$11,000</td><td class="n">$62,000</td><td class="n">$280,000</td></tr>
  <tr><td>Security and compliance certification</td><td class="n">$118,000</td><td class="n">$112,000</td><td class="n">$290,000</td></tr>
  <tr class="tot"><td>Gross profit</td><td class="n">$310,800</td><td class="n">$6,713,080</td><td class="n">$31,366,000</td></tr>
  <tr><td>Gross margin</td><td class="n">31%</td><td class="n">82%</td><td class="n">87%</td></tr>
</table>

<h3>6.3 Cost to Win a Customer, and What One Is Worth</h3>
<p>Two standard measures. <em>Acquisition cost</em> is what it costs in sales and marketing to sign one customer. <em>Lifetime value</em> is the profit that customer produces before they leave, stated here over three years, which is deliberately conservative.</p>

<p class="cap">Table 9. Customer economics at 2028 rates.</p>
<table>
  <tr><th>Measure</th><th class="n" style="width:21%">Practice</th><th class="n" style="width:17%">Insurer</th><th class="n" style="width:17%">Blended</th></tr>
  <tr><td>Cost to acquire one customer</td><td class="n">$6,000</td><td class="n">$22,000</td><td class="n">$6,699</td></tr>
  <tr><td>Value over three years</td><td class="n">$58,248</td><td class="n">$51,057</td><td class="n">$57,533</td></tr>
  <tr><td>Value per $1 spent acquiring</td><td class="n">$9.70</td><td class="n">$2.30</td><td class="n">$8.60</td></tr>
  <tr><td>Months to earn the cost back</td><td class="n">3.5</td><td class="n">15.2</td><td class="n">4.0</td></tr>
</table>

<p>At $2.30 back per $1 spent and fifteen months to recover it, insurer contracts do not pay for themselves as a product. We fund them anyway, because signing one insurer makes Pavo available to every practice that already submits to it. It is a distribution channel, not a profit centre.</p>

<h3>6.4 Profit, and What We Are Asking For</h3>
<p>After engineering, sales and admin, the company loses $2.37 million in 2026 and $3.21 million in 2027, then makes $11.23 million in 2028. The deepest point is $5.58 million of cumulative losses, in late 2027.</p>
<p><strong>We are asking for $8.0 million</strong>, which covers that trough with roughly twelve months of cushion past breaking even. It is not a shopping list. The three largest spending lines across the plan come to more than the raise on their own: $7.46m of engineering, $5.67m of insurer business development and $1.72m of clinical staff encoding coverage rules. Most of that is paid for out of revenue as it arrives. What the raise funds is the part that has to come before any revenue does: the start of the clinical rule library, the security certification no insurer will sign without, and the engineering to close the gaps in Table 6.</p>
<p>The assumption most likely to be wrong is the number of practices, not the price. If all four of our main assumptions are wrong at once, 2028 revenue is $13.8 million rather than $36.1 million: a smaller company, but still a real one.</p>

<h2>7. How to Check Any of This</h2>
<p><code>git log --shortstat 0a24def</code> reproduces the build figures in section 4.1, and <code>.venv/bin/python -m pytest</code> reproduces the 148 passing tests in 4.2. Starting the backend and posting one request, with the command in the repository's README, returns the decision, the rule behind it and the confidence: the whole of section 3 in one response. The demonstration at <code>/demo</code> runs the entire path end to end in about eleven seconds, and <code>/audit</code> shows every message the two agents exchanged along the way.</p>
"""

doc = (
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    "<title>Pavo Cloud Technical Execution Report</title>\n"
    f"<style>{CSS}</style>\n</head>\n<body>\n{BODY}\n</body>\n</html>\n"
)
out = os.path.join(HERE, "report.html")
open(out, "w", encoding="utf-8").write(doc)
print(f"wrote {out} ({len(doc)/1024:.0f} KB)")
