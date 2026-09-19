"""Build the HTML that Google Drive turns into the Google Doc copy of the report.

Drive's HTML importer throws away images given as data: URIs but does fetch
http(s) ones, so the three figures are referenced from the public repository at
a pinned commit. Everything else is the same content build_report.py writes,
read back out of report.html so the two cannot drift.

Google Docs lays text out differently from a browser, so the numbers in CSS
below are tuned for Docs and will look tight if you open this file in one.
Measured against a calibration document, for 12pt Times:

    line box = 2.25pt + 12.5pt x line-height

so line-height 1.38 gives 19.5pt, not the 16.56pt a browser gives, and the
document ran a page long. 1.15 reproduces the printed report. Three further
things the importer does on its own:

  * a table cell takes its line box from the paragraph's font size, not from
    a span inside it, so cell text needs its own <p> or every row is set as
    though it were 12pt;
  * an empty paragraph inherits the previous paragraph's size, so the
    spacers after tables carry a non-breaking space;
  * it gives every table cell all four borders, and rounds font sizes to
    whole points.

    python build_gdoc_html.py
"""
from __future__ import annotations

import html as H
import os
import re

from build_docx import parse, width_of

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "gdoc.html")

RAW = ("https://raw.githubusercontent.com/hwangus922/AI2O-Pavo-Cloud/"
       "5c11e2c/submission/assets/")
IMG = {
    "figure1": ("fig1.png", 480),
    "assets/demo_complete_print.jpg": ("demo_complete_print.jpg", 270),
    "assets/dashboard_print.jpg": ("dashboard_print.jpg", 297),
}

CSS = """
body{font-family:'Times New Roman',Times,serif;font-size:12pt;line-height:1.01;color:#000}
p{margin:0 0 3.75pt;text-align:justify;line-height:1.01}
p.t{font-size:16pt;font-weight:bold;text-align:center;margin:0 0 3pt}
p.s{font-style:italic;text-align:center;margin:0 0 3pt}
p.a{text-align:center;margin:0 0 15pt}
h2{font-size:12pt;font-weight:bold;margin:7pt 0 2.25pt;text-align:left;line-height:1.01}
h3{font-size:12pt;font-weight:bold;margin:4.5pt 0 1.5pt;text-align:left;line-height:1.01}
p.c{font-style:italic;margin:3pt 0 1.5pt;text-align:left}
p.f{font-size:9.5pt;font-style:italic;line-height:1.05;margin:2.25pt 0 3.375pt;text-align:left}
p.g{margin:4pt 0 2pt;text-align:left}
p.z{font-size:2pt;line-height:1;margin:0}
table{border-collapse:collapse;width:100%}
td{vertical-align:top;padding:1.8pt 7.5pt 1.8pt 0;
   border-top:0 none #fff;border-left:0 none #fff;border-right:0 none #fff;
   border-bottom:1px solid #DCDCDC}
td.h{vertical-align:bottom;padding:1.9pt 7.5pt 1.9pt 0;border-bottom:1px solid #555555}
td.n{padding-right:0}
td.e{border-bottom:1px solid #000000}
td.o{border-top:1px solid #555555}
td.p{border:1px solid #CCCCCC;background-color:#F4F4F4;padding:5pt 6pt}
td.i{border:0 none #fff;padding:0 6pt 0 0;vertical-align:bottom}
td.i2{border:0 none #fff;padding:0 0 0 6pt;vertical-align:bottom}
td.j{border:0 none #fff;padding:3pt 6pt 0 0;vertical-align:top}
td.j2{border:0 none #fff;padding:3pt 0 0 6pt;vertical-align:top}
p.q{font-size:10.5pt;line-height:1.05;margin:0;text-align:left}
p.n{text-align:right}
p.hh{color:#1274C4;font-weight:bold}
p.bb{font-weight:bold}
p.m{font-family:'Courier New',Courier,monospace;font-size:7.6pt;line-height:1.0;
    margin:0;text-align:left}
p.k{font-size:9.5pt;font-style:italic;line-height:1.05;margin:0;text-align:justify}
p.w{margin:0;text-align:left}
"""


def runs_html(runs) -> str:
    out = []
    for run in runs:
        text, b, i = run[0], run[1], run[2]
        mono = run[3] if len(run) > 3 else 0
        t = H.escape(text)
        if mono:
            t = f'<span style="font-family:\'Courier New\',monospace;font-size:10pt">{t}</span>'
        if b:
            t = f"<b>{t}</b>"
        if i:
            t = f"<i>{t}</i>"
        out.append(t)
    return "".join(out)


