Rebuild my existing 10-slide Pavo Cloud pitch deck into a 16-slide deck. Keep every
visual decision from the current deck exactly as it is. I am fixing content, not
redesigning. Six slides need specific corrections, four need source lines, and six
new slides need to be built in the same style.

## DESIGN SYSTEM: match the existing slides exactly, do not invent a new look

Colours, used verbatim:
- Page background: #FFFAFA (warm off-white, never pure white, never a gradient)
- Headings and big numerals: #1F1E1E
- Body text, bylines, table cells: #3A3535
- Soft accent fill, used for the small label chip at the top of a slide: #D6DCF4
- Hairline rules and table borders: #9C9797 at 1px
- Data accent, for the one number per slide that matters and for table headers: #1274C4

Type: one geometric sans throughout (Poppins, or the closest Gamma has). Slide titles
bold and large. Section label chips in ALL CAPS, ~11px, letter-spaced, sitting in a
#D6DCF4 pill. Body copy regular weight, generous line height.

Layout: left-aligned, never centred. Very generous whitespace, because the current deck breathes
and that is the point. One idea per slide. Thin horizontal rule to separate a title block
from content where the current deck does that. No drop shadows, no gradients, no stock
photography, no 3D icons. Flat line icons only, in #1274C4, if any.

Writing rules, applied to every slide:
- No em dashes anywhere. Use a comma, colon, semicolon or full stop.
- En dashes are fine in number ranges (3–14 days, 85–92%).
- Never round a number up. 88.6 milliseconds is not "under 50ms".
- Every speed claim must distinguish agent latency (88.6ms) from the end-to-end round
  trip (under five minutes). Never imply a patient gets an answer in 89 milliseconds.
- American spelling (authorization, not authorisation).
- Any statistic about the outside world carries a visible source line in 12px #9C9797
  under the slide. If there is no source, cut the statistic.

## THE NUMBER SHEET: use these exact values, do not recompute or restate in other units

Measured on the committed code at commit 0a24def, 20 September 2026:
| Complete authorization decision, start to finish | 88.6 milliseconds (median, n=200) |
| One RSA-2048 signature, of the two every decision needs | 42.0 milliseconds |
| Checking a signature | 0.05 milliseconds |
| Creating one zero-knowledge privacy proof | 401 milliseconds |
| Full six-step guided demonstration | 11.0 seconds |
| Automated tests passing | 148 of 148 |

Build, through commit 0a24def:
| Commits | 18, in 11 reviewed batches |
| File changes | 260 |
| Lines added | 22,739 insertions, 1,215 deletions |
| Hand-written | 15,871 of those insertions; the rest is a dependency lockfile |
| Phases complete | 4 of 4 |
| Build window | 7–19 September 2026 |

Three-year financials:
| Practices served (average) | 55 | 330 | 1,400 |
| Insurers connected (average) | 11 | 84 | 160 |
| Requests processed | 171,600 | 1,647,360 | 8,736,000 |
| Fees per request, at $3.00 | $514,800 | $4,942,080 | $26,208,000 |
| Practice subscriptions, at $400/month | $264,000 | $1,584,000 | $6,720,000 |
| Insurer connection fees, at $20,000/year | $220,000 | $1,680,000 | $3,200,000 |
| Total revenue | $998,800 | $8,206,080 | $36,128,000 |
| Gross profit | $310,800 | $6,713,080 | $31,366,000 |
| Gross margin | 31% | 82% | 87% |

Unit economics at 2028 rates:
| Cost to acquire one customer | $6,000 practice | $22,000 insurer | $6,699 blended |
| Value over three years | $58,248 | $51,057 | $57,533 |
| Value per $1 spent acquiring | $9.70 | $2.30 | $8.60 |
| Months to earn the cost back | 3.5 | 15.2 | 4.0 |

The raise: $8.0 million. Losses of $2.37M in 2026 and $3.21M in 2027, then $11.23M of
profit in 2028. Deepest point is $5.58M of cumulative losses, in late 2027.

## PART 1: CORRECTIONS TO EXISTING SLIDES

