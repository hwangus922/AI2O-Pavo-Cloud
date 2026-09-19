# Build prompt: Pavo Cloud Round 2 pitch deck

Paste everything below this line into the agent that will build the deck.

---

## 1. Your role and the job

You are a presentation designer building the **Round 2 pitch deck for Pavo Cloud**, a
company selling autonomous prior-authorization software to US healthcare providers and
insurers. This deck is a competition submission in the "AI for Business" track. It
refines an existing Round 1 deck and must add one new required slide (Current Traction).

Deliver a **16:9 slide deck, 16 slides plus 3 appendix slides**, as a PDF. Build it in
HTML/CSS rendered to PDF at 1920×1080 per slide (or Google Slides / PowerPoint if you
have no rendering path, but PDF is the deliverable).

There is a companion document, the **Technical Execution Report** (8 pages). The deck and
that report are read by the same judges. **Every number in this deck must match the
report.** The figures are given to you in section 3 below; use those exact values.

## 2. Hard rules: read before writing a single slide

1. **Do not invent traction.** Pavo has no customers, no pilots, no letters of intent, no
   revenue and no deployment. Its traction is *build* traction: working software, a test
   suite, measured performance. If you catch yourself writing "3 design partners" or
   "$40k in signed LOIs", stop; that is fabrication and it will lose the round.
2. **Do not round numbers up.** 81.8 milliseconds is not "under 50ms". $998,800 is not
   "$1M+" (you may write "$1.0M" where space demands, since the report does).
3. **The speed claim must be stated carefully.** The *agents* reach a decision in 81.8
   milliseconds. The *end-to-end* round trip is under five minutes once the hospital's
   record system and the insurer's network are included. Round 1 said "3 to 4 minutes"
   without that distinction; the report corrects it. Every speed claim in this deck must
   carry the distinction. Never imply a patient gets an answer in 82 milliseconds.
4. **Year 1 gross margin is 31%, not break-even.** Round 1 implied the company breaks even
   per sale in year one. It does not. Say 31% and say why (early customers need heavy
   hand-holding). The 87% figure is year 3.
5. **The $8.0M ask is sized against peak cumulative burn of $5.58M**, giving roughly twelve
   months of cushion past breakeven. Do **not** present a "use of funds" pie that sums to
   more than $8.0M. (The three-year spend lines, $1.72M clinical rules, $520K security,
   $5.67M payer BD, $7.46M engineering, total $15.37M and are funded by revenue *plus*
   the raise. Presenting them as "what the $8M buys" is wrong.)
6. **Statistics carried over from Round 1 need a citation or they get cut.** The ones in
   this bucket: 94% of doctors report delays, 97% of requests approved, $35B annual cost,
   3–14 day decision time, $6.2B SAM by 2033, $45.3M SOM by 2028, 47M payer-provider
   interactions/year. Put a source in small type under each, or drop the stat. Judges in
   round 2 check.
7. **British/American spelling:** use American throughout (authorization, not
   authorisation).
8. **No em dashes anywhere on a slide.** Use a comma, a colon, a semicolon or a full stop,
   whichever the sentence actually needs. En dashes are fine in number ranges (85-92%,
   $15-$40). The Technical Execution Report follows the same rule, so the two documents
   read as one voice.

## 3. The number sheet: single source of truth

Copy these exactly. Do not recompute, do not restate in other units.

### Measured system performance (measured 19 Sept 2026 against committed code)
| Metric | Value |
|---|---|
| Complete authorization decision, start to finish | 81.8 milliseconds |
| One RSA-2048 signature, of the two every decision needs | 37.9 milliseconds |
| Checking a signature | 0.05 milliseconds |
| Creating one zero-knowledge privacy proof | 365 milliseconds |
| Full six-step guided demonstration | 11.1 seconds |
| Automated tests passing | 148 of 148 |

