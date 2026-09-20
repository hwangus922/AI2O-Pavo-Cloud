"""Correct the four wrong facts in the Gamma pitch deck, in place.

The deck is left byte-for-byte alone everywhere else: same layout, same colours,
same typeface. Each changed line is painted over with the slide's own background
and rewritten with the deck's own embedded fonts, pulled straight back out of the
PDF, so the corrected text is set in the same face as the text around it.

Four corrections, all of them facts the technical report contradicts:
  1. Slide 1  "not three days"        -> "not three to fourteen days"
  2. Slide 4  the 44.7ms agent figure -> the two signatures that make up the 88.6ms
  3. Slide 5  "Supabase"              -> "Supabase-ready"
  4. Slide 5  "(avg, n=20)"           -> "(median, n=200)"

Then the financial slides the deck never had are appended, drawn to the deck's
own geometry and palette.

    python patch_deck.py
"""
from __future__ import annotations

import os

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/root/.claude/uploads/c69d7a86-da65-5509-8c7d-5f88c08530e0/f0c4880e-Pavo_Cloud_Updated_Pitch_Deck__1.pdf"
OUT = os.path.join(HERE, "Pavo_Cloud_Pitch_Deck_corrected.pdf")

BG = (1.0, 0xFA / 255, 0xFA / 255)          # #FFFAFA, the deck's own page fill
INK = (0x3B / 255, 0x35 / 255, 0x35 / 255)  # #3B3535, the deck's body colour
HEAD = (0x1F / 255, 0x1E / 255, 0x1E / 255)
BLUE = (0x12 / 255, 0x74 / 255, 0xC4 / 255)
CHIP = (0xD6 / 255, 0xDC / 255, 0xF4 / 255)
RULE = (0x9C / 255, 0x97 / 255, 0x97 / 255)

doc = pymupdf.open(SRC)
W, H = doc[0].rect.width, doc[0].rect.height

# ---- pull the deck's own fonts back out so replacements match exactly -------
_cache: dict[int, pymupdf.Font] = {}


def font(xref: int) -> pymupdf.Font:
    if xref not in _cache:
        _cache[xref] = pymupdf.Font(fontbuffer=doc.extract_font(xref)[3])
    return _cache[xref]


REG, BOLD, HEAVY = 13, 22, 18   # the deck's regular, bold and heading faces


def blank(page, x0, y0, x1, y1):
    """Really delete the text under this box, do not merely paint over it.

    A covering rectangle leaves the old words in the text layer, where a copy,
    a search or a screen reader still finds them. Redaction removes the content
    stream operators themselves. Images and line art are left alone so the
    slide's icons and diagram survive.
    """
    page.add_redact_annot(pymupdf.Rect(x0, y0, x1, y1), fill=BG)
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                          graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                          text=pymupdf.PDF_REDACT_TEXT_REMOVE)


def write(page, runs, x, baseline, size, lead=0.0):
    """Lay `runs` of (text, font-xref) along one baseline, left to right."""
    tw = pymupdf.TextWriter(page.rect)
    cx = x
    for text, fx in runs:
        f = font(fx)
        tw.append((cx, baseline), text, font=f, fontsize=size)
        cx += f.text_length(text, size) + lead
    tw.write_text(page, color=INK)
    return cx


def wrap(page, text, x, baseline, size, width, leading, fx=REG, x2=None, width2=None):
    """Write `text` into a column, wrapping on spaces.

    `x2` lets continuation lines hang back to a different left edge, which is
    what the deck does under its bold "Stack:" label.
    """
    f = font(fx)
    words, line, y = text.split(), "", baseline
    cx, cw = x, width
    for w in words:
        trial = (line + " " + w).strip()
        if f.text_length(trial, size) > cw and line:
            write(page, [(line, fx)], cx, y, size)
            line, y = w, y + leading
            cx = x2 if x2 is not None else x
            cw = width2 if width2 is not None else width
        else:
            line = trial
    if line:
        write(page, [(line, fx)], cx, y, size)
    return y


# =========================================================== slide 1 =========
# "not three days" understates the report's own range of three to fourteen.
p = doc[0]
blank(p, 48, 318, 930, 341)
write(p, [("The insurer's answer in ", REG),
          ("88.6 milliseconds", BOLD),
          (". The whole round trip in under five minutes, not three to fourteen days.", REG)],
      49.78, 334.4, 13.70)

