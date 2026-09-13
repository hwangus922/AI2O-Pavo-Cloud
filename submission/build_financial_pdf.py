"""Render the financial model workbook to a print-ready HTML document.

Every value is read out of Pavo_Cloud_3Yr_Financial_Model.xlsx and, where the
cell holds a formula, evaluated against the workbook itself — so the PDF cannot
disagree with the spreadsheet. Run after any change to the model:

    python build_financial_pdf.py
    chromium --headless --print-to-pdf=Pavo_Cloud_3Yr_Financial_Model.pdf financials.html
"""
from __future__ import annotations

import html
import os
import re

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string, get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
BOOK = os.path.join(HERE, "Pavo_Cloud_3Yr_Financial_Model.xlsx")
OUT = os.path.join(HERE, "financials.html")

wb = load_workbook(BOOK)

# ------------------------------------------------------------------ engine ---
REF = re.compile(r"(?:'([^']+)'!|([A-Za-z0-9 &]+)!)?\$?([A-Z]{1,2})\$?(\d+)")
RANGE = re.compile(
    r"SUM\(\s*(?:'([^']+)'!)?\$?([A-Z]{1,2})\$?(\d+)\s*:\s*\$?([A-Z]{1,2})\$?(\d+)\s*\)"
)
_memo: dict = {}


def value(sheet: str, coord: str):
    key = (sheet, coord)
    if key in _memo:
        return _memo[key]
    raw = wb[sheet][coord].value
    if isinstance(raw, str) and raw.startswith("="):
        out = _eval(sheet, raw[1:])
    elif isinstance(raw, (int, float)) and not isinstance(raw, bool):
        out = float(raw)
    else:
        out = raw
    _memo[key] = out
    return out


def _eval(sheet: str, expr: str) -> float:
    def sum_sub(m):
        sh = m.group(1) or sheet
        c1, r1, c2, r2 = m.group(2), int(m.group(3)), m.group(4), int(m.group(5))
        total = 0.0
        for ci in range(column_index_from_string(c1), column_index_from_string(c2) + 1):
            for ri in range(r1, r2 + 1):
                v = value(sh, f"{get_column_letter(ci)}{ri}")
                if isinstance(v, float):
                    total += v
        return repr(total)

    expr = RANGE.sub(sum_sub, expr)

    def ref_sub(m):
        sh = m.group(1) or m.group(2) or sheet
        v = value(sh, f"{m.group(3)}{m.group(4)}")
        return repr(v if isinstance(v, float) else 0.0)

    return float(eval(REF.sub(ref_sub, expr).replace("^", "**"), {"__builtins__": {}}, {}))


# --------------------------------------------------------------- formatting ---
def _decimals(nf: str) -> int:
    """Count the digits Excel would show after the decimal point."""
    core = nf.split(";")[0].split('"')[0]
    m = re.search(r"\.(0+)", core)
    return len(m.group(1)) if m else 0


def fmt(v, number_format: str) -> str:
    """Apply the cell's Excel number format, closely enough for print."""
    if v is None:
        return ""
    if isinstance(v, str):
        return html.escape(v)
    nf = number_format or ""
    dp = _decimals(nf)
    if "%" in nf:
        return f"{v * 100:.{dp}f}%"
    if '"\u00d7"' in nf:
        return f"{v:.1f}&times;"
    if '" mo"' in nf:
        return f"{v:.1f} mo"
    if '" s"' in nf:
        return f"{v:.{dp}f} s"
    if "$" in nf:
        s_ = f"${abs(v):,.{dp}f}"
        return f"({s_})" if v < 0 else s_
    return f"{v:,.{dp}f}"


def is_money_negative(v) -> bool:
    return isinstance(v, float) and v < 0


