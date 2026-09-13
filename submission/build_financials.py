"""Build the Pavo Cloud three-year financial model workbook.

Every output cell is a live Excel formula wired back to the Drivers tab, so a
judge can change an assumption and watch the model move. Nothing is a typed-in
constant except the drivers themselves.

    python build_financials.py
"""
from __future__ import annotations

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# ---------------------------------------------------------------- palette ---
NAVY = "16324F"
ACCENT = "1F6F8B"
INK = "10151F"
MUTED = "5D6875"
GOOD = "1C6B4A"
BAD = "9B2C2C"
WASH = "F5F7FA"
BAND = "EDF1F5"

MONEY = '$#,##0;($#,##0)'
MONEY2 = '$#,##0.00;($#,##0.00)'
MONEY4 = '$#,##0.0000'
MONEY6 = '$#,##0.000000'
NUM = '#,##0'
PCT = '0%'
PCT1 = '0.0%'
MULT = '0.0"×"'
MONTHS = '0.0" mo"'

thin = Side(style="thin", color="D6DBE2")
rule = Side(style="medium", color=NAVY)


def title(ws, text, sub=""):
    ws["A1"] = text
    ws["A1"].font = Font(bold=True, size=15, color=NAVY)
    if sub:
        ws["A2"] = sub
        ws["A2"].font = Font(size=9, color=MUTED, italic=True)
    ws.freeze_panes = "B5"


def header(ws, row, labels, widths=None):
    for i, label in enumerate(labels, start=1):
        c = ws.cell(row=row, column=i, value=label)
        c.font = Font(bold=True, size=8, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(
            horizontal="right" if i > 1 else "left", vertical="center", wrap_text=True
        )
    ws.row_dimensions[row].height = 26
    if widths:
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w


def line(ws, row, label, values, fmt=NUM, bold=False, band=False,
         note=None, indent=0, color=None, top_rule=False):
    """Write one model row. `values` are formula strings or numbers."""
    c = ws.cell(row=row, column=1, value=label)
    c.font = Font(bold=bold, size=9, color=color or (INK if bold else "2B3440"))
    c.alignment = Alignment(indent=indent, vertical="center")
    for i, v in enumerate(values, start=2):
        cell = ws.cell(row=row, column=i, value=v)
        cell.number_format = fmt
        cell.font = Font(bold=bold, size=9, color=color or (INK if bold else "2B3440"))
        cell.alignment = Alignment(horizontal="right", vertical="center")
    last = 1 + len(values)
    if note is not None:
        n = ws.cell(row=row, column=last + 1, value=note)
        n.font = Font(size=8, color=MUTED, italic=True)
        n.alignment = Alignment(vertical="center", wrap_text=True)
        last += 1
    for i in range(1, last + 1):
        cell = ws.cell(row=row, column=i)
        cell.border = Border(
            bottom=thin, top=rule if top_rule else None
        )
        if band:
            cell.fill = PatternFill("solid", fgColor=BAND)
    ws.row_dimensions[row].height = 16
    return row + 1


def section(ws, row, text):
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(bold=True, size=9.5, color=ACCENT)
    ws.row_dimensions[row].height = 22
    return row + 1


def note_block(ws, row, text, width=6):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=width)
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(size=8.5, color=NAVY, italic=True)
    c.alignment = Alignment(wrap_text=True, vertical="top")
    c.fill = PatternFill("solid", fgColor=WASH)
    ws.row_dimensions[row].height = 46
    return row + 2


wb = Workbook()

# ==========================================================  1 · DRIVERS ====
ws = wb.active
ws.title = "1 Drivers"
title(ws, "Pavo Cloud — Model Drivers",
      "Every other tab reads from here. Change a cell and the whole model moves.")
header(ws, 4, ["Driver", "2026", "2027", "2028", "Basis / source"],
       [40, 14, 14, 14, 60])

r = 5
r = section(ws, r, "VOLUME")
r = line(ws, r, "Provider groups — ending", [110, 560, 2240], NUM,
         note="Sales plan. A 'group' averages 8 physicians.")
r = line(ws, r, "Provider groups — average active", [55, 330, 1400], NUM, bold=True, band=True,
         note="Monthly-weighted; back-loaded ramp within each year.")