def build() -> str:
    blocks = parse(open(os.path.join(HERE, "report.html"), encoding="utf-8").read())
    out: list[str] = []
    seen_head = False

    for b in blocks:
        if b.kind == "p" and not seen_head:
            text = "".join(r[0] for r in b.runs)
            if text.startswith("Pavo Cloud") and len(text) < 20:
                out.append(f'<p class="t">{runs_html(b.runs)}</p>')
                continue
            if "Technical Execution Report" in text:
                out.append(f'<p class="s">{runs_html(b.runs)}</p>')
                continue
            if "CFO" in text:
                out.append(f'<p class="a">{runs_html(b.runs)}</p>')
                continue

        if b.kind in ("h2", "h3"):
            seen_head = seen_head or b.kind == "h2"
            out.append(f"<{b.kind}>{runs_html(b.runs)}</{b.kind}>")

        elif b.kind == "p":
            cls = "f" if "fcap" in b.cls else "c" if "cap" in b.cls else ""
            tag = f'<p class="{cls}">' if cls else "<p>"
            out.append(f"{tag}{runs_html(b.runs)}</p>")

        elif b.kind == "figure1":
            name, w = IMG["figure1"]
            out.append(f'<p class="g"><img src="{RAW}{name}" width="{w}"></p>')

        elif b.kind == "pre":
            lines = []
            for ln in b.text.strip("\n").split("\n"):
                stripped = ln.lstrip(" ")
                pad = "&nbsp;" * (len(ln) - len(stripped))
                lines.append(pad + H.escape(stripped).replace("  ", " &nbsp;"))
            out.append('<table><tr><td class="p"><p class="m">'
                       + "<br>".join(lines) + '</p></td></tr></table><p class="z">&nbsp;</p>')

        elif b.kind == "table":
            out.append(table_html(b.rows))

        elif b.kind == "figrow":
            # images on one row, one caption spanning both on the next
            widths = ["47.6%", "52.4%"]
            imgs = []
            for i, src in enumerate(b.srcs):
                name, w = IMG[src]
                cls = "i" if i == 0 else "i2"
                imgs.append(f'<td class="{cls}" style="width:{widths[i]}">'
                            f'<p class="w"><img src="{RAW}{name}" width="{w}"></p></td>')
            cap = H.escape(H.unescape(re.sub(r"\s+", " ",
                                            re.sub(r"<[^>]+>", "", b.cap))).strip())
            out.append('<table><tr>' + "".join(imgs) + '</tr><tr>'
                       + f'<td class="j" colspan="2"><p class="k">{cap}</p></td>'
                       + '</tr></table><p class="z">&nbsp;</p>')

    return "\n".join(out)


def table_html(rows) -> str:
    ncols = max(len(r["cells"]) for r in rows)
    widths = []
    for i in range(ncols):
        c = rows[0]["cells"][i] if i < len(rows[0]["cells"]) else {}
        widths.append(width_of(c.get("width", "")))
    free = [i for i, w in enumerate(widths) if w is None]
    rest = 1 - sum(w for w in widths if w)
    for i in free:
        widths[i] = rest / len(free)

    last = len(rows) - 1
    trs = []
    for ri, row in enumerate(rows):
        tds = []
        for ci, cell in enumerate(row["cells"]):
            cls = []
            if cell["head"]:
                cls.append("h")
            elif ri == last:
                cls.append("e")
            if "n" in cell["cls"]:
                cls.append("n")
            if "tot" in row["cls"]:
                cls.append("o")
            c = f' class="{" ".join(cls)}"' if cls else ""
            pcls = ["q"]
            if "n" in cell["cls"]:
                pcls.append("n")
            if cell["head"]:
                pcls.append("hh")
            elif "tot" in row["cls"]:
                pcls.append("bb")
            inner = runs_html(cell["runs"]).replace("\n", "<br>")
            tds.append(f'<td{c} style="width:{widths[ci] * 100:.0f}%">'
                       f'<p class="{" ".join(pcls)}">{inner}</p></td>')
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return "<table>" + "".join(trs) + '</table><p class="z">&nbsp;</p>'


if __name__ == "__main__":
    doc = ('<!doctype html><html><head><meta charset="utf-8">'
           "<title>Pavo Cloud Technical Execution Report</title>"
           f"<style>{CSS}</style></head>"
           f"<body>{build()}</body></html>")
    open(OUT, "w", encoding="utf-8").write(doc)
    print(f"wrote {OUT} ({len(doc)/1024:.1f} KB)")