### Build metrics (repository `hwangus922/AI2O-Pavo-Cloud`, through commit `cd0891a`)
| Metric | Value |
|---|---|
| Lines of code | 22,459 insertions, 646 deletions |
| File changes | 238 |
| Commits | 16, in 9 reviewed batches |
| Build window | 7–19 September 2026 (13 days) |
| Phases complete | 4 of 4 |
| Largest phase | Phase 1, 9,429 lines |
| Coverage rules encoded | 5 |

### Commit history (use verbatim if you show a terminal block)
```
a13f6cb 2026-09-12  Fix the three failures that break a deployed demo (#5)
abc1b5c 2026-09-09  Phase 4: demo flow, audit UI, and a real ZK proof (#4)
99bbb96 2026-09-08  Phase 3: autonomous appeals and cryptographic identity (#3)
5f26194 2026-09-07  Phase 2: Insure price transparency (#2)
e48ec54 2026-09-07  Phase 1: autonomous prior authorization core loop (#1)
d5ea3a7 2026-09-07  Initial commit
```

### Revenue build
| Line | 2026 | 2027 | 2028 |
|---|---|---|---|
| Practices served (avg) | 55 | 330 | 1,400 |
| Insurers connected (avg) | 11 | 84 | 160 |
| Requests processed | 171,600 | 1,647,360 | 8,736,000 |
| Fees per request @ $3.00 | $514,800 | $4,942,080 | $26,208,000 |
| Practice subs @ $400/mo | $264,000 | $1,584,000 | $6,720,000 |
| Insurer fees @ $20,000/yr | $220,000 | $1,680,000 | $3,200,000 |
| **Total revenue** | **$998,800** | **$8,206,080** | **$36,128,000** |

### Margin and profit
| Line | 2026 | 2027 | 2028 |
|---|---|---|---|
| Cost of revenue | $688,000 | $1,493,000 | $4,762,000 |
| Gross profit | $310,800 | $6,713,080 | $31,366,000 |
| Gross margin | 31% | 82% | 87% |
| EBITDA | −$2,366,200 | −$3,214,920 | $11,226,000 |
| Cumulative EBITDA | −$2,366,200 | −$5,581,120 | $5,644,880 |

### Unit economics, at 2028 rates
| Metric | Practice | Insurer | Blended |
|---|---|---|---|
| CAC | $6,000 | $22,000 | $6,699 |
| LTV (3-year) | $58,248 | $51,057 | $57,533 |
| LTV:CAC | 9.7× | 2.3× | 8.6× |
| CAC payback | 3.5 months | 15.2 months | 4.0 months |
| Annual logo churn | 5.0% | 2.0% | 4.7% |

### Cost structure
- Cost to process one request: **about six hundredths of one cent** ($0.0006). The
  deciding path runs no AI models at all, which is why.
- Largest cost line in every year: **clinical staff encoding each insurer's published
  coverage rules.** Not servers. Margins improve with scale, not with technology.
- Downside case: if all four main assumptions are wrong at once, 2028 revenue is
  **$13.8M** rather than $36.1M.

### Technology (for the architecture slide: all of this is built and running)
FastAPI/Python backend · Next.js 14 frontend · Supabase · FHIR R4 bundles ·
RSA-2048 RSASSA-PSS message signing · circom/snarkjs zero-knowledge circuits ·
append-only audit log, five time-stamped entries per request.

## 4. Design system

- **Slide size** 1920×1080 px (16:9). Safe margin 96px all sides.
- **Primary blue** `#1274C4`. **Ink** `#111111`. **Body grey** `#444444`.
  **Rule grey** `#DCDCDC`. **Wash** `#F2F7FC`. **Amber (escalation only)** `#B8860B`.
  **Red is reserved for competitor gaps and denial paths, never for Pavo.**
- **Type** Headings and body in a serif that matches the report: Times New Roman /
  Source Serif. Numbers and code in a mono face (Courier New / JetBrains Mono).
  If the deck must feel more modern than the report, use Inter for body and keep the
  serif for slide titles only, but pick one system and hold it for all 19 slides.