# ------------------------------------------------------------------ render ---
def render_sheet(name: str, cols: list[int], widths: list[str]) -> str:
    ws = wb[name]
    rows = []
    last_col = len(cols)
    for r in range(4, ws.max_row + 1):
        cells = []
        empty = True
        merged = any(r >= m.min_row and r <= m.max_row for m in ws.merged_cells.ranges)
        for c in cols:
            cell = ws.cell(row=r, column=c)
            v = value(name, cell.coordinate)
            txt = fmt(v, cell.number_format)
            if txt:
                empty = False
            bold = bool(cell.font and cell.font.bold)
            colr = cell.font.color.rgb if (cell.font and cell.font.color and
                                           cell.font.color.rgb) else None
            cls = []
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                cls.append("num")
            elif c > 1:
                cls.append("txt")
            if bold:
                cls.append("b")
            if colr in ("FF1C6B4A", "1C6B4A"):
                cls.append("good")
            if colr in ("FF9B2C2C", "9B2C2C"):
                cls.append("bad")
            if colr in ("FF5D6875", "5D6875"):
                cls.append("mut")
            if colr in ("FF1F6F8B", "1F6F8B"):
                cls.append("acc")
            if r == 4:
                cls.append("hd")
            cells.append((txt, " ".join(cls)))
        if empty:
            continue
        if merged and cells[0][0]:
            rows.append(f'<tr class="noteRow"><td colspan="{last_col}">{cells[0][0]}</td></tr>')
            continue
        # a section label: only column A has content and it is accent-coloured
        if cells[0][0] and not any(t for t, _ in cells[1:]):
            rows.append(f'<tr class="sec"><td colspan="{last_col}">{cells[0][0]}</td></tr>')
            continue
        tds = "".join(f'<td class="{cl}">{t}</td>' for t, cl in cells)
        rows.append(f"<tr>{tds}</tr>")
    cg = "".join(f'<col style="width:{w}">' for w in widths)
    return f"<table><colgroup>{cg}</colgroup>" + "".join(rows) + "</table>"


CSS = """
@page { size: Letter; margin: 0.5in 0.55in 0.45in 0.55in; }
:root{--ink:#10151f;--body:#2b3440;--muted:#5d6875;--line:#d6dbe2;--hair:#e8ecf1;
      --navy:#16324f;--accent:#1f6f8b;--good:#1c6b4a;--bad:#9b2c2c;--wash:#f5f7fa;--band:#edf1f5}
*{box-sizing:border-box}
body{margin:0;font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:8.1pt;
     line-height:1.3;color:var(--body);-webkit-font-smoothing:antialiased}
.page{page-break-after:always;display:flex;flex-direction:column;min-height:948px}
.page:last-child{page-break-after:auto}
h1{font-size:18pt;margin:0 0 3px;color:var(--ink);letter-spacing:-.4px;line-height:1.1}
h2{font-size:10.4pt;margin:0 0 5px;color:var(--navy);padding-bottom:4px;
   border-bottom:1.6px solid var(--navy);letter-spacing:-.15px}
h2 .n{color:var(--accent);font-weight:700;margin-right:7px}
h3{font-size:9pt;margin:9px 0 2px;color:var(--ink)}
.cover-rule{height:5px;background:var(--navy);margin-bottom:11px}
.eyebrow{font-size:7.4pt;letter-spacing:.17em;text-transform:uppercase;color:var(--accent);
         font-weight:700;margin-bottom:6px}
.sub{font-size:10pt;color:var(--muted);margin:2px 0 7px}
p{margin:0 0 5px}
b{color:var(--ink);font-weight:600}
code{font-family:"SF Mono",Menlo,Consolas,monospace;font-size:7.2pt;background:var(--wash);
     padding:.5px 3px;border-radius:2px;color:var(--navy)}
table{width:100%;border-collapse:collapse;margin:3px 0 6px;font-size:7.7pt}
td{padding:2.4px 6px;border-bottom:.8px solid var(--hair);vertical-align:top}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.b{font-weight:700;color:var(--ink)}
td.good{color:var(--good)} td.bad{color:var(--bad)}
td.mut{color:var(--muted)} td.acc{color:var(--accent)}
td.txt{color:var(--muted);font-size:7.3pt}
tr.hd td,td.hd{font-weight:700;color:var(--navy);font-size:7pt;text-transform:uppercase;
        letter-spacing:.05em;border-bottom:1.4px solid var(--navy);padding-bottom:3px}
tr.sec td{font-weight:700;color:var(--accent);font-size:8.4pt;padding-top:8px;
          border-bottom:none;letter-spacing:.02em}
tr.noteRow td{background:var(--wash);border-left:2.8px solid var(--accent);
              font-style:italic;color:var(--navy);padding:5px 8px;font-size:7.2pt;
              border-bottom:none}
.footer{margin-top:auto;padding-top:4px;font-size:6.5pt;color:#9aa4b0;
        border-top:.8px solid var(--hair);display:flex;justify-content:space-between}
.note{background:var(--wash);border-left:2.8px solid var(--accent);padding:6px 8px;margin:5px 0 0}
.note .t{font-weight:700;color:var(--navy);font-size:8pt;display:block;margin-bottom:2px}
"""