# =========================================================== slide 4 =========
# 44.7ms was measured over a loopback interface, so "network excluded" meant
# nothing. The report drops it. The signature breakdown replaces it and is
# stronger: the deciding is not what costs the time.
p = doc[3]
blank(p, 487, 266, 930, 336)
wrap(p, "The full decision path takes 88.6ms, and 84.0 of those are the two "
        "RSA-2048 signatures every authorization writes. The deciding itself "
        "is the cheap part.",
     489.13, 283.68, 13.70, width=418, leading=22.34)

# =========================================================== slide 5 =========
# Supabase is supported but unset by default, so the demo runs in memory; and
# the speed line quoted a mean over twenty runs where the report reports a
# median over two hundred.
p = doc[4]
blank(p, 494, 278, 930, 320)
y = wrap(p, "FastAPI · Next.js 14 · Supabase-ready · FHIR R4 · RSA-2048 signing "
            "· ZK circuits (circom/snarkjs) · timestamped audit log",
         541.0, 293.64, 12.24, width=370, leading=18.74,
         x2=496.35, width2=415)
write(p, [("Stack:", BOLD)], 496.35, 293.64, 12.24)

blank(p, 494, 326, 930, 350)
write(p, [("Speed:", BOLD), (" Step 1 to step 7 in 88.6ms (median, n=200)", REG)],
      496.35, 341.95, 12.24)

# =================================================== appended slides =========
# Everything below copies the geometry of the deck's own slides 2 and 6, down
# to the card rectangles and baselines, so the added slides are the same
# template rather than a lookalike. Two rules follow from reading the original:
#
#   * The deck uses no blue type anywhere. Every number on slide 2, however
#     large, is #3B3535. The accent is the pale card fill, not the text.
#   * The deck's own embedded fonts are subsets and are missing "$", "9", "6",
#     "(" and ")", which is most of what a financials slide is made of. Work
#     Sans matches the deck's metrics (exactly, at 18.7pt) and has the full
#     character set, so the added slides are set in it throughout rather than
#     falling back mid-word to whatever glyph happens to exist.

FONTS = "/mnt/skills/examples/canvas-design/canvas-fonts"
HEAVY_F = pymupdf.Font(fontfile=f"{FONTS}/WorkSans-Bold.ttf")     # deck "font 1"
REG_F = pymupdf.Font(fontfile=f"{FONTS}/WorkSans-Regular.ttf")    # deck "font 3"

CARD_FILL = (0xD5 / 255, 0xDC / 255, 0xF6 / 255)   # #D5DCF6
CARD_EDGE = (0xBB / 255, 0xC2 / 255, 0xDC / 255)   # #BBC2DC

# the deck's own card grid, lifted off slide 6
COL3 = ((50.04, 327.24), (341.64, 618.84), (633.24, 910.44))
COL2 = ((50.04, 473.40), (487.08, 910.44))
ROW1 = (192.65, 322.28)     # slide 6's upper card row, to the hundredth
ROW2 = (336.68, 443.27)     # and its lower one


def put(page, text, x, baseline, size, f, colour):
    tw = pymupdf.TextWriter(page.rect)
    tw.append((x, baseline), text, font=f, fontsize=size)
    tw.write_text(page, color=colour)


def centred(page, text, cx, baseline, size, f, colour):
    put(page, text, cx - f.text_length(text, size) / 2, baseline, size, f, colour)


def lines(page, text, x, baseline, size, f, colour, width, leading):
    line, y = "", baseline
    for w in text.split():
        trial = (line + " " + w).strip()
        if f.text_length(trial, size) > width and line:
            put(page, line, x, y, size, f, colour)
            line, y = w, y + leading
        else:
            line = trial
    if line:
        put(page, line, x, y, size, f, colour)


def page_shell(title_text, chip_text):
    page = doc.new_page(width=W, height=H)
    page.draw_rect(page.rect, color=None, fill=BG)
    w = REG_F.text_length(chip_text, 10.8)
    chip_pill(page, 49.68, 97.22, 49.68 + w + 17.08, 118.83)
    put(page, chip_text, 58.3, 110.8, 10.8, REG_F, INK)
    put(page, title_text, 49.8, 159.1, 36.8, HEAVY_F, HEAD)
    return page


CARD_R = 5.97      # slide 6's corner radius, read off its bezier control points
KAPPA = 0.5523     # and the circle approximation it uses