- **Sizes** Slide title 54px bold · section eyebrow 20px letter-spaced uppercase in blue ·
  body 26px · caption 18px italic · big stat numerals 96–120px bold.
- **Layout grid** 12 columns, 48px gutters.
- **Every slide carries**: a thin 4px blue rule across the top; the slide title top-left;
  page number bottom-right in 16px grey; the word mark "Pavo Cloud" bottom-left in 16px.
- **No stock photography. No clip art. No gradients. No drop shadows.** Line art, flat
  fills and type only. The Round 1 deck's flat blue icon circles were right; keep that.
- **One idea per slide.** If a slide has more than ~60 words of body copy, cut it.

## 5. Slide-by-slide specification

### Slide 1: Title
**Layout** Centered, vertically stacked, generous whitespace.
**Copy**
- Wordmark "Pavo Cloud" 120px bold.
- Subhead: "Autonomous Prior Authorization"
- One line: "The insurer's answer in 81.8 milliseconds. The whole round trip in under five minutes, not three days."
- Rule, then team line: "Dhanvanth Lakshman, CFO · Viraj Gadeela, CTO · Harry Wang, CEO"
- Bottom-right badge: "AI for Business Track · Round 2"
**Visual** None beyond a single 4px blue rule under the wordmark. Resist the urge to
decorate the title slide.

### Slide 2: The problem
**Layout** Title, one-sentence setup, then a 4-up stat row across the lower two thirds.
**Copy** Title: "Prior Authorization Is Broken". Setup: "A doctor orders treatment and the
patient waits, not for a clinical reason, but for an insurer's approval."
**Visual** Four stat cards, equal width, separated by 1px `#DCDCDC` vertical rules (no
boxes). Each: numeral 110px bold in `#1274C4`, label 24px below in grey, **source in 14px
italic under the label**.
| Numeral | Label |
|---|---|
| 3–14 | days to a decision |
| 94% | of doctors report delays |
| 97% | of requests approved anyway |
| $35B | spent on the process each year |
**Design note** The punchline is the pairing of 97% and 3–14 days: almost everything gets
approved, but only after the wait. Set 97% in blue and the other three in ink so the eye
lands there, and add a 20px caption under the row: "Ninety-seven percent approved, after
a wait that averages a week."

### Slide 3: The three eras
Carry this over from Round 1 with the same chevron device; it tested well.
**Visual** Three right-pointing chevrons, left to right, each 520px wide, 180px tall,
overlapping by 40px. Era 1 and 2 fill `#F2F7FC` with grey text; **Era 3 fills `#1274C4`
with white text**: the eras should visibly escalate. Number each chevron 1/2/3 in the
notch.
**Copy under each chevron** (three lines: name, mechanism, time)
| Era | Mechanism | Time |
|---|---|---|
| 1 · Fax and phone | A person starts it and a person resolves it | ~4 weeks |
| 2 · Digital portals | A person starts it, the portal assists | 3–14 days |
| 3 · Autonomous agents | Software starts it and resolves it | Under 5 min |
**Footer line** "Each era removed paperwork. Only the third removes the person from the
routine cases, so clinicians spend their time on the hard ones."

### Slide 4: The solution
**Layout** Title, then 2×2 grid of four quadrants divided by 1px rules.
**Copy** Title: "Era 3: Agent to Agent". Eyebrow: "SOLUTION".
| Quadrant | Heading | Body |
|---|---|---|
| 1 | Submitted automatically | Clinical documentation leaves the EHR directly. No staff touchpoint, no portal login. |
| 2 | Clear cases close in milliseconds | The full decision path takes 81.8ms, almost all of it the two signatures it writes. |
| 3 | Unclear cases escalate, assembled | A human reviewer opens a file that is already complete: records, rule, signature check, confidence score. |
| 4 | The doctor stays in charge | Medical necessity remains a physician's call. Only the administrative burden disappears. |
**Visual** One small line icon per quadrant, 64px, stroke `#1274C4`, 2px: an outbound
document, a stopwatch, a branch arrow, a stethoscope.