def page(body: str, n: int, total: int) -> str:
    return (f'<div class="page">{body}'
            f'<div class="footer"><span>Pavo Cloud — Three-Year Financial Model</span>'
            f'<span>Page {n} of {total}</span></div></div>')


T = 4
p1 = page(f"""
  <div class="cover-rule"></div>
  <div class="eyebrow">Round 2 Submission &nbsp;·&nbsp; Financial Model</div>
  <h1>Three-Year Financial Model</h1>
  <div class="sub">Every figure derived from the drivers below — nothing is asserted</div>
  <h2><span class="n">1</span>Drivers</h2>
  <p>This is the only tab with typed-in numbers. Everything on pages 2–4 is a formula pointing back
  here, so changing one assumption moves the whole model. The three revenue targets carried over from
  the Round 1 narrative — $1.0M, $8.2M, $36.1M — are not typed anywhere; they fall out of these inputs.</p>
  {render_sheet("1 Drivers", [1,2,3,4,6], ["31%","11%","11%","11%","36%"])}
""", 1, T)

p2 = page(f"""
  <h2><span class="n">2</span>Revenue build</h2>
  {render_sheet("2 Revenue", [1,2,3,4,6], ["32%","14%","14%","14%","26%"])}
  <h2><span class="n">3</span>Cost of revenue and gross margin</h2>
  {render_sheet("3 Cost of Revenue", [1,2,3,4,5], ["32%","14%","14%","14%","26%"])}
""", 2, T)

p3 = page(f"""
  <h2><span class="n">4</span>Profit and loss</h2>
  {render_sheet("4 P&L", [1,2,3,4], ["40%","20%","20%","20%"])}
  <h2><span class="n">5</span>Unit economics — CAC, LTV, payback</h2>
  {render_sheet("5 Unit Economics", [1,2,3,4], ["40%","20%","20%","20%"])}
""", 3, T)

p4 = page(f"""
  <h2><span class="n">6</span>Server and API cost — measured, not assumed</h2>
  <p>Timings taken against the committed code on 13 September 2026. The point is not that infrastructure
  is cheap — it is that infrastructure is not what this business spends money on. People encoding payer
  criteria are.</p>
  {render_sheet("6 Server & API Cost", [1,2,3,4,5], ["30%","13%","13%","13%","31%"])}
  <h2><span class="n">7</span>Sensitivity</h2>
  {render_sheet("7 Sensitivity", [1,2,3,4,5,6,7], ["33%","11%","10%","10%","8%","16%","12%"])}
""", 4, T)

doc = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
       f'<title>Pavo Cloud — Three-Year Financial Model</title>'
       f"<style>{CSS}</style></head><body>{p1}{p2}{p3}{p4}</body></html>")

open(OUT, "w", encoding="utf-8").write(doc)
print(f"wrote {OUT} ({len(doc)/1024:.0f} KB)")
