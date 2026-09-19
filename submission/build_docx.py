"""Build a Word (.docx) copy of the Technical Execution Report.

The text, tables and figures are read out of report.html, so this file cannot
drift from the PDF. The .docx exists for one reason: Google Drive converts it
into a Google Doc with the images intact, whereas Drive's HTML importer throws
embedded images away.

    python build_docx.py
"""
from __future__ import annotations

import os
import re
from html.parser import HTMLParser

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "report.html")
OUT = os.path.join(HERE, "Pavo_Cloud_Technical_Execution_Report.docx")

BLUE = RGBColor(0x12, 0x74, 0xC4)
PX = 0.75                      # one CSS pixel in points
CONTENT_W = 6.5                # inches between the margins

# --------------------------------------------------------------------- parse ---
INLINE = {"em", "strong", "b", "i", "br", "tspan", "span", "code"}


class Block:
    def __init__(self, kind, **kw):
        self.kind = kind
        self.__dict__.update(kw)


class ReportParser(HTMLParser):
    """Turn report.html into a flat list of blocks the writer understands."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[Block] = []
        self.mode = None           # what kind of block we are inside
        self.runs: list[tuple] = []
        self.bold = 0
        self.ital = 0
        self.mono = 0
        self.in_body = False
        self.in_style = False
        self.in_svg = 0
        self.cls = ""
        # table state
        self.table = None
        self.row = None
        self.cell = None
        # figrow state
        self.figrow = None

    # -- helpers ---------------------------------------------------------
    def _flush(self):
        runs, self.runs = self.runs, []
        return [r for r in runs if r[0]]

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "body":
            self.in_body = True
            return
        if tag == "style":
            self.in_style = True
            return
        if not self.in_body:
            return
        if tag == "svg":
            self.in_svg += 1
            return
        if self.in_svg:
            return
        if tag in ("strong", "b"):
            self.bold += 1
        elif tag in ("em", "i"):
            self.ital += 1
        elif tag == "code":
            self.mono += 1
        elif tag == "br":
            self.runs.append(("\n", self.bold, self.ital, self.mono))
        elif tag in ("h2", "h3", "pre"):
            self.mode = tag
            self.runs = []
        elif tag in ("p", "div"):
            self.mode = "p"
            self.cls = a.get("class", "")
            self.runs = []
        elif tag == "img":
            self.figrow[-1]["img"] = a["src"]
        elif tag == "table":
            self.table = []
        elif tag == "tr":
            self.row = {"cells": [], "cls": a.get("class", "")}
        elif tag in ("td", "th"):
            self.cell = {"head": tag == "th", "cls": a.get("class", ""),
                         "width": a.get("style", "")}
            self.runs = []
        elif tag == "div" and "figrow" in a.get("class", ""):
            self.figrow = []

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
            return
        if tag == "svg":
            self.in_svg -= 1
            if self.in_svg == 0:
                self.blocks.append(Block("figure1"))
            return
        if self.in_svg or not self.in_body:
            return
        if tag in ("strong", "b"):
            self.bold -= 1
        elif tag in ("em", "i"):
            self.ital -= 1
        elif tag == "code":
            self.mono -= 1
        elif tag in ("h2", "h3"):
            self.blocks.append(Block(tag, runs=self._flush()))
            self.mode = None
        elif tag == "pre":
            self.blocks.append(Block("pre", text="".join(r[0] for r in self.runs)))
            self.runs = []
            self.mode = None
        elif tag in ("td", "th"):
            self.cell["runs"] = self._flush()
            self.row["cells"].append(self.cell)
            self.cell = None
        elif tag == "tr":
            self.table.append(self.row)
            self.row = None
        elif tag == "table":
            self.blocks.append(Block("table", rows=self.table))
            self.table = None
        elif tag == "p":
            runs = self._flush()
            if self.figrow is not None and "fcap" in self.cls:
                self.figrow[-1]["cap"] = runs
            elif runs:
                self.blocks.append(Block("p", runs=runs, cls=self.cls))
            self.mode = None
            self.cls = ""
        elif tag == "div":
            if self.figrow is not None and self.mode is None:
                pass
            runs = self._flush()
            if runs:
                self.blocks.append(Block("p", runs=runs, cls=self.cls))
            self.mode = None
            self.cls = ""

    def handle_data(self, data):
        if self.in_style or not self.in_body or self.in_svg:
            return
        if self.cell is not None or self.mode in ("h2", "h3", "p"):
            text = re.sub(r"\s+", " ", data)
            if text.strip() or (self.runs and text == " "):
                self.runs.append((text, self.bold, self.ital, self.mono))
        elif self.mode == "pre":
            self.runs.append((data, 0, 0, 0))


def parse(html_text: str) -> list[Block]:
    """Run the parser, handling the one construct it needs help with: figrow."""
    out: list[Block] = []
    # Pull the two-up figure row out first; everything else is linear.
    m = re.search(r'<div class="figrow">(.*?)\n</div>', html_text, re.S)
    figrow_html = m.group(1)
    srcs = re.findall(r'<img src="([^"]+)"', figrow_html)
    caps = re.findall(r'<p class="fcap">(.*?)</p>', figrow_html, re.S)
    figs = list(zip(srcs, caps))
    stripped = html_text[: m.start()] + "<!--FIGROW-->" + html_text[m.end():]

    p = ReportParser()
    p.feed(stripped)
    for b in p.blocks:
        out.append(b)
    # splice the figure row back in, in place of the marker paragraph
    idx = next(i for i, b in enumerate(out)
               if b.kind == "p" and b.runs and "screens below" in b.runs[0][0])
    out.insert(idx + 1, Block("figrow", figs=figs))
    return out


# --------------------------------------------------------------------- write ---
def _el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn("w:" + k), v)
    return e


def borders(el, **sides):
    """sides: bottom=('DCDCDC', 6) — colour and size in eighths of a point."""
    pr = el.get_or_add_tcPr() if el.tag.endswith("}tc") else el
    tag = "w:tcBorders" if el.tag.endswith("}tc") else "w:pBdr"
    b = pr.find(qn(tag))
    if b is None:
        b = OxmlElement(tag)
        pr.append(b)
    for side, spec in sides.items():
        colour, sz = spec
        e = b.find(qn("w:" + side))
        if e is None:
            e = OxmlElement("w:" + side)
            b.append(e)
        e.set(qn("w:val"), "single" if colour else "nil")
        e.set(qn("w:sz"), str(sz))
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), colour or "auto")


def shade(el, colour):
    pr = el.get_or_add_tcPr() if el.tag.endswith("}tc") else el
    s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear")
    s.set(qn("w:color"), "auto")
    s.set(qn("w:fill"), colour)
    pr.append(s)


def cell_margins(cell, top=0, bottom=0, left=0, right=0):
    tcPr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for name, val in (("top", top), ("start", left), ("bottom", bottom), ("end", right)):
        e = OxmlElement("w:" + name)
        e.set(qn("w:w"), str(int(val * 20)))      # points -> twips
        e.set(qn("w:type"), "dxa")
        mar.append(e)
    tcPr.append(mar)


def para(doc_or_cell, runs, *, size=12, italic=False, bold=False, align=None,
         before=0, after=0, line=None, keep=False, font="Times New Roman",
         colour=None, indent=(0, 0), first=None):
    p = doc_or_cell.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    if line:
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = Pt(line)
    if align is not None:
        p.alignment = align
    pf.keep_with_next = keep
    pf.left_indent, pf.right_indent = Inches(indent[0]), Inches(indent[1])
    for run in runs:
        text, b, i = run[0], run[1], run[2]
        mono = run[3] if len(run) > 3 else 0
        r = p.add_run(text)
        r.font.size = Pt(size * 0.93 if mono else size)
        r.font.bold = bold or bool(b)
        r.font.italic = italic or bool(i)
        if colour is not None:
            r.font.color.rgb = colour
        face = "Courier New" if mono else font
        if face != "Times New Roman":           # Normal style already carries it
            r.font.name = face
            font = face
            rpr = r._element.get_or_add_rPr()
            rf = OxmlElement("w:rFonts")
            for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                rf.set(qn(a), font)
            rpr.insert(0, rf)
    return p


def picture_border(run, colour="BBBBBB"):
    """Draw a hairline around the last picture in a run."""
    spPr = run._element.find(qn("w:drawing"))
    if spPr is None:
        return
    for sp in spPr.iter():
        if sp.tag.endswith("}spPr"):
            ns = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
            ln = sp.makeelement(ns + "ln", {"w": "9525"})
            fill = sp.makeelement(ns + "solidFill", {})
            clr = sp.makeelement(ns + "srgbClr", {"val": colour})
            fill.append(clr)
            ln.append(fill)
            sp.append(ln)
            break


def spacer(doc, pts):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(pts)
    r = p.add_run("")
    r.font.size = Pt(1)
    return p


def width_of(style_attr: str) -> float | None:
    m = re.search(r"width:\s*([\d.]+)%", style_attr or "")
    return float(m.group(1)) / 100 if m else None


def build():
    blocks = parse(open(SRC, encoding="utf-8").read())
    doc = Document()

    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(12)
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), "Times New Roman")
    if rf.getparent() is None:
        rpr.insert(0, rf)

    s = doc.sections[0]
    s.page_width, s.page_height = Inches(8.5), Inches(11)
    s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(1)

    body_line = 12 * 1.38                     # CSS line-height, in points
    seen_head = False

    for b in blocks:
        if b.kind == "p" and not seen_head:
            text = "".join(r[0] for r in b.runs)
            if text.startswith("Pavo Cloud") and len(text) < 20:
                para(doc, b.runs, size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
                     after=3 * PX, line=19)
                continue
            if "Technical Execution Report" in text:
                para(doc, b.runs, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER,
                     after=3 * PX, line=body_line)
                continue
            if "CFO" in text:
                para(doc, b.runs, align=WD_ALIGN_PARAGRAPH.CENTER,
                     after=20 * PX, line=body_line)
                continue

        if b.kind == "h2":
            seen_head = True
            para(doc, b.runs, bold=True, before=17 * PX, after=6 * PX,
                 line=body_line, keep=True)
        elif b.kind == "h3":
            para(doc, b.runs, bold=True, before=14 * PX, after=5 * PX,
                 line=body_line, keep=True)
        elif b.kind == "p":
            if "fcap" in b.cls:
                para(doc, b.runs, italic=True, size=10.5, before=3 * PX,
                     after=10 * PX, line=13)
            elif "cap" in b.cls:
                para(doc, b.runs, italic=True, before=10 * PX, after=4 * PX,
                     line=body_line, keep=True)
            else:
                para(doc, b.runs, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                     after=8 * PX, line=body_line)
        elif b.kind == "pre":
            write_pre(doc, b.text)
        elif b.kind == "table":
            write_table(doc, b.rows)
        elif b.kind == "figure1":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6 * PX)
            p.paragraph_format.space_after = Pt(3 * PX)
            p.paragraph_format.keep_with_next = True
            r = p.add_run()
            r.add_picture(os.path.join(HERE, "assets", "fig1.png"),
                          width=Inches(CONTENT_W))
        elif b.kind == "figrow":
            write_figrow(doc, b.figs)

    doc.save(OUT)
    print(f"wrote {OUT} ({os.path.getsize(OUT) / 1024:.0f} KB)")
    slim(OUT)


def write_pre(doc, text):
    lines = text.strip("\n").split("\n")
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(4 * PX)
    pf.space_after = Pt(3 * PX)
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(8.4 * 1.35)
    pf.left_indent = Inches(0.08)
    pf.right_indent = Inches(0.08)
    pf.keep_together = True
    for i, ln in enumerate(lines):
        r = p.add_run(("\n" if i else "") + ln)
        r.font.name = "Courier New"
        r.font.size = Pt(8.4)
        rpr = r._element.get_or_add_rPr()
        rf = OxmlElement("w:rFonts")
        for a in ("w:ascii", "w:hAnsi", "w:cs"):
            rf.set(qn(a), "Courier New")
        rpr.insert(0, rf)
        t = r._element.find(qn("w:t"))
        if t is not None:
            t.set(qn("xml:space"), "preserve")
    ppr = p._element.get_or_add_pPr()
    shade(ppr, "F4F4F4")
    borders(ppr, top=("CCCCCC", 6), bottom=("CCCCCC", 6),
            left=("CCCCCC", 6), right=("CCCCCC", 6))
    return p


def write_table(doc, rows):
    ncols = max(len(r["cells"]) for r in rows)
    head = rows[0]
    widths = []
    for i in range(ncols):
        c = head["cells"][i] if i < len(head["cells"]) else {}
        widths.append(width_of(c.get("width", "")))
    free = [i for i, w in enumerate(widths) if w is None]
    rest = 1 - sum(w for w in widths if w)
    for i in free:
        widths[i] = rest / len(free)

    t = doc.add_table(rows=0, cols=ncols)
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    t.autofit = False
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    ind = OxmlElement("w:tblInd")
    ind.set(qn("w:w"), "0")
    ind.set(qn("w:type"), "dxa")
    tblPr.append(ind)

    last = len(rows) - 1
    for ri, row in enumerate(rows):
        tr = t.add_row()
        trPr = tr._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)
        for ci, cell in enumerate(row["cells"]):
            tc = tr.cells[ci]
            tc.width = Inches(CONTENT_W * widths[ci])
            tc._tc.remove(tc._tc.find(qn("w:p")))
            right = 0 if "n" in cell["cls"] else 10 * PX
            head_row = cell["head"]
            cell_margins(tc, top=4 * PX if head_row else 5 * PX,
                         bottom=4 * PX if head_row else 5 * PX,
                         left=0, right=right)
            if head_row:
                borders(tc._tc, bottom=("555555", 6))
            elif ri == last:
                borders(tc._tc, bottom=("000000", 6))
            else:
                borders(tc._tc, bottom=("DCDCDC", 6))
            if "tot" in row["cls"]:
                borders(tc._tc, top=("555555", 6))
            align = (WD_ALIGN_PARAGRAPH.RIGHT if "n" in cell["cls"]
                     else WD_ALIGN_PARAGRAPH.LEFT)
            # a cell can carry a forced line break (Table 3)
            chunks, cur = [], []
            for run in cell["runs"]:
                if run[0] == "\n":
                    chunks.append(cur)
                    cur = []
                else:
                    cur.append(run)
            chunks.append(cur)
            for k, ch in enumerate(chunks):
                para(tc, ch, size=10.5, align=align,
                     after=0, line=10.5 * 1.22,
                     bold=head_row or "tot" in row["cls"],
                     colour=BLUE if head_row else None)
    spacer(doc, 11 * PX)


def write_figrow(doc, figs):
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    t.autofit = False
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    ind = OxmlElement("w:tblInd")
    ind.set(qn("w:w"), "0")
    ind.set(qn("w:type"), "dxa")
    tblPr.append(ind)
    names = {"assets/demo_complete_print.jpg": "demo_complete_print.jpg",
             "assets/dashboard_print.jpg": "dashboard_print.jpg"}
    for ci, (src, cap) in enumerate(figs):
        tc = t.rows[0].cells[ci]
        tc.width = Inches(3.10 if ci == 0 else 3.40)
        tc._tc.remove(tc._tc.find(qn("w:p")))
        cell_margins(tc, right=10 * PX if ci == 0 else 0,
                     left=10 * PX if ci == 1 else 0)
        p = tc.add_paragraph()
        p.paragraph_format.space_after = Pt(4 * PX)
        p.paragraph_format.space_before = Pt(0)
        r = p.add_run()
        r.add_picture(os.path.join(HERE, "assets", names[src]),
                      width=Inches(3.03 if ci == 0 else 3.32))
        picture_border(r)
        runs = [(re.sub(r"<[^>]+>", "", cap).replace("&mdash;", "—")
                 .replace("&nbsp;", " ").strip(), 0, 0)]
        para(tc, runs, size=9.5, italic=True, after=0, line=11.5)
    spacer(doc, 4)




# ------------------------------------------------------------------- slim ---
def slim(path: str):
    """Strip the parts of Word's default template this document never uses.

    The upload has to travel as one base64 blob, so every kilobyte of boilerplate
    is a kilobyte less room for the figures.
    """
    import re as _re
    import shutil
    import zipfile

    drop_exact = {
        "word/stylesWithEffects.xml",
        "word/numbering.xml",
        "docProps/thumbnail.jpeg",
        "customXml/item1.xml",
        "customXml/itemProps1.xml",
        "customXml/_rels/item1.xml.rels",
    }
    keep_styles = {"Normal", "DefaultParagraphFont", "TableNormal", "NoList"}

    src = zipfile.ZipFile(path)
    parts = {i.filename: src.read(i.filename) for i in src.infolist()}
    src.close()

    for name in list(parts):
        if name in drop_exact:
            del parts[name]

    # styles.xml: keep the document defaults and the four styles actually used
    s = parts["word/styles.xml"].decode("utf-8")
    s = _re.sub(r"<w:latentStyles.*?</w:latentStyles>", "", s, flags=_re.S)
    s = _re.sub(r"<w:latentStyles[^>]*/>", "", s)

    def keep(m):
        sid = _re.search(r'w:styleId="([^"]+)"', m.group(0))
        return m.group(0) if sid and sid.group(1) in keep_styles else ""

    s = _re.sub(r"<w:style [^>]*>.*?</w:style>", keep, s, flags=_re.S)
    s = _re.sub(r'(<w:docDefaults>.*?<w:rFonts[^/]*?)/>',
                lambda m: _re.sub(r'w:(ascii|hAnsi|cs|eastAsia)="[^"]*"',
                                  lambda n: f'w:{n.group(1)}="Times New Roman"', m.group(1)) + "/>",
                s, count=1, flags=_re.S)
    parts["word/styles.xml"] = s.encode("utf-8")

    # drop the relationships that pointed at the removed parts
    for rels in ("_rels/.rels", "word/_rels/document.xml.rels"):
        r = parts[rels].decode("utf-8")
        r = _re.sub(
            r'<Relationship [^>]*Target="[^"]*'
            r'(stylesWithEffects|numbering|thumbnail|item1)[^"]*"[^>]*/>', "", r)
        parts[rels] = r.encode("utf-8")

    ct = parts["[Content_Types].xml"].decode("utf-8")
    for gone in ("stylesWithEffects", "numbering", "thumbnail", "item1", "itemProps1"):
        ct = _re.sub(r'<Override PartName="[^"]*' + gone + r'[^"]*"[^>]*/>', "", ct)
    parts["[Content_Types].xml"] = ct.encode("utf-8")

    tmp = path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in parts.items():
            z.writestr(name, data)
    shutil.move(tmp, path)
    print(f"slimmed to {os.path.getsize(path) / 1024:.0f} KB")


if __name__ == "__main__":
    build()