### Slide 5: How it works (System Architecture 2.0)
This is the most important visual in the deck. Reproduce the architecture diagram from the
Technical Execution Report; **do not design a new one**, so the two documents agree.
**Visual spec** Three labeled swim lanes, left to right:
- **THE DOCTOR'S SIDE**: steps 1–4 stacked: (1) The order is placed · (2) The name is
  removed · (3) The request is packaged into FHIR · (4) It is signed.
- **THE INSURER'S SIDE**: steps 5–7 stacked: (5) The signature is checked · (6) The rules
  are applied · (7) A decision comes out.
- **THE PERMANENT RECORD**: two tall boxes: "The audit trail" (five time-stamped entries
  per request) and "Nothing can be edited" (append-only; a regulator can reconstruct it).
Lane headers 18px bold letter-spaced in `#1274C4` with a 1px blue rule beneath.
Step boxes white, 1px `#8F8F8F` border, step number in blue bold, title in black bold,
body in 15px `#333333`.
**Step 5 is drawn differently**: fill `#F2F7FC`, border 2px `#1274C4`. It is a gate: if
the signature fails, the request is refused *before it is read*.
**Arrows** Grey `#777777` 1.1px between steps within a lane. **One blue 1.5px arrow** runs
from step 4 across to step 5; draw it as an orthogonal elbow (right, up, right), not a
diagonal. Caption it: "the only path that crosses between two organizations."
**Below the lanes**, a blue horizontal distribution line fanning down into three outcome
boxes: **Approved** (written straight back into the chart, no person involved) ·
**Unclear** (a human reviewer gets the assembled file) · **Denied** (appealed
automatically or sent to a person; *the software cannot issue a final denial by itself*).
Set the three outcome titles in `#1274C4` bold.
**Footer strip** "Typical time from step 1 to step 7: **81.8 milliseconds**, measured over
twenty consecutive runs."

### Slide 6: Current Traction  ← NEW, REQUIRED SLIDE
**This slide is the one the round explicitly asks for. It is about proof of progress, not
customers.** Lead with the honest framing so nobody thinks you are hiding a sales number.
**Layout** Title, a one-line honesty statement, then a left/right split: left = numbers,
right = evidence.
**Copy** Title: "What We Have Actually Built". Eyebrow: "CURRENT TRACTION".
Honesty line, 24px, directly under the title:
"No customers yet, and we are not going to pretend otherwise. What we have is working
software: every number on this slide came off the committed code, not a projection."
**Left panel**: a 2×3 grid of six stat tiles, numeral 72px blue bold, label 20px grey:
| 4 of 4 | phases built and running |
| 148 | automated tests, all passing |
| 22,459 | lines of code, 238 files |
| 16 | commits in 9 reviewed batches |
| 81.8 ms | end-to-end decision |
| 13 days | from first commit to working system |
**Right panel**: the commit history in a mono terminal block (grey `#F4F4F4` fill, 1px
`#CCCCCC` border, 16px mono), using the ten commits verbatim from section 3. Caption under
it in 16px italic: "Reviewed and merged in nine batches, 7-19 September 2026."
**Bottom strip across full width**: three short "what this proves" items separated by
vertical rules: "A tampered message is refused" · "An unmatched request goes to a human,
never a guess" · "Every decision names the rule that produced it", each followed by
"(covered by a test)" in 14px grey.

### Slide 7: The system running
**Layout** Two large screenshots side by side, captions beneath.
**Visual** Left: the six-step guided demonstration, completed. Right: the authorization
dashboard. Both at 1px `#BBBBBB` border, no shadow. Source images live in the repository at
`submission/assets/demo_complete_print.jpg` and `submission/assets/dashboard_print.jpg`.
**Captions** (18px italic)
- Left: "The guided demonstration after a single click. All six steps run with no further
  input and finish in about eleven seconds. The last step prices the same operation at
  five facilities: a spread of $2,475 for identical care."