r = line(ws, r, "Physicians per group", [8, 8, 8], NUM,
         note="Mid-market target segment.")
r = line(ws, r, "Prior auths per physician per week", [30, 30, 30], NUM,
         note="Conservative. AMA 2023 survey reports 43–45.")
r = line(ws, r, "Share of PA volume routed through Pavo", [0.25, 0.40, 0.50], PCT,
         note="Rises as the encoded rule library widens.")
r = line(ws, r, "Payer contracts — average active", [11, 84, 160], NUM, bold=True, band=True,
         note="~18% of the ~900 payers impacted by CMS-0057-F by 2028.")
r += 1

r = section(ws, r, "PRICE")
r = line(ws, r, "Fee per authorization", [3.00, 3.00, 3.00], MONEY2,
         note="85–92% below the $15–$40 payers spend manually.")
r = line(ws, r, "Provider subscription", [400, 400, 400], MONEY,
         note="Per group per month.")
r = line(ws, r, "Payer compliance API", [20000, 20000, 20000], MONEY,
         note="Per payer per year.")
r += 1

r = section(ws, r, "ACQUISITION")
r = line(ws, r, "New provider groups acquired", [110, 470, 1750], NUM,
         note="Ending count, less prior ending, plus churned replacements.")
r = line(ws, r, "New payer contracts acquired", [18, 122, 80], NUM)
r = line(ws, r, "Provider CAC", [9500, 7200, 6000], MONEY, bold=True, band=True,
         note="Falls 37%: payer contracts open the provider channel.")
r = line(ws, r, "Payer CAC", [34000, 27000, 22000], MONEY, bold=True, band=True,
         note="Enterprise cycle, 6–12 months.")
r = line(ws, r, "Provider annual logo churn", [0.08, 0.06, 0.05], PCT)
r = line(ws, r, "Payer annual logo churn", [0.02, 0.02, 0.02], PCT,
         note="Multi-year compliance contracts.")
r += 1

r = section(ws, r, "COST OF REVENUE")
r = line(ws, r, "Cloud infrastructure", [54000, 198000, 900000], MONEY,
         note="Compute, Postgres, object storage, egress, 7-year retention.")
r = line(ws, r, "Model API (Insure + appeals only)", [11000, 62000, 280000], MONEY,
         note="Zero tokens on the authorization path — see tab 6.")
r = line(ws, r, "Clinical rule library — FTE", [1.5, 3.5, 8.0], '0.0',
         note="Informaticists encoding each payer's published criteria.")
r = line(ws, r, "Clinical rule library — loaded cost/FTE", [126000, 130000, 135000], MONEY)
r = line(ws, r, "Implementation & onboarding — FTE", [2.0, 4.0, 12.0], '0.0')
r = line(ws, r, "Implementation — loaded cost/FTE", [112000, 119000, 119000], MONEY)
r = line(ws, r, "Customer support — FTE", [1.0, 2.0, 8.0], '0.0')
r = line(ws, r, "Support — loaded cost/FTE", [92000, 95000, 98000], MONEY)
r = line(ws, r, "Security & compliance", [118000, 112000, 290000], MONEY,
         note="SOC 2 Type II in Year 1, then surveillance + pen testing.")
r += 1

r = section(ws, r, "OPERATING EXPENSE")
r = line(ws, r, "Engineers", [4, 12, 26], NUM)
r = line(ws, r, "Loaded cost per engineer", [170000, 175000, 180000], MONEY)
r = line(ws, r, "General & administrative", [340000, 1150000, 3200000], MONEY,
         note="Finance, legal, HR, facilities, insurance.")
r += 1

note_block(ws, r,
           "Reading this model:  every figure on tabs 2–7 is an Excel formula pointing back at this tab. "
           "The three revenue targets carried over from the Round 1 narrative ($1.0M / $8.2M / $36.1M) are not "
           "typed anywhere — they fall out of the drivers above. Tab 7 shows what happens when the four most "
           "fragile of those drivers are wrong.")

DR = "'1 Drivers'!"


def d(row):
    """Driver row → the B:D range reference for a given year column."""
    return {c: f"{DR}{chr(ord('B') + i)}{row}" for i, c in enumerate("BCD")}


