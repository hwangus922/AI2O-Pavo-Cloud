"""Assemble the Build Log appendix from captured terminal output and screenshots.

Terminal text is embedded verbatim from captures/*.txt and screenshots are
inlined from assets/, so the page cannot drift from what the commands actually
printed. Re-capture those files on your own machine, then:

    python build_appendix.py
    chromium --headless --print-to-pdf=Pavo_Cloud_BuildLog_Appendix.pdf appendix.html
"""
import base64
import glob
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "appendix.html")
SHOTS = os.path.join(HERE, "assets")

term = {
    os.path.splitext(os.path.basename(f))[0]: open(f, encoding="utf-8").read().rstrip()
    for f in glob.glob(os.path.join(HERE, "captures", "*.txt"))
}


def t(name):
    return html.escape(term[name])


def img(fn):
    """Inline a screenshot so the page renders standalone."""
    with open(os.path.join(SHOTS, fn), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


CSS = """
@page { size: Letter; margin: 0.5in 0.55in 0.45in 0.55in; }
:root{--ink:#10151f;--body:#2b3440;--muted:#5d6875;--line:#d6dbe2;--hair:#e8ecf1;
      --navy:#16324f;--accent:#1f6f8b;--good:#1c6b4a;--warn:#8a5a12;--wash:#f5f7fa;}
*{box-sizing:border-box}
body{margin:0;font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;
     font-size:8.4pt;line-height:1.34;color:var(--body);-webkit-font-smoothing:antialiased}
.page{page-break-after:always;display:flex;flex-direction:column;min-height:952px}
.page:last-child{page-break-after:auto}
h1{font-size:17pt;line-height:1.1;margin:0 0 3px;color:var(--ink);letter-spacing:-.4px}
h2{font-size:10.6pt;margin:0 0 6px;color:var(--navy);padding-bottom:4px;
   border-bottom:1.6px solid var(--navy);letter-spacing:-.15px}
h2 .n{color:var(--accent);font-weight:700;margin-right:7px}
p{margin:0 0 5px}
b{color:var(--ink);font-weight:600}
code{font-family:"SF Mono",Menlo,Consolas,monospace;font-size:7.3pt;background:var(--wash);
     padding:.5px 3px;border-radius:2px;color:var(--navy)}
.cover-rule{height:5px;background:var(--navy);margin-bottom:11px}
.eyebrow{font-size:7.4pt;letter-spacing:.17em;text-transform:uppercase;color:var(--accent);
         font-weight:700;margin-bottom:6px}
.sub{font-size:10pt;color:var(--muted);margin:2px 0 8px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.two>*{min-width:0}
.item{margin-bottom:7px}
.cap{display:flex;justify-content:space-between;align-items:baseline;
     border-bottom:1.2px solid var(--navy);padding-bottom:2.5px;margin-bottom:4px}
.cap .ttl{font-size:8.7pt;font-weight:700;color:var(--ink)}
.cap .ttl .ix{color:var(--accent);margin-right:5px}
.cap .pv{font-size:7pt;color:var(--muted);font-style:italic;text-align:right;max-width:52%}
pre{background:#12181f;color:#dfe6ee;border-radius:3px;padding:7px 9px;margin:0;max-width:100%;
    font-family:"SF Mono",Menlo,Consolas,monospace;font-size:6.5pt;line-height:1.42;
    white-space:pre;overflow:hidden}
pre .g{color:#7fd1a8}
figure{margin:0}
figure img{width:93%;margin:0 auto;display:block;border:1px solid var(--line);border-radius:3px}
.note{background:var(--wash);border-left:2.8px solid var(--accent);padding:6px 8px;margin:6px 0 0}
.note .t{font-weight:700;color:var(--navy);font-size:8pt;display:block;margin-bottom:2px}
.warnb{background:#fdfaf4;border-left:2.8px solid var(--warn);padding:6px 8px;margin:6px 0 0}
.warnb .t{font-weight:700;color:var(--warn);font-size:8pt;display:block;margin-bottom:2px}
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin:7px 0 7px}
.kpi{border:1px solid var(--line);border-top:2.6px solid var(--accent);padding:5px 7px 6px}
.kpi .v{font-size:13.5pt;font-weight:700;color:var(--ink);line-height:1;letter-spacing:-.5px}
.kpi .l{font-size:6.4pt;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);
        margin-top:4px;font-weight:600}
.footer{margin-top:auto;padding-top:4px;font-size:6.5pt;color:#9aa4b0;
        border-top:.8px solid var(--hair);display:flex;justify-content:space-between}
"""


def item(ix, title, proves, body):
    return f"""<div class="item">
  <div class="cap"><div class="ttl"><span class="ix">{ix}</span>{title}</div>
  <div class="pv">{proves}</div></div>
  {body}</div>"""


def shot(fn, pct=None):
    w = f' style="width:{pct}%"' if pct else ""
    return f'<figure><img src="{img(fn)}"{w} alt=""></figure>'


def term_block(name):
    return f"<pre>{t(name)}</pre>"


page1 = f"""<div class="page">
  <div class="cover-rule"></div>
  <div class="eyebrow">Technical Execution Report &nbsp;·&nbsp; Appendix</div>
  <h1>The Build Log</h1>
  <div class="sub">Nine artifacts, captured from the running system on 13 September 2026</div>

  <div class="kpis">
    <div class="kpi"><div class="v">12</div><div class="l">Commits, 5 merged PRs</div></div>
    <div class="kpi"><div class="v">138</div><div class="l">Tests passing, 0 failing</div></div>
    <div class="kpi"><div class="v">19,541</div><div class="l">Lines of product code</div></div>
    <div class="kpi"><div class="v">88.6<span style="font-size:8pt">ms</span></div><div class="l">Median decision, 20 runs</div></div>
    <div class="kpi"><div class="v">11.1<span style="font-size:8pt">s</span></div><div class="l">Full six-step demo</div></div>
  </div>

  {item("1", "Commit history — four phases, one PR each",
        "A sustained build, not one weekend. Scoped to the product commits; the Round 2 "
        "submission commit adds documents, not code.",
        term_block("git"))}

  <div class="two">
    <div>
      {item("2", "The test suite",
            "138 passing, 0 failing, 23.4 s.",
            term_block("pytest"))}
    </div>
    <div>
      {item("3", "Production build",
            "Deployable software — 7 routes, clean compile.",
            term_block("build"))}
    </div>
  </div>

  {item("4", "A live authorization decision, end to end",
        "This call: 90.1 ms. Note the patient ID — <code>mrn-99001</code> went in, a SHA-256 hash came back.",
        term_block("decision"))}

  <div class="note">
    <span class="t">Reproduce every figure on this page</span>
    <code>git log --shortstat a13f6cb</code> &nbsp;·&nbsp;
    <code>cd zk &amp;&amp; npm install</code> then <code>cd backend &amp;&amp; .venv/bin/python -m pytest</code> &nbsp;·&nbsp;
    <code>cd frontend &amp;&amp; npm run build</code> &nbsp;·&nbsp; the <code>curl</code> shown above.
    The ZK tests need snarkjs present; without it 7 of the 138 fail on a missing dependency.
  </div>

  <div class="footer"><span>Pavo Cloud — Build Log Appendix</span><span>Page 1 of 5</span></div>
</div>"""

page2 = f"""<div class="page">
  <h2><span class="n">A</span>The safety guarantees, demonstrated</h2>

  <div class="two">
    <div>
      {item("5", "An unverified message never acts",
            "HTTP 401 before the payload is read.",
            term_block("tamper"))}
    </div>
    <div>
      {item("6", "Five audit entries per authorization",
            "Every decision row carries its rule ID.",
            term_block("audit"))}
    </div>
  </div>

  {item("7", "A zero-knowledge proof of patient criteria",
        "Three criteria proven. Age, diagnosis and deductible appear nowhere in the response.",
        term_block("zk"))}

  <div class="warnb">
    <span class="t">What this response does and does not reveal</span>
    The six public signals are three verdicts (<code>1,1,1</code>) and the three policy parameters the
    payer set (<code>min_age 18</code>, the approved-diagnosis hash, <code>deductible_required 1</code>).
    The patient's actual age, diagnosis code and deductible balance are never transmitted. The one
    thing it does leak, stated in §5.3 of the report: because the diagnosis check compares against a
    single hash, a passing proof tells the payer the patient carries that one diagnosis.
  </div>

  <div class="footer"><span>Pavo Cloud — Build Log Appendix</span><span>Page 2 of 5</span></div>
</div>"""

page3 = f"""<div class="page">
  <h2><span class="n">B</span>The running system — one order, start to finish</h2>

  {item("8", "The six-step demo, completed in 11.1 seconds",
        "Every panel is live data. Measured across three consecutive runs: 11.00 s, 11.07 s, 11.17 s.",
        shot("demo_complete.png"))}

  {item("8a", "Step 3 — zero-knowledge, in the UI",
        "The same proof as artifact 7, as a payer would see it.",
        shot("demo_zk.png"))}

  <div class="footer"><span>Pavo Cloud — Build Log Appendix</span><span>Page 3 of 5</span></div>
</div>"""

page4 = f"""<div class="page">
  <h2><span class="n">C</span>Identity, and the rule that decided</h2>

  {item("8b", "Step 2 — identity",
        "Two RSA-2048 signatures, both verified against the sender's registered public key.",
        shot("demo_identity.png"))}

  {item("8c", "Step 4 — the rule engine",
        "PAVO-R002, with the full text of the rule that produced the approval.",
        shot("demo_rules.png"))}

  <div class="footer"><span>Pavo Cloud — Build Log Appendix</span><span>Page 4 of 5</span></div>
</div>"""

page5 = f"""<div class="page">
  <h2><span class="n">D</span>The record behind every decision</h2>

  {item("9", "The dashboard — every decision with the rule that produced it",
        "10 authorizations, 44 ms average resolution, 20 signed ARIA messages.",
        shot("dashboard.png", 88))}

  {item("9a", "The audit trail — 74 events, filterable, exportable",
        "Append-only. Nothing on this screen is editable.",
        shot("audit.png", 88))}

  <div class="note">
    <span class="t">What to notice in the requests table</span>
    Every row carries a rule ID and 100% confidence — 100% because the match is <i>definitive</i>, not
    because a model was sure. No language model participates in any decision on that screen. The one
    <b>Escalated</b> row is <code>PAVO-R003</code>: a knee replacement whose diagnosis did not match the
    covered condition, waiting for a human with its record already assembled.
  </div>

  <div class="footer"><span>Pavo Cloud — Build Log Appendix</span><span>Page 5 of 5</span></div>
</div>"""

doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Pavo Cloud — Build Log Appendix</title>
<style>{CSS}</style></head><body>
{page1}
{page2}
{page3}
{page4}
{page5}
</body></html>"""

open(OUT, "w", encoding="utf-8").write(doc)
print(f"wrote {OUT}  ({len(doc)/1024:.0f} KB with inlined images)")