**Slide 1, Title.** Change the subtitle line. It currently reads "The insurer's answer in
88.6 milliseconds. The whole round trip in under five minutes, not three days." Replace
"not three days" with "not three to fourteen days". Everything else on this slide stays.

**Slide 2, Prior Authorization Is Broken.** Keep the four stat tiles. Add a source line
under the row in 12px #9C9797 citing where "94% of doctors report delays" and "97% of
requests approved" come from (AMA prior authorization physician survey, and the KFF
Medicare Advantage prior authorization analysis). If either cannot be sourced, delete
that tile and run three tiles instead. "3–14 days" and "$35B" stay as they are.

**Slide 4, Era 3: Agent to Agent.** The second bullet currently reads "The two agents
agree in 44.7ms; the full decision path takes 88.6ms." Delete the 44.7ms claim entirely.
It was measured over a loopback interface, so "network excluded" meant nothing, and it
does not appear in the technical report. Replace the bullet body with:

  "The full decision path takes 88.6 milliseconds, and 84.0 of those are the two
  RSA-2048 signatures every authorization writes. The deciding itself is the cheap part."

The other three bullets on this slide are correct and stay.

**Slide 5, System Architecture.** Two fixes on the speed line. It currently reads
"Speed: Step 1→7 in 88.6ms (avg, n=20)". Change it to:

  "Speed: step 1 to step 7 in 88.6ms (median, n=200)"

Also change "Supabase" in the stack line to "Supabase-ready". The service supports it,
but the running demonstration stores state in memory unless a Supabase URL is configured,
and claiming otherwise invites a question we would lose.

**Slide 8, What We Have Not Solved.** The technical report discloses six gaps and this
slide shows four. Add the two missing rows so the deck and the report agree:

  | Facility prices are generated, not gathered | The voice agent that calls facilities,
    plus the price files insurers must now publish. |
  | The learning layer is not built | Deliberate. Until it exists, anything without a
    definitive rule goes to a person, which is the correct default anyway. |

Keep the existing four rows exactly as written.

**Slide 9, Everyone Else Still Waits for a Person.** Keep the comparison table. Add a
source line in 12px #9C9797 naming where the Cohere Health and Availity AuthAI
capabilities were read from, with the date they were checked. Any cell that cannot be
sourced becomes a grey dot, not a claim.

**Slide 10, A Market a Regulation Is About to Create.** Keep all three points. Add source
lines: CMS-0057-F for the January 1 2027 FHIR prior-authorization API mandate, and the
CAQH Index for the 47M payer-provider interactions figure.

## PART 2: SIX NEW SLIDES, BUILT IN THE SAME STYLE

**New slide, place after System Architecture. Title: "What We Actually Built".**
Label chip: EVIDENCE. Left two thirds is a 2x3 grid of stat tiles, numeral 72px bold in
#1274C4, label 20px #3A3535 beneath:
  4 of 4 / phases built and running
  148 / automated tests, all passing
  18 / commits in 11 reviewed batches
  22,739 / lines added across 260 files
  88.6 ms / end-to-end decision
  13 days / from first commit to working system
Right third is a monospace terminal block, #F4F4F4 fill with a 1px #CCCCCC border, 14px
mono, showing the last six commit subjects. Caption under it, 14px italic #3A3535:
"Reviewed and merged in eleven batches, 7 to 19 September 2026." Add one line across the
bottom: "Every number on this slide comes off the committed code, not a projection."

**New slide, immediately after. Title: "The System Running".**
Label chip: LIVE SOFTWARE. Two screenshots side by side at equal height, thin #9C9797
border on each, no shadows. Left is the guided demonstration after a single click. Right
is the authorization dashboard. One caption spanning both, 14px italic #3A3535:
"Left: all six steps, order through price, run with no further input and finish in 11.0
seconds. Right: every row carries the rule that produced it; the two amber rows are knee
replacements whose diagnosis did not match the covered condition, and both wait for a
human reviewer with the file already assembled." Leave both image frames empty for me to
drop the screenshots into.