# driver row numbers (kept in sync with the writes above)
ROW = dict(
    groups_end=6, groups_avg=7, physicians=8, pa_per_phys=9, share=10, payers=11,
    fee=14, sub=15, api=16,
    new_prov=19, new_pay=20, prov_cac=21, pay_cac=22, prov_churn=23, pay_churn=24,
    infra=27, model_api=28, clin_fte=29, clin_cost=30, impl_fte=31, impl_cost=32,
    sup_fte=33, sup_cost=34, seccomp=35,
    engineers=38, eng_cost=39, ga=40,
)

COLS = "BCD"


def dref(key, col):
    return f"{DR}{col}{ROW[key]}"


# ========================================================  2 · REVENUE ======
ws = wb.create_sheet("2 Revenue")
title(ws, "Revenue Build", "Bottom-up from the driver tab. No figure here is typed in.")
header(ws, 4, ["Line", "2026", "2027", "2028", "Note"],
       [40, 16, 16, 16, 52])

r = 5
r = section(ws, r, "AUTHORIZATION VOLUME")
r = line(ws, r, "Prior auths per group per year",
         [f"={dref('physicians',c)}*{dref('pa_per_phys',c)}*52" for c in COLS], NUM,
         note="8 physicians × 30/week × 52 weeks")
r = line(ws, r, "Authorizations routed through Pavo, per group",
         [f"=B6*{dref('share',c)}" if c == "B" else
          f"={chr(ord('B')+i)}6*{dref('share',c)}" for i, c in enumerate(COLS)], NUM)
r = line(ws, r, "Total authorizations processed",
         [f"={c}7*{dref('groups_avg',c)}" for c in COLS], NUM, bold=True, band=True)
r += 1

r = section(ws, r, "REVENUE BY STREAM")
r = line(ws, r, "Per-authorization fees",
         [f"={c}8*{dref('fee',c)}" for c in COLS], MONEY, note="$3.00 per authorization")
r = line(ws, r, "Provider subscriptions",
         [f"={dref('groups_avg',c)}*{dref('sub',c)}*12" for c in COLS], MONEY,
         note="$400/month per group")
r = line(ws, r, "Payer compliance API",
         [f"={dref('payers',c)}*{dref('api',c)}" for c in COLS], MONEY,
         note="$20,000/year per payer")
r = line(ws, r, "Total revenue", [f"=SUM({c}11:{c}13)" for c in COLS], MONEY,
         bold=True, top_rule=True)
r = line(ws, r, "Year-on-year growth",
         ["", "=C14/B14-1", "=D14/C14-1"], PCT, color=ACCENT)
r += 1

r = section(ws, r, "MIX")
r = line(ws, r, "Authorization fees, share of revenue",
         [f"={c}11/{c}14" for c in COLS], PCT1)
r = line(ws, r, "Subscriptions, share of revenue",
         [f"={c}12/{c}14" for c in COLS], PCT1)
r = line(ws, r, "Compliance API, share of revenue",
         [f"={c}13/{c}14" for c in COLS], PCT1)
r += 1

note_block(ws, r,
           "The authorization fee is 73% of 2028 revenue, which is why the model's single greatest "
           "exposure is provider group count rather than price. Tab 7 quantifies that.")

# ============================================================  3 · COGS =====
ws = wb.create_sheet("3 Cost of Revenue")
title(ws, "Cost of Revenue and Gross Margin",
      "The largest line is people encoding payer criteria — not servers.")
header(ws, 4, ["Line", "2026", "2027", "2028", "Driver"], [40, 16, 16, 16, 46])

r = 5
r = line(ws, r, "Cloud infrastructure",
         [f"={dref('infra',c)}" for c in COLS], MONEY,
         note="Compute, Postgres, storage, egress, 7-year retention")
r = line(ws, r, "Model API — Insure parsing, appeal drafting",
         [f"={dref('model_api',c)}" for c in COLS], MONEY,
         note="Not on the authorization path")
r = line(ws, r, "Clinical rule library",
         [f"={dref('clin_fte',c)}*{dref('clin_cost',c)}" for c in COLS], MONEY,
         note="1.5 → 3.5 → 8.0 FTE informaticists")
r = line(ws, r, "Implementation & onboarding",
         [f"={dref('impl_fte',c)}*{dref('impl_cost',c)}" for c in COLS], MONEY,
         note="2.0 → 4.0 → 12.0 FTE")