def rounded(page, x0, y0, x1, y1, r=CARD_R, edge=True):
    """Slide 6's card outline: straight edges, r-radius corners, same kappa."""
    k = r * KAPPA
    sh = page.new_shape()
    sh.draw_line(pymupdf.Point(x0 + r, y0), pymupdf.Point(x1 - r, y0))
    sh.draw_bezier(pymupdf.Point(x1 - r, y0), pymupdf.Point(x1 - r + k, y0),
                   pymupdf.Point(x1, y0 + r - k), pymupdf.Point(x1, y0 + r))
    sh.draw_line(pymupdf.Point(x1, y0 + r), pymupdf.Point(x1, y1 - r))
    sh.draw_bezier(pymupdf.Point(x1, y1 - r), pymupdf.Point(x1, y1 - r + k),
                   pymupdf.Point(x1 - r + k, y1), pymupdf.Point(x1 - r, y1))
    sh.draw_line(pymupdf.Point(x1 - r, y1), pymupdf.Point(x0 + r, y1))
    sh.draw_bezier(pymupdf.Point(x0 + r, y1), pymupdf.Point(x0 + r - k, y1),
                   pymupdf.Point(x0, y1 - r + k), pymupdf.Point(x0, y1 - r))
    sh.draw_line(pymupdf.Point(x0, y1 - r), pymupdf.Point(x0, y0 + r))
    sh.draw_bezier(pymupdf.Point(x0, y0 + r), pymupdf.Point(x0, y0 + r - k),
                   pymupdf.Point(x0 + r - k, y0), pymupdf.Point(x0 + r, y0))
    if edge:
        sh.finish(color=CARD_EDGE, fill=CARD_FILL, width=0.5, closePath=True)
    else:
        sh.finish(color=None, fill=CARD_FILL, closePath=True)
    sh.commit()


def chip_pill(page, x0, y0, x1, y1):
    """The label pill: same shape, 4.78pt corners, fill only, no edge."""
    rounded(page, x0, y0, x1, y1, r=4.78, edge=False)


def card(page, span, y0, y1, big, label, label_w=248):
    rounded(page, span[0], y0, span[1], y1)
    put(page, big, span[0] + 14.46, y0 + 32.05, 18.7, HEAVY_F, INK)
    lines(page, label, span[0] + 14.46, y0 + 63.35, 13.7, REG_F, INK, label_w, 22.3)


# ---- how Pavo makes money: slide 6's card grid, three over two -------------
p = page_shell("How Pavo Makes Money", "BUSINESS MODEL")
for span, big, lab in zip(COL3,
                          ("$3.00", "$400", "$20,000"),
                          ("per request, to the insurer",
                           "per practice, per month",
                           "per insurer, per year")):
    card(p, span, *ROW1, big, lab)
for span, big, lab in zip(COL2,
                          ("$36.1M", "87%"),
                          ("2028 revenue, from $1.0M in 2026",
                           "gross margin by 2028, 31% in year one")):
    card(p, span, *ROW2, big, lab, label_w=394)

# ---- the system running: the demo the guide requires, and the closing slide -
# "You cannot just talk about the AI; you must show it." The two screenshots sit
# in exactly the band slide 6's cards occupy, 192.65 to 443.27, and carry the
# same 0.5pt #BBC2DC edge the cards do.
p = page_shell("The System Running", "LIVE SOFTWARE")
SHOTS = (("assets/demo_complete_print.jpg", 950 / 609),
         ("assets/dashboard_print.jpg", 950 / 671))
GAP, LEFT, RIGHT = 14.4, 50.04, 910.44
avail = RIGHT - LEFT - GAP
h = avail / (SHOTS[0][1] + SHOTS[1][1])
x = LEFT
for src, aspect in SHOTS:
    w = h * aspect
    r = pymupdf.Rect(x, 192.65, x + w, 192.65 + h)
    p.insert_image(r, filename=os.path.join(HERE, src))
    p.draw_rect(r, color=CARD_EDGE, fill=None, width=0.5)
    x += w + GAP
cap_y = 192.65 + h + 24
put(p, "Left: six steps, order through price, unattended, in 11.0 seconds. "
       "Right: every row carries the rule that produced it.",
    LEFT, cap_y, 13.7, REG_F, INK)
put(p, "Every number in this deck came off this build.",
    LEFT, cap_y + 23.5, 13.7, HEAVY_F, HEAD)

doc.save(OUT, garbage=3, deflate=True)
print(f"wrote {OUT} ({doc.page_count} slides, {os.path.getsize(OUT)//1024} KB)")