**New slide, place after the competitor slide. Title: "How Pavo Makes Money".**
Label chip: BUSINESS MODEL. Top: three revenue lines as three equal cards, each with the
price in 40px #1274C4 bold and a one-line explanation:
  $3.00 per request, charged to the insurer
  $400 per month, per medical practice
  $20,000 per year, per insurer connection
Below: the full revenue table, 2026 / 2027 / 2028, headers in #1274C4 bold, 1px #9C9797
rules, total row in bold with a heavier top rule. Bottom line, 16px:
"The $3.00 fee is 85–92% below the $15–$40 an insurer spends handling a request by hand
today, which is what makes the switch easy to justify."

**New slide, immediately after. Title: "What It Costs, and What Is Left".**
Label chip: MARGIN. Three large tiles across the top: 31% / 82% / 87% in 72px #1274C4
with 2026 / 2027 / 2028 beneath. Under them, two short paragraphs:
"Servers are not the expense. Processing one request costs about six hundredths of a cent,
because the deciding path uses no AI models at all."
"The real cost is clinical staff translating each insurer's published rules into the fixed
rules the software applies. That is the largest line in every year, and the reason margins
improve with scale rather than with technology."
Add one honest note in 14px #3A3535: "Year 1 is 31%, not break-even. Early customers need
a great deal of hand-holding."

**New slide, immediately after. Title: "Cost to Win a Customer, and What One Is Worth".**
Label chip: UNIT ECONOMICS. The four-row unit economics table, columns Practice / Insurer
/ Blended, headers #1274C4 bold. Above it, one line defining the terms: "Acquisition cost
is what it costs in sales and marketing to sign one customer. Lifetime value is the profit
that customer produces before they leave, stated here over three years, which is
deliberately conservative." Below it, in a #D6DCF4 panel:
"Read the insurer column honestly. At $2.30 back per $1 spent and fifteen months to
recover it, insurer contracts do not pay for themselves as a product. We fund them anyway,
because signing one insurer makes Pavo available to every practice that already submits to
it. It is a distribution channel, not a profit centre."

**New slide, immediately after. Title: "We Are Asking For $8.0 Million".**
Label chip: THE ASK. Left half: a small line chart of cumulative cash, dipping to
-$5.58M in late 2027 and crossing zero during 2028, drawn as a single #1274C4 line on
#FFFAFA with a #9C9797 zero axis. Label the trough "$5.58M, late 2027". Not a pie chart.
Right half: three priority blocks, each with a #1274C4 left rule, describing what the
raise funds and in what order:
  The start of the clinical rule library
  The security certification no insurer will sign without
  The engineering that closes the gaps on the limitations slide
Under them, 14px: "$8.0 million covers that trough with roughly twelve months of cushion
past breaking even. It is not a shopping list. The three largest spending lines across the
plan, $7.46M of engineering, $5.67M of insurer business development and $1.72M of clinical
staff encoding coverage rules, come to more than the raise on their own, and most of that
is paid for out of revenue as it arrives."
Bottom line in 14px #3A3535: "If all four of our main assumptions are wrong at once, 2028
revenue is $13.8 million rather than $36.1 million: a smaller company, but still a real
one."

## PART 3: FINAL SLIDE ORDER

1. Pavo Cloud (title, corrected)
2. Prior Authorization Is Broken (sourced)
3. The Three Eras of Prior Authorization
4. Era 3: Agent to Agent (44.7ms removed)
5. System Architecture (median n=200, Supabase-ready)
6. What We Actually Built (new)
7. The System Running (new)
8. Customer Discovery and Validation (existing traction slide, unchanged)
9. The Safe Outcome Is the Default
10. What We Have Not Solved (six gaps)
11. Everyone Else Still Waits for a Person (sourced)
12. A Market a Regulation Is About to Create (sourced)
13. How Pavo Makes Money (new)
14. What It Costs, and What Is Left (new)
15. Cost to Win a Customer, and What One Is Worth (new)
16. We Are Asking For $8.0 Million (new)

Do not change slides 3, 8 or 9 in this final order beyond what is written above. Do not
add slides I have not asked for. Do not restate any number in different units than the
number sheet gives.