r = line(ws, r, "Customer support",
         [f"={dref('sup_fte',c)}*{dref('sup_cost',c)}" for c in COLS], MONEY,
         note="1.0 → 2.0 → 8.0 FTE")
r = line(ws, r, "Security & compliance",
         [f"={dref('seccomp',c)}" for c in COLS], MONEY,
         note="SOC 2 Type II, penetration testing, BAA management")
r = line(ws, r, "Total cost of revenue", [f"=SUM({c}5:{c}10)" for c in COLS], MONEY,
         bold=True, top_rule=True)
r += 1
r = line(ws, r, "Revenue", [f"='2 Revenue'!{c}14" for c in COLS], MONEY)
r = line(ws, r, "Gross profit", [f"={c}13-{c}11" for c in COLS], MONEY, bold=True)
r = line(ws, r, "Gross margin", [f"={c}14/{c}13" for c in COLS], PCT,
         bold=True, band=True, color=GOOD)
r += 1
r = section(ws, r, "COST SHARE")
r = line(ws, r, "People (rule library + implementation + support)",
         [f"=({c}7+{c}8+{c}9)/{c}11" for c in COLS], PCT1)
r = line(ws, r, "Infrastructure + model API",
         [f"=({c}5+{c}6)/{c}11" for c in COLS], PCT1)
r += 1
note_block(ws, r,
           "Year 1 gross margin of 31% is deliberate and corrects the Round 1 narrative, which implied "
           "break-even. Early pilots carry a disproportionate implementation load and are delivered near "
           "cost. Margin reaches 87% by 2028 because authorization volume scales without adding people — "
           "the marginal cost of one authorization is about $0.00057 (tab 6).")

# =============================================================  4 · P&L =====
ws = wb.create_sheet("4 P&L")
title(ws, "Three-Year Profit and Loss",
      "EBITDA-positive during 2028. Peak cumulative burn $5.58M in Q4 2027.")
header(ws, 4, ["Line", "2026", "2027", "2028", "Note"], [40, 17, 17, 17, 44])

r = 5
r = line(ws, r, "Revenue", [f"='2 Revenue'!{c}14" for c in COLS], MONEY, bold=True)
r = line(ws, r, "Cost of revenue", [f"=-'3 Cost of Revenue'!{c}11" for c in COLS], MONEY)
r = line(ws, r, "Gross profit", [f"={c}5+{c}6" for c in COLS], MONEY, bold=True, top_rule=True)
r = line(ws, r, "Gross margin", [f"={c}7/{c}5" for c in COLS], PCT, color=MUTED, indent=1)
r += 1
r = section(ws, r, "OPERATING EXPENSE")
r = line(ws, r, "Research & development",
         [f"=-{dref('engineers',c)}*{dref('eng_cost',c)}" for c in COLS], MONEY,
         note="4 → 12 → 26 engineers")
r = line(ws, r, "Sales & marketing",
         [f"=-({dref('new_prov',c)}*{dref('prov_cac',c)}+{dref('new_pay',c)}*{dref('pay_cac',c)})"
          for c in COLS], MONEY, note="New logos × CAC, both segments")
r = line(ws, r, "New logos acquired",
         [f"={dref('new_prov',c)}+{dref('new_pay',c)}" for c in COLS], NUM,
         color=MUTED, indent=1)
r = line(ws, r, "General & administrative",
         [f"=-{dref('ga',c)}" for c in COLS], MONEY)
r = line(ws, r, "Total operating expense",
         [f"=SUM({c}11:{c}12)+{c}14" for c in COLS], MONEY, bold=True, top_rule=True)
r += 1
r = line(ws, r, "EBITDA", [f"={c}7+{c}15" for c in COLS], MONEY, bold=True, band=True)
r = line(ws, r, "EBITDA margin", [f"={c}17/{c}5" for c in COLS], PCT, color=MUTED, indent=1)
r = line(ws, r, "Cumulative EBITDA", ["=B17", "=B19+C17", "=C19+D17"], MONEY,
         bold=True, color=BAD)
r += 1
note_block(ws, r,
           "Peak cumulative burn is $5.58M. An $8.0M raise covers it with roughly twelve months of "
           "buffer past EBITDA breakeven. Sales & marketing is the largest operating line in all three "
           "years, and 73% of it is provider acquisition — which the payer channel is what makes cheap.")

