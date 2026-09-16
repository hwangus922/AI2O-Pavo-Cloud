"""Build the HTML that Google Drive turns into the Google Doc copy of the report.

Drive's HTML importer throws away images given as data: URIs but does fetch
http(s) ones, so the three figures are referenced from the public repository.
Everything else is the same content build_report.py writes, read back out of
report.html so the two cannot drift.

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
       "refs/heads/claude/great-mendel-n663c4/submission/assets/")
IMG = {
    "figure1": ("fig1.png", 624),
    "assets/demo_complete_print.jpg": ("demo_complete_print.jpg", 296),
    "assets/dashboard_print.jpg": ("dashboard_print.jpg", 296),
}

SERIF = "font-family:'Times New Roman',Times,serif"
BODY = f"{SERIF};font-size:12pt;line-height:1.38;color:#000"
BLUE = "#1274C4"


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
                out.append(f'<p style="{BODY};font-size:16pt;font-weight:bold;'
                           f'text-align:center;margin:0 0 3pt">{runs_html(b.runs)}</p>')
                continue
            if "Technical Execution Report" in text:
                out.append(f'<p style="{BODY};font-style:italic;text-align:center;'
                           f'margin:0 0 3pt">{runs_html(b.runs)}</p>')
                continue
            if "CFO" in text:
                out.append(f'<p style="{BODY};text-align:center;margin:0 0 15pt">'
                           f"{runs_html(b.runs)}</p>")
                continue

        if b.kind in ("h2", "h3"):
            seen_head = seen_head or b.kind == "h2"
            top = "13pt" if b.kind == "h2" else "10.5pt"
            bot = "4.5pt" if b.kind == "h2" else "4pt"
            out.append(f'<{b.kind} style="{BODY};font-weight:bold;margin:{top} 0 {bot}">'
                       f"{runs_html(b.runs)}</{b.kind}>")

        elif b.kind == "p":
            if "cap" in b.cls:
                out.append(f'<p style="{BODY};font-style:italic;margin:7.5pt 0 3pt">'
                           f"{runs_html(b.runs)}</p>")
            elif "fcap" in b.cls:
                out.append(f'<p style="{BODY};font-size:10.5pt;font-style:italic;'
                           f'margin:2pt 0 7.5pt">{runs_html(b.runs)}</p>')
            else:
                out.append(f'<p style="{BODY};text-align:justify;margin:0 0 6pt">'
                           f"{runs_html(b.runs)}</p>")

        elif b.kind == "figure1":
            name, w = IMG["figure1"]
            out.append(f'<p style="margin:4pt 0 2pt"><img src="{RAW}{name}" width="{w}"></p>')

        elif b.kind == "pre":
            lines = []
            for ln in b.text.strip("\n").split("\n"):
                stripped = ln.lstrip(" ")
                pad = "&nbsp;" * (len(ln) - len(stripped))
                lines.append(pad + H.escape(stripped).replace("  ", " &nbsp;"))
            body = "<br>".join(lines)
            out.append(
                '<table style="border-collapse:collapse;width:100%"><tr>'
                '<td style="background-color:#f4f4f4;border:1px solid #cccccc;'
                'padding:5pt 6pt">'
                f"<p style=\"font-family:'Courier New',Courier,monospace;font-size:8.4pt;"
                f'line-height:1.35;margin:0;color:#000">{body}</p>'
                "</td></tr></table>"
                '<p style="font-size:2pt;margin:0">&nbsp;</p>')

        elif b.kind == "table":
            out.append(table_html(b.rows))

        elif b.kind == "figrow":
            cells = []
            for src, cap in b.figs:
                name, w = IMG[src]
                cap = re.sub(r"<[^>]+>", "", cap)
                cap = H.escape(H.unescape(re.sub(r"\s+", " ", cap)).strip())
                cells.append(
                    '<td style="width:50%;vertical-align:top;padding:0 6pt 0 0">'
                    f'<p style="margin:0 0 3pt"><img src="{RAW}{name}" width="{w}"></p>'
                    f'<p style="{BODY};font-size:9.5pt;font-style:italic;margin:0">'
                    f"{cap}</p></td>")
            out.append('<table style="border-collapse:collapse;width:100%"><tr>'
                       + "".join(cells) + "</tr></table>"
                       '<p style="font-size:2pt;margin:0">&nbsp;</p>')

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
            head = cell["head"]
            num = "n" in cell["cls"]
            if head:
                border = "1px solid #555555"
            elif ri == last:
                border = "1px solid #000000"
            else:
                border = "1px solid #DCDCDC"
            style = (f"{SERIF};font-size:10.5pt;line-height:1.24;"
                     f"border-bottom:{border};"
                     f"padding:{'3pt' if head else '3.75pt'} "
                     f"{'0' if num else '7.5pt'} "
                     f"{'3pt' if head else '3.75pt'} 0;"
                     f"text-align:{'right' if num else 'left'};"
                     f"vertical-align:{'bottom' if head else 'top'};"
                     f"width:{widths[ci] * 100:.0f}%")
            if "tot" in row["cls"]:
                style += ";border-top:1px solid #555555"
            if head:
                style += f";color:{BLUE};font-weight:bold"
            elif "tot" in row["cls"]:
                style += ";font-weight:bold"
            inner = runs_html(cell["runs"]).replace("\n", "<br>")
            tds.append(f'<td style="{style}">{inner}</td>')
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return ('<table style="border-collapse:collapse;width:100%;margin:1pt 0 8pt">'
            + "".join(trs) + "</table>"
            '<p style="font-size:4pt;margin:0">&nbsp;</p>')


if __name__ == "__main__":
    doc = ('<!doctype html><html><head><meta charset="utf-8">'
           "<title>Pavo Cloud — Technical Execution Report</title></head>"
           f'<body style="{BODY}">{build()}</body></html>')
    open(OUT, "w", encoding="utf-8").write(doc)
    print(f"wrote {OUT} ({len(doc)/1024:.0f} KB)")