- Right: "Every row carries the rule that produced it, in the RULE column. The single
  amber row is a knee replacement whose diagnosis did not match the covered condition. It
  is waiting for a human reviewer, with its file already assembled."
**Callout** Draw a thin blue leader line to the amber row and label it "escalation, not a
guess". That one row is the slide's argument.

### Slide 8: Trust, compliance and the human line
**Layout** Title, then a two-column split: left "What the software may decide", right
"What only a person may decide". Then a full-width strip of four compliance pills.
**Copy** Title: "The Safe Outcome Is the Default".
**Left column, fixed rules (decides)**: identity checks, coverage rules, price
arithmetic, denial-reason sorting. Guarantee: "Same input, same answer, every time, and
every answer names the exact rule behind it."
**Right column, AI models (assist only)**: reading insurance cards and benefit documents,
mapping plain English to a medical code, drafting appeal letters. Guarantee: "Every result
carries a confidence score. Below threshold it goes to a person."
**The single strongest line on the slide, set 32px bold, centered between the columns:**
"No AI language model ever decides an authorization."
**Bottom strip, four pills**, `#F2F7FC` fill, blue left border 3px:
- "Unmatched request → human reviewer, within 4 hours"
- "Appeal below 70% confidence → held for a person"
- "AI provider offline → authorization is unaffected"
- "Bias audit quarterly, by age, geography and diagnosis"
**Design note** Add a one-line consequence in 20px italic at the very bottom: "If our AI
vendor went down tomorrow, prior authorization would keep working: there is no model on
that path."

### Slide 9: What we have not solved
Keep this slide. Judges reward a team that names its own gaps, and it inoculates you
against the questions.
**Layout** Title, then a two-column table, 6 rows, 1px `#DCDCDC` row rules, no outer box.
**Copy** Title: "What We Have Not Solved". Subtitle: "These are real limitations of a
prototype. We would rather state them than be caught by them."
| Gap | What it needs |
|---|---|
| The privacy proof reveals which covered condition a patient has | A more advanced circuit. Scoped for the next phase. |
| The proof's setup was done on one machine | A proper multi-party ceremony before any real use |
| Provider identity is trusted, not verified | One integration against the federal provider registry |
| Facility prices are generated, not gathered | The voice agent, plus the price files insurers must now publish |
| Five coverage rules, not a rule library | Clinical staff encoding each insurer's criteria, our largest cost, and the real barrier to a competitor |
| The learning layer is not built | Deliberate. Until it exists, anything without a definitive rule goes to a person |
**Design note** Set the last cell's final clause in blue: the admission is also the moat.

### Slide 10: Competition
**Replace Round 1's 0–100 bar chart.** Scoring competitors 100 vs 50 on "Speed of Request"
is not defensible and a judge will ask where the 50 came from.
**Visual** A capability matrix instead. Rows = capabilities, columns = Pavo Cloud / Cohere
Health / Availity AuthAI. Cells are **✓ (blue, filled)**, **partial (hollow blue circle)**
or **· (grey dot)**. Header row in blue bold, 1px `#555555` under it; 1px `#DCDCDC`
between rows; 1px black under the table. Pavo's column gets a `#F2F7FC` wash so it reads
first.
| Capability | Pavo | Cohere | Availity |
|---|---|---|---|
| Software can start a request with no human | ✓ | · | · |
| Decision without a human in the loop for clear cases | ✓ | · | · |
| Cryptographic sender verification | ✓ | partial | partial |
| FHIR R4 native | ✓ | ✓ | ✓ |
| Human review path for unclear cases | ✓ | ✓ | ✓ |
| Zero-knowledge patient privacy proof | ✓ | · | · |
**Copy** Title: "Everyone Else Still Waits for a Person". Under the matrix, one 26px line:
"The incumbents digitized the paperwork. We removed the requirement that a person start
the request at all, which is why the comparison is a category difference, not a
percentage."
**Rule** If you cannot substantiate a row for a competitor from public material, delete the
row. A short honest matrix beats a long unverifiable one.