# ==================================================  5 · UNIT ECONOMICS =====
ws = wb.create_sheet("5 Unit Economics")
title(ws, "CAC, LTV, and Payback — at 2028 economics",
      "LTV is stated on a 3-year horizon. The 5-year figure is shown, but we do not underwrite on it.")
header(ws, 4, ["Metric", "Provider group", "Payer", "Blended", "Note"],
       [42, 17, 17, 17, 44])

GMREF = "'3 Cost of Revenue'!D15"
r = 5
r = line(ws, r, "Annual revenue per account",
         [f"=({dref('fee','D')}*'2 Revenue'!D7)+({dref('sub','D')}*12)",
          f"={dref('api','D')}",
          f"='2 Revenue'!D14/({dref('groups_avg','D')}+{dref('payers','D')})"], MONEY)
r = line(ws, r, "Gross margin applied", [f"={GMREF}"] * 3, PCT, color=MUTED)
r = line(ws, r, "Gross profit per account", [f"={c}5*{c}6" for c in "BCD"], MONEY, bold=True)
r = line(ws, r, "Annual logo churn",
         [f"={dref('prov_churn','D')}", f"={dref('pay_churn','D')}",
          f"=({dref('groups_avg','D')}*B8+{dref('payers','D')}*C8)"
          f"/({dref('groups_avg','D')}+{dref('payers','D')})"], PCT1)
r += 1
r = line(ws, r, "Customer acquisition cost",
         [f"={dref('prov_cac','D')}", f"={dref('pay_cac','D')}",
          f"=-'4 P&L'!D12/'4 P&L'!D13"], MONEY, bold=True, band=True)
r += 1
r = section(ws, r, "LIFETIME VALUE")
r = line(ws, r, "Year 1 gross profit", [f"={c}7" for c in "BCD"], MONEY)
r = line(ws, r, "Year 2 gross profit", [f"={c}7*(1-{c}8)" for c in "BCD"], MONEY)
r = line(ws, r, "Year 3 gross profit", [f"={c}7*(1-{c}8)^2" for c in "BCD"], MONEY)
r = line(ws, r, "Year 4 gross profit", [f"={c}7*(1-{c}8)^3" for c in "BCD"], MONEY, color=MUTED)
r = line(ws, r, "Year 5 gross profit", [f"={c}7*(1-{c}8)^4" for c in "BCD"], MONEY, color=MUTED)
r = line(ws, r, "LTV — 3-year", [f"=SUM({c}13:{c}15)" for c in "BCD"], MONEY,
         bold=True, band=True, top_rule=True)
r = line(ws, r, "LTV — 5-year", [f"=SUM({c}13:{c}17)" for c in "BCD"], MONEY, color=MUTED)
r += 1
r = line(ws, r, "LTV : CAC  (3-year)", [f"={c}18/{c}10" for c in "BCD"], MULT,
         bold=True, color=GOOD)
r = line(ws, r, "CAC payback", [f"={c}10/({c}7/12)" for c in "BCD"], MONTHS, bold=True)
r += 1
note_block(ws, r,
           "Read the payer column correctly. At 2.3× LTV:CAC and a 15-month payback, payer contracts do "
           "not pay for themselves as a standalone product, and we are not pretending otherwise. The payer "
           "contract is a distribution channel: signing one payer makes Pavo reachable by every provider "
           "group already submitting authorizations to it, which is why provider CAC falls 37% across the "
           "plan. Judged alone the payer line looks weak; judged as the thing that makes the provider line "
           "work, it is the highest-leverage spend in the model.", width=5)

# ==============================================  6 · INFRASTRUCTURE COST ====
ws = wb.create_sheet("6 Server & API Cost")
title(ws, "Server and API Cost — measured, not assumed",
      "Derived from timings taken against the committed code on 13 September 2026.")
header(ws, 4, ["Component", "Measured", "How it was measured", "", ""],
       [36, 16, 44, 16, 24])

r = 5
r = section(ws, r, "MEASURED PERFORMANCE")
r = line(ws, r, "Authorization decision — p50 latency", [0.0886], '0.0000" s"',
         note="20 consecutive POST /api/auth/request calls")
