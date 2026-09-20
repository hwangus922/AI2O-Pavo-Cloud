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

BG = (1.0, 0xF9 / 255, 0xF9 / 255)          # #FFF9F9, sampled off the slides
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

# ============================================== appended financial slides ====
def new_slide():
    page = doc.new_page(width=W, height=H)
    page.draw_rect(page.rect, color=None, fill=BG)
    return page


def chip(page, text, x=49.8, y=154.4):
    f = font(BOLD)
    w = f.text_length(text, 10.8)
    page.draw_rect(pymupdf.Rect(x, y - 13.6, x + w + 17, y + 4.4),
                   color=None, fill=CHIP, radius=0.18)
    tw = pymupdf.TextWriter(page.rect)
    tw.append((x + 8.5, y), text, font=f, fontsize=10.8)
    tw.write_text(page, color=INK)


def title(page, text, y=119.8):
    tw = pymupdf.TextWriter(page.rect)
    tw.append((49.8, y), text, font=font(HEAVY), fontsize=36.8)
    tw.write_text(page, color=HEAD)


def heading(page, text, x, y, size=18.7):
    tw = pymupdf.TextWriter(page.rect)
    tw.append((x, y), text, font=font(HEAVY), fontsize=size)
    tw.write_text(page, color=HEAD)


def stat(page, num, label, x, y, size=34, lw=190):
    tw = pymupdf.TextWriter(page.rect)
    tw.append((x, y), num, font=font(HEAVY), fontsize=size)
    tw.write_text(page, color=BLUE)
    wrap(page, label, x, y + 19, 11.5, width=lw, leading=14.5)


def row(page, cells, y, size=13.7, bold=False, line=True):
    fx = BOLD if bold else REG
    for text, x, align in cells:
        f = font(fx)
        cx = x - f.text_length(text, size) if align == "r" else x
        tw = pymupdf.TextWriter(page.rect)
        tw.append((cx, y), text, font=f, fontsize=size)
        tw.write_text(page, color=HEAD if bold else INK)
    if line:
        page.draw_line(pymupdf.Point(49.8, y + 8.5), pymupdf.Point(910, y + 8.5),
                       color=RULE, width=0.5, stroke_opacity=0.35)


# ---- slide 11: how Pavo makes money ----------------------------------------
p = new_slide()
title(p, "How Pavo Makes Money")
chip(p, "BUSINESS MODEL")
for i, (price, what) in enumerate([
        ("$3.00", "per request, charged to the insurer"),
        ("$400", "per month, per medical practice"),
        ("$20,000", "per year, per insurer connection")]):
    x = 49.8 + i * 293
    p.draw_rect(pymupdf.Rect(x, 196, x + 264, 262), color=RULE, width=0.5,
                stroke_opacity=0.5, radius=0.03)
    tw = pymupdf.TextWriter(p.rect)
    tw.append((x + 18, 228), price, font=font(HEAVY), fontsize=25)
    tw.write_text(p, color=BLUE)
    wrap(p, what, x + 18, 249, 11.5, width=230, leading=14)

COLS = (600, 730, 880)
row(p, [("Source", 49.8, "l"), ("2026", COLS[0], "r"), ("2027", COLS[1], "r"),
        ("2028", COLS[2], "r")], 288, size=12.3, bold=True)
DATA = [("Medical practices served (average)", "55", "330", "1,400"),
        ("Requests processed", "171,600", "1,647,360", "8,736,000"),
        ("Fees per request, at $3.00", "$514,800", "$4,942,080", "$26,208,000"),
        ("Practice subscriptions, at $400/month", "$264,000", "$1,584,000", "$6,720,000"),
        ("Insurer connection fees, at $20,000/year", "$220,000", "$1,680,000", "$3,200,000")]
y = 288
for label, a, b, c in DATA:
    y += 31
    row(p, [(label, 49.8, "l"), (a, COLS[0], "r"), (b, COLS[1], "r"),
            (c, COLS[2], "r")], y, size=12.3)
y += 31
p.draw_line(pymupdf.Point(49.8, y - 21), pymupdf.Point(910, y - 21),
            color=RULE, width=0.7)
row(p, [("Total revenue", 49.8, "l"), ("$998,800", COLS[0], "r"),
        ("$8,206,080", COLS[1], "r"), ("$36,128,000", COLS[2], "r")],
    y, size=12.3, bold=True, line=False)
wrap(p, "The $3.00 fee is 85-92% below the $15-$40 an insurer spends handling a "
        "request by hand today, which is what makes the switch easy to justify.",
     49.8, 508, 11.5, width=860, leading=14)

# ---- slide 12: margin -------------------------------------------------------
p = new_slide()
title(p, "What It Costs, and What Is Left")
chip(p, "MARGIN")
for i, (n, l) in enumerate([("31%", "gross margin, 2026"),
                            ("82%", "gross margin, 2027"),
                            ("87%", "gross margin, 2028")]):
    stat(p, n, l, 49.8 + i * 293, 250, size=46, lw=240)
p.draw_line(pymupdf.Point(49.8, 300), pymupdf.Point(910, 300),
            color=RULE, width=0.5, stroke_opacity=0.5)
heading(p, "Servers are not the expense", 49.8, 345)
wrap(p, "Processing one request costs about six hundredths of a cent, because "
        "the deciding path uses no AI models at all.",
     49.8, 372, 13.7, width=400, leading=20)