### Slide 11: Market
**Visual** Three concentric arcs or three nested bars, left to right, largest to smallest, **not** a pie. Label each with figure, name and one qualifier.
| Tier | Figure | Qualifier |
|---|---|---|
| TAM | $35B / yr | total US spend on prior authorization today |
| SAM | $6.2B by 2033 | the portion addressable once CMS mandates FHIR APIs |
| SOM | $45.3M by 2028 | mid-sized payers and their provider groups |
**Copy** Title: "A Market a Regulation Is About to Create". Add a source line in 14px under
each figure; see hard rule 6.
**Design note** Put your own 2028 plan ($36.1M revenue) as a small marker inside the SOM
band so the ambition is visibly bounded by the model. Judges like a TAM slide that
constrains itself.

### Slide 12: Why now
**Layout** Three columns under a single spine line, each headed by a 64px line icon.
**Copy** Title: "The Law Builds Our Rails".
| Column | Heading | Body |
|---|---|---|
| 1 | Federal mandate | CMS-0057-F requires FHIR-based prior-auth APIs by 1 January 2027. Every payer has a deadline. |
| 2 | AI inflection | Agents now need a way to *initiate* authorizations. Pavo is that rail. |
| 3 | Scale already exists | 47M payer–provider interactions a year, still moving through portals and fax. |
**Bottom band, full width, `#F2F7FC`** with the argument in 30px:
"The mandate is not a risk to us. It is a forcing function that puts a FHIR endpoint at
every payer in the country, and we are already built against it."

### Slide 13: Business model
**Layout** Three price cards, equal width, 1px border, blue header band.
| Card | Price | Who | Why it sticks |
|---|---|---|---|
| Per authorization | $3.00 | both sides | 85–92% below the $15–$40 an insurer spends handling one by hand |
| Practice subscription | $400 / month | provider groups | the daily pain: denials and staff overhead |
| Compliance API | $20,000 / year | insurers | legally required from 2027, no internal engineering lift |
**Below the cards**, one line of unit-economics proof, 26px:
"Cost to process one request: about six hundredths of a cent. The deciding path runs no AI
models at all."
**Design note** Add a small honest aside, 18px italic: "Insurer contracts return $2.30 per
$1 spent acquiring them and take 15 months to pay back. We fund them anyway: signing one
insurer makes Pavo available to every practice that already submits to it. It is a
distribution channel, not a profit centre."

### Slide 14: Go-to-market
**Visual** Horizontal timeline, three numbered nodes on a single 2px blue spine.
| Node | Period | Bullets |
|---|---|---|
| 1 | 2026 Launch | Onboard provider groups · close first payer contracts · reach $1.0M revenue |
| 2 | Jan 2027 Mandate | CMS rule takes effect · every payer must expose FHIR APIs · Pavo is already integrated, so the deadline becomes a distribution event |
| 3 | 2027–28 Scale | $8.2M → $36.1M · deepen payer and provider adoption |
**Below**, three short rationale blocks: "Provider-led entry" (sign practices first,
generate the data and the demand that pulls payers in) · "Regulatory tailwind" (the
deadline does our prospecting) · "Compounding scale" (every authorization adds volume,
improving unit economics).