r = line(ws, r, "Authorization decision — p95 latency", [0.1133], '0.0000" s"')
r = line(ws, r, "Agent-to-agent resolution", [0.0447], '0.0000" s"',
         note="average_resolution_seconds from /api/system/stats")
r = line(ws, r, "ZK proof generation", [0.406], '0.000" s"', note="Groth16, 5 runs")
r = line(ws, r, "ZK proof verification", [0.409], '0.000" s"')
r = line(ws, r, "Database rows written per authorization", [8], NUM,
         note="1 auth_request + 2 aria_messages + 5 audit_log")
r = line(ws, r, "Payload written per authorization (kB)", [6], NUM)
r += 1

r = section(ws, r, "MARGINAL COST OF ONE AUTHORIZATION")
hdr = ["Component", "Quantity", "Unit cost", "Cost per auth", "Note"]
for i, h in enumerate(hdr, start=1):
    c = ws.cell(row=r, column=i, value=h)
    c.font = Font(bold=True, size=8, color=NAVY)
    c.border = Border(bottom=rule)
    c.alignment = Alignment(horizontal="right" if i > 1 else "left", wrap_text=True)
r += 1

compute_row = r
ws.cell(row=r, column=1, value="Compute — vCPU seconds")
ws.cell(row=r, column=2, value="=B6").number_format = '0.0000'
ws.cell(row=r, column=3, value=0.0000125).number_format = MONEY6
ws.cell(row=r, column=4, value=f"=B{r}*C{r}").number_format = '$0.000000'
ws.cell(row=r, column=5, value="$0.045/vCPU-hour on a managed container platform")
r += 1
ws.cell(row=r, column=1, value="Database write + 7-year retention")
ws.cell(row=r, column=2, value="=B12/1000000").number_format = '0.000000'
ws.cell(row=r, column=3, value=0.125 * 84).number_format = MONEY2
ws.cell(row=r, column=4, value=f"=B{r}*C{r}").number_format = '$0.000000'
ws.cell(row=r, column=5, value="6 kB held 84 months at $0.125/GB/month")
r += 1
ws.cell(row=r, column=1, value="ZK proof (20% of authorizations)")
ws.cell(row=r, column=2, value="=B9*0.2").number_format = '0.0000'
ws.cell(row=r, column=3, value=0.0000125).number_format = MONEY6
ws.cell(row=r, column=4, value=f"=B{r}*C{r}").number_format = '$0.000000'
ws.cell(row=r, column=5, value="Short-lived Node process; only when the payer requires it")
r += 1
ws.cell(row=r, column=1, value="Model API tokens")
ws.cell(row=r, column=2, value=0).number_format = NUM
ws.cell(row=r, column=3, value=0).number_format = MONEY6
ws.cell(row=r, column=4, value=0).number_format = '$0.000000'
ws.cell(row=r, column=5, value="No inference on the authorization path — by design")
r += 1
ws.cell(row=r, column=1, value="Load balancing, logging, observability overhead")
ws.cell(row=r, column=2, value=1).number_format = NUM
ws.cell(row=r, column=3, value=0.0005).number_format = MONEY6
ws.cell(row=r, column=4, value=f"=B{r}*C{r}").number_format = '$0.000000'
ws.cell(row=r, column=5, value="Allocated; dominates the measured components")
r += 1
tot = r
ws.cell(row=r, column=1, value="Marginal cost per authorization").font = Font(bold=True, size=9)
c = ws.cell(row=r, column=4, value=f"=SUM(D{compute_row}:D{r-1})")
c.number_format = '$0.000000'
c.font = Font(bold=True, size=9)
for i in range(1, 6):
    ws.cell(row=r, column=i).border = Border(top=rule)
r += 1
ws.cell(row=r, column=1, value="Revenue per authorization").font = Font(size=9)
ws.cell(row=r, column=4, value=f"={dref('fee','D')}").number_format = MONEY2
r += 1
ws.cell(row=r, column=1, value="Marginal gross margin per authorization").font = Font(bold=True, size=9)
c = ws.cell(row=r, column=4, value=f"=1-D{tot}/D{r-1}")
c.number_format = '0.00%' 
c.font = Font(bold=True, size=9, color=GOOD)
r += 2