heading(p, "Clinical staff are", 489.1, 345)
wrap(p, "Translating each insurer's published rules into the fixed rules the "
        "software applies is the largest line in every year, and the reason "
        "margins improve with scale rather than with technology.",
     489.1, 372, 13.7, width=420, leading=20)
wrap(p, "Year 1 is 31%, not break-even. Early customers need a great deal of "
        "hand-holding, and we would rather say so.",
     49.8, 500, 11.5, width=860, leading=14)

# ---- slide 13: unit economics ----------------------------------------------
p = new_slide()
title(p, "Cost to Win a Customer, and What One Is Worth")
chip(p, "UNIT ECONOMICS")
wrap(p, "Acquisition cost is what it costs in sales and marketing to sign one "
        "customer. Lifetime value is the profit that customer produces before "
        "they leave, stated here over three years, which is deliberately "
        "conservative.",
     49.8, 208, 13.7, width=860, leading=20)
UC = (640, 780, 905)
row(p, [("Measure", 49.8, "l"), ("Practice", UC[0], "r"), ("Insurer", UC[1], "r"),
        ("Blended", UC[2], "r")], 272, bold=True)
for i, (label, a, b, c) in enumerate([
        ("Cost to acquire one customer", "$6,000", "$22,000", "$6,699"),
        ("Value over three years", "$58,248", "$51,057", "$57,533"),
        ("Value per $1 spent acquiring", "$9.70", "$2.30", "$8.60"),
        ("Months to earn the cost back", "3.5", "15.2", "4.0")]):
    row(p, [(label, 49.8, "l"), (a, UC[0], "r"), (b, UC[1], "r"), (c, UC[2], "r")],
        306 + i * 34, line=(i < 3))
p.draw_rect(pymupdf.Rect(49.8, 452, 910, 520), color=None, fill=CHIP, radius=0.02)
wrap(p, "Read the insurer column honestly. At $2.30 back per $1 spent and fifteen "
        "months to recover it, insurer contracts do not pay for themselves as a "
        "product. We fund them anyway, because signing one insurer makes Pavo "
        "available to every practice that already submits to it. It is a "
        "distribution channel, not a profit centre.",
     66, 476, 12.3, width=828, leading=16)

# ---- slide 14: the ask ------------------------------------------------------
p = new_slide()
title(p, "We Are Asking For $8.0 Million")
chip(p, "THE ASK")
# cumulative cash: 0, -2.37M end 2026, -5.58M end 2027, +5.65M end 2028
ax, ay, aw = 70, 330, 380
p.draw_line(pymupdf.Point(ax - 14, ay), pymupdf.Point(ax + aw + 10, ay),
            color=RULE, width=0.6)
pts = [(ax, ay), (ax + aw * 0.31, ay + 52), (ax + aw * 0.64, ay + 96),
       (ax + aw, ay - 96)]
for i in range(len(pts) - 1):
    p.draw_line(pymupdf.Point(*pts[i]), pymupdf.Point(*pts[i + 1]),
                color=BLUE, width=2.4)
p.draw_circle(pymupdf.Point(*pts[2]), 4, color=None, fill=BLUE)
tw = pymupdf.TextWriter(p.rect)
tw.append((ax - 30, ay + 4), "$0", font=font(REG), fontsize=10)
for lbl, px in [("2026", pts[1][0] - 14), ("2027", pts[2][0] - 14), ("2028", pts[3][0] - 26)]:
    tw.append((px, ay + 16), lbl, font=font(REG), fontsize=10)
tw.write_text(p, color=RULE)
write(p, [("-$5.58M, late 2027", BOLD)], pts[2][0] - 56, pts[2][1] + 24, 11.5)
write(p, [("+$5.65M", BOLD)], pts[3][0] - 60, pts[3][1] - 10, 11.5)
wrap(p, "Cumulative cash. The raise covers the trough with roughly twelve months "
        "of cushion past breaking even.",
     49.8, 470, 11.5, width=410, leading=14)

for i, (h, s) in enumerate([
        ("The clinical rule library", "Our largest cost and the real barrier to a competitor."),
        ("Security certification", "No insurer signs without it."),
        ("Closing the gaps we listed", "Provider registry, multi-party ceremony, rule library.")]):
    yy = 224 + i * 62
    p.draw_line(pymupdf.Point(500, yy - 15), pymupdf.Point(500, yy + 28),
                color=BLUE, width=2.6)
    heading(p, h, 514, yy, size=14.5)
    wrap(p, s, 514, yy + 20, 11.5, width=396, leading=14)
wrap(p, "It is not a shopping list. The three largest spending lines across the "
        "plan, $7.46M of engineering, $5.67M of insurer business development and "
        "$1.72M of clinical staff encoding coverage rules, come to more than the "
        "raise on their own, and most of that is paid for out of revenue as it "
        "arrives.",
     500, 432, 11.5, width=410, leading=14)
wrap(p, "If all four of our main assumptions are wrong at once, 2028 revenue is "
        "$13.8 million rather than $36.1 million: a smaller company, but still a "
        "real one.",
     49.8, 516, 11.5, width=860, leading=14)

doc.save(OUT, garbage=3, deflate=True)
print(f"wrote {OUT} ({doc.page_count} slides, {os.path.getsize(OUT)//1024} KB)")
