"""Build the HTML that Google Drive turns into the Google Doc copy of the report.

Drive's HTML importer throws away images given as data: URIs but does fetch
http(s) ones, so the three figures are referenced from the public repository at
a pinned commit. Everything else is the same content build_report.py writes,
read back out of report.html so the two cannot drift.

Two things the importer does on its own and have to be undone here: it gives
every table cell all four borders, and it rounds font sizes to whole points.

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
       "2a7b02c442edfa7f0223fba97cd6d57f06564c85/submission/assets/")
IMG = {
    "figure1": ("fig1.png", 624),
    "assets/demo_complete_print.jpg": ("demo_complete_print.jpg", 296),
    "assets/dashboard_print.jpg": ("dashboard_print.jpg", 296),
}

CSS = """
body{font-family:'Times New Roman',Times,serif;font-size:12pt;line-height:1.38;color:#000}
p{margin:0 0 6pt;text-align:justify}
p.t{font-size:16pt;font-weight:bold;text-align:center;margin:0 0 3pt}
p.s{font-style:italic;text-align:center;margin:0 0 3pt}
p.a{text-align:center;margin:0 0 15pt}
h2{font-size:12pt;font-weight:bold;margin:13pt 0 4.5pt;text-align:left}
h3{font-size:12pt;font-weight:bold;margin:10.5pt 0 4pt;text-align:left}
p.c{font-style:italic;margin:7.5pt 0 3pt;text-align:left}
p.f{font-style:italic;margin:2pt 0 7.5pt;text-align:left}
p.g{margin:4pt 0 2pt;text-align:left}
p.z{font-size:4pt;margin:0}
table{border-collapse:collapse;width:100%}
td{font-size:10.5pt;line-height:1.24;text-align:left;vertical-align:top;
   padding:3.75pt 7.5pt 3.75pt 0;
   border-top:0 none #fff;border-left:0 none #fff;border-right:0 none #fff;
   border-bottom:1px solid #DCDCDC}
td.h{color:#1274C4;font-weight:bold;vertical-align:bottom;
     padding:3pt 7.5pt 3pt 0;border-bottom:1px solid #555555}
td.n{text-align:right;padding-right:0}
td.e{border-bottom:1px solid #000000}
td.o{border-top:1px solid #555555;font-weight:bold}
td.p{border:1px solid #CCCCCC;background-color:#F4F4F4;padding:5pt 6pt}
td.i{border:0 none #fff;padding:0 6pt 0 0;vertical-align:top}
p.m{font-family:'Courier New',Courier,monospace;font-size:8.4pt;line-height:1.35;
    margin:0;text-align:left}
p.k{font-size:9.5pt;font-style:italic;margin:0;text-align:left}
p.w{margin:0 0 3pt;text-align:left}
"""


def runs_html(runs) -> str:
    out = []
    for text, b, i in runs:
        t = H.escape(text)
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
            text = "".join(t for t, _, _ in b.runs)
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
                       + "<br>".join(lines) + '</p></td></tr></table><p class="z"></p>')

        elif b.kind == "table":
            out.append(table_html(b.rows))

        elif b.kind == "figrow":
            cells = []
            for src, cap in b.figs:
                name, w = IMG[src]
                cap = H.escape(H.unescape(re.sub(r"\s+", " ",
                                                 re.sub(r"<[^>]+>", "", cap))).strip())
                cells.append(f'<td class="i" style="width:50%">'
                             f'<p class="w"><img src="{RAW}{name}" width="{w}"></p>'
                             f'<p class="k">{cap}</p></td>')
            out.append("<table><tr>" + "".join(cells)
                       + '</tr></table><p class="z"></p>')

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
            inner = runs_html(cell["runs"]).replace("\n", "<br>")
            tds.append(f'<td{c} style="width:{widths[ci] * 100:.0f}%">{inner}</td>')
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return "<table>" + "".join(trs) + '</table><p class="z"></p>'


if __name__ == "__main__":
    doc = ('<!doctype html><html><head><meta charset="utf-8">'
           "<title>Pavo Cloud — Technical Execution Report</title>"
           f"<style>{CSS}</style></head>"
           f"<body>{build()}</body></html>")
    open(OUT, "w", encoding="utf-8").write(doc)
    print(f"wrote {OUT} ({len(doc)/1024:.1f} KB)")