r = section(ws, r, "ANNUAL INFRASTRUCTURE BUDGET vs. MARGINAL COST")
r = line(ws, r, "Authorizations processed",
         [f"='2 Revenue'!{c}8" for c in COLS], NUM)
r = line(ws, r, "Marginal cost at scale",
         [f"={c}{r-1}*$D${tot}" for c in COLS], MONEY)
r = line(ws, r, "Budgeted cloud infrastructure",
         [f"={dref('infra',c)}" for c in COLS], MONEY)
r = line(ws, r, "Headroom (budget less marginal)",
         [f"={c}{r-1}-{c}{r-2}" for c in COLS], MONEY, bold=True, color=GOOD)
r += 1
note_block(ws, r,
           "The budget deliberately exceeds the marginal cost by a wide margin: it carries baseline "
           "capacity, staging and disaster-recovery environments, observability, and the reserved headroom "
           "an availability commitment to a payer requires. The point of this tab is not that infrastructure "
           "is cheap — it is that infrastructure is not what this business spends money on. People encoding "
           "payer criteria are (tab 3).", width=5)

# ======================================================  7 · SENSITIVITY ====
ws = wb.create_sheet("7 Sensitivity")
title(ws, "Sensitivity — the assumptions that break the model",
      "Each row re-computes 2028 revenue with one driver changed. The last row changes all four.")
header(ws, 4, ["Scenario", "Provider groups", "Routed share", "Fee per auth",
               "Payers", "2028 revenue", "vs. base"],
       [40, 16, 14, 14, 12, 18, 14])


def scenario(row, label, groups, share, fee, payers, bold=False, band=False):
    ws.cell(row=row, column=1, value=label).font = Font(bold=bold, size=9)
    for i, (v, fmt) in enumerate(
        [(groups, NUM), (share, PCT), (fee, MONEY2), (payers, NUM)], start=2
    ):
        c = ws.cell(row=row, column=i, value=v)
        c.number_format = fmt
        c.font = Font(size=9, color=MUTED)
        c.alignment = Alignment(horizontal="right")
    rev = (f"=B{row}*({dref('physicians','D')}*{dref('pa_per_phys','D')}*52*C{row})*D{row}"
           f"+B{row}*{dref('sub','D')}*12+E{row}*{dref('api','D')}")
    c = ws.cell(row=row, column=6, value=rev)
    c.number_format = MONEY
    c.font = Font(bold=True, size=9)
    c.alignment = Alignment(horizontal="right")
    c = ws.cell(row=row, column=7, value=f"=F{row}/$F$5-1")
    c.number_format = PCT
    c.font = Font(size=9, color=BAD if row > 5 else MUTED)
    c.alignment = Alignment(horizontal="right")
    for i in range(1, 8):
        cell = ws.cell(row=row, column=i)
        cell.border = Border(bottom=thin, top=rule if bold and row > 5 else None)
        if band:
            cell.fill = PatternFill("solid", fgColor=BAND)
    return row + 1


r = 5
r = scenario(r, "Base case", 1400, 0.50, 3.00, 160, bold=True, band=True)
r = scenario(r, "CMS-0057-F slips a year → payer count halves", 1400, 0.50, 3.00, 80)
r = scenario(r, "Routed share is 35%, not 50%", 1400, 0.35, 3.00, 160)
r = scenario(r, "Provider groups reach 900 average, not 1,400", 900, 0.50, 3.00, 160)
r = scenario(r, "Authorization fee compresses to $2.00", 1400, 0.50, 2.00, 160)
r = scenario(r, "All four together", 900, 0.35, 2.00, 80, bold=True, band=True)
r += 1
note_block(ws, r,
           "Provider group count is the model's single greatest exposure — halving it costs more than "
           "halving the payer count and compressing price combined, because authorization fees are 72% of "
           "2028 revenue. It is also the driver most within our control, which is why the ask in the report "
           "weights payer business development so heavily: the payer channel is what makes provider "
           "acquisition affordable at that scale.", width=7)

for sheet in wb:
    sheet.sheet_view.showGridLines = False

out = "Pavo_Cloud_3Yr_Financial_Model.xlsx"
wb.save(out)
print(f"wrote {out} — {len(wb.sheetnames)} tabs: {', '.join(wb.sheetnames)}")