### Slide 15: Financials
**Layout** Left two-thirds: revenue column chart. Right third: unit-economics table.
**Chart spec** Vertical bars, three columns, y-axis 0–$40M with gridlines at $10M
intervals in `#DCDCDC`. Bars `#1274C4`, 160px wide. Data labels above each bar in bold.
| Year | Revenue |
|---|---|
| 2026 | $1.0M |
| 2027 | $8.2M |
| 2028 | $36.1M |
Under the chart, a second row of three small labels showing gross margin per year:
**31% · 82% · 87%**, with a 16px note: "Year 1 is 31%, not break-even: early customers
need a great deal of hand-holding."
**Right table** (no outer box, blue header, 1px row rules)
| Metric | Practice | Insurer | Blended |
|---|---|---|---|
| CAC | $6,000 | $22,000 | $6,699 |
| 3-year LTV | $58,248 | $51,057 | $57,533 |
| LTV:CAC | 9.7× | 2.3× | 8.6× |
| Payback | 3.5 mo | 15.2 mo | 4.0 mo |
**Footer line, 18px italic** "Downside case: if all four of our main assumptions are wrong
at once, 2028 revenue is $13.8M rather than $36.1M: a smaller company, but still a real
one."

### Slide 16: The ask
**Layout** One huge figure, then the justification, then three allocation bars.
**Copy** Title: "We Are Raising $8.0 Million".
Figure 160px bold blue: **$8.0M**
Directly beneath, 28px: "Peak cumulative burn is $5.58M in late 2027. Eight million covers
it with roughly twelve months of cushion past breakeven."
**Visual, a burn curve, not a pie.** A small line chart: cumulative EBITDA across 2026–28,
plotted at −$2.37M, −$5.58M, +$5.64M. Shade the area below zero `#F2F7FC`. Mark the
trough with a blue dot labeled "$5.58M, late 2027" and mark the zero crossing "breakeven".
Overlay a horizontal dashed line at −$8.0M labeled "raise". **This single chart justifies
the number better than any allocation pie.**
**Three priority blocks below** (what the money de-risks, in order; describe them as priorities,
never as a budget that sums to $8M):
1. **The clinical rule library**: our largest cost and the real barrier to a competitor
2. **Security certification**: no insurer signs without it
3. **Closing the gaps on slide 9**: provider registry, multi-party ceremony, rule library

### Slide 17: Close
**Copy** Title: "Why Pavo Wins". Three stacked one-liners, 40px, each with a blue rule:
- "Regulation is the tailwind: every payer has a January 2027 deadline."
- "Ten times better, not ten percent: we removed the person from the start of the process."
- "Timing is the moat: trust networks between payers and providers take years to build."
**Closing line**, 30px centered: "The software works today. The deadline is in fifteen
months. We are asking for the capital to be the default before the market consolidates."

### Appendix A: Measured performance
The five-row performance table from section 3, plus the methodology note: "measured over
twenty consecutive runs against the committed code on 13 September 2026."

### Appendix B: Full revenue build
The seven-row revenue table from section 3.

### Appendix C: Risk register
The eight-row failure table: what happens when a rule does not match, a message is
tampered with, an appeal scores low, the AI provider goes offline, the literature service
is unreachable, an appeal is rejected, approval rates drift by demographic, each with the
automatic action and who gets involved.

## 6. Build instructions

1. Build each slide as a fixed 1920×1080 container. No slide may overflow; if copy does not
   fit, cut copy; do not shrink type below the sizes in section 4.
2. Charts: draw as inline SVG, not images, so they stay sharp. No chart library chrome, no
   legends where direct labels will do, no 3D, no rounded bar caps.
3. Render to a single PDF, one page per slide, 16:9, and verify the page count is 19.
4. Check every figure against section 3 one final time before you export. Any number that
   does not appear in section 3 should not appear in the deck.

## 7. Self-check before you hand it back

- [ ] Every speed claim distinguishes agent latency (81.8ms) from end-to-end (<5 min)
- [ ] Year 1 margin stated as 31%, never as break-even
- [ ] No fabricated customers, pilots, LOIs or revenue anywhere
- [ ] No use-of-funds figure or chart sums to more than $8.0M
- [ ] Every carried-over market statistic has a source line, or was cut
- [ ] Every number matches the number sheet in section 3
- [ ] Slide 6 (Current Traction) exists and leads with the honesty line
- [ ] Architecture diagram matches the Technical Execution Report, not a redesign
- [ ] 19 pages, 16:9, nothing overflowing
