#!/usr/bin/env python3
"""Draw the front page of THE WORLD TODAY for Monday 23 November 2026.

This program paints the whole newspaper page from scratch with Pillow:
masthead and date, a three-line red headline band, a UTC timeline strip,
a numbers strip, three illustrated lead stories, eleven secondary stories,
a schematic world map with numbered pins, twenty-three briefs, a
date-check box and a footer. Every story lives in the data tables below,
so running the program regenerates the same page.

Usage:
    python3 main.py                          # writes ./entry.png and $MAKEFUN_OUTPUT_DIR/entry.png
    MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import hashlib
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PAGE_W = 1024
PAGE_H = 1024
MARGIN = 14
CONTENT_W = PAGE_W - 2 * MARGIN

IVORY = (250, 248, 245)
INK = (26, 26, 26)
CRIMSON = (158, 27, 35)
GREEN = (30, 122, 52)
OCHRE = (154, 107, 14)
NAVY = (31, 42, 90)
SKY = (191, 227, 242)
LAND = (232, 217, 176)
GREY = (110, 110, 110)
FAINT = (205, 200, 192)
DARKPANEL = (22, 22, 34)
WHITE = (255, 255, 255)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def _load_font(filename, size):
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, filename), size)
    except OSError:
        try:
            return ImageFont.load_default(size)
        except TypeError:
            return ImageFont.load_default()


def serif(size, bold=True):
    return _load_font("DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf", size)


def sans(size, bold=False):
    return _load_font("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)


def wrap_text(font, text, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if font.getlength(trial) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_lines(draw, x, y, lines, font, fill, leading):
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += leading
    return y


def draw_centered(draw, cx, y, text, font, fill):
    w = font.getlength(text)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def chip_width(label, size=10):
    return int(sans(size, bold=True).getlength(label)) + 12


def draw_chip(draw, x, y, label, bg, size=10, height=15):
    f = sans(size, bold=True)
    pad = 6
    w = int(f.getlength(label)) + 2 * pad
    try:
        draw.rounded_rectangle([x, y, x + w, y + height], radius=4, fill=bg)
    except AttributeError:
        draw.rectangle([x, y, x + w, y + height], fill=bg)
    draw.text((x + pad, y + (height - size) / 2 - 1), label, font=f, fill=WHITE)
    return w


def draw_rule(draw, y, width=2):
    draw.line([(MARGIN, y), (PAGE_W - MARGIN, y)], fill=INK, width=width)


UTC_MARKS = [
    ("06:27", "Asia sell-off eases"),
    ("07:10", "Merkury sunk"),
    ("09:46", "US futures rally"),
    ("11:10", "Libya: what we know"),
    ("12:40", "Paredes collapses"),
    ("13:04", "Iran vows 'all means'"),
    ("13:36", "COP31 'worst ever'"),
]

NUMBERS = [
    ("258", "House seats, Democrats"),
    ("14", "killed around Kyiv"),
    ("7", "tankers hit since 16 Nov"),
    ("24", "dead in Indonesia fire"),
    ("$93.5bn", "Anthropic IPO"),
    ("99%", "of Gaza contaminated"),
]

LEADS = [
    {
        "art": "hormuz",
        "place": "STRAIT OF HORMUZ",
        "kicker": "MIDDLE EAST · HORMUZ",
        "chip": ("REPORTED", OCHRE),
        "headline": "Iran hits Bahrain and mines two tankers",
        "deck": "Tehran strikes US bases; 7 tankers hit since 16 Nov. Trump 'inclined' to resume strikes.",
        "source": "AP",
    },
    {
        "art": "cop",
        "place": "COP31 · ANTALYA",
        "kicker": "CLIMATE · ANTALYA",
        "chip": ("CONFIRMED", GREEN),
        "headline": "COP31 collapse: 'worst ever' summit",
        "deck": "Australia under fire; Saudis accused of hijacking the talks. First collapse since 2009.",
        "source": "Reuters",
    },
    {
        "art": "nato",
        "place": "NATO · BRUSSELS",
        "kicker": "EUROPE · BRUSSELS",
        "chip": ("CONFIRMED", GREEN),
        "headline": "Russian missiles fell in Poland",
        "deck": "Allies meet Monday in Brussels. Rutte: 'We will defend every inch of Polish territory.'",
        "source": "Reuters",
    },
]

SECONDARIES_TOP = [
    {"art": "kyiv", "place": "KYIV", "kicker": "UKRAINE", "chip": ("CONFIRMED", GREEN),
     "headline": "Russian strikes kill 14 around Kyiv", "deck": "10 dead in Dymer."},
    {"art": "merkury", "place": "MERKURY", "kicker": "LIBYA", "chip": ("CONFIRMED", GREEN),
     "headline": "Zelensky: we sank the Merkury", "deck": "7 sea drones; Angara hit too."},
    {"art": "usa", "place": "USA", "kicker": "USA", "chip": ("REPORTED", OCHRE),
     "headline": "Democrats take 258 House seats", "deck": "Largest majority in decades."},
    {"art": "markets", "place": "NASDAQ", "kicker": "MARKETS", "chip": ("CONFIRMED", GREEN),
     "headline": "Nasdaq fell 10% in a week", "deck": "Futures rebound 2.8%."},
    {"art": "tech", "place": "NVDA", "kicker": "TECH", "chip": ("CONFIRMED", GREEN),
     "headline": "Nvidia falls 14% in a day", "deck": "Huang ousted, SEC inquiry."},
    {"art": "indonesia", "place": "INDONESIA", "kicker": "INDONESIA", "chip": ("CONFIRMED", GREEN),
     "headline": "Factory fire kills 24", "deck": "~30 still missing in Serang."},
]

SECONDARIES_BOTTOM = [
    {"art": "gaza", "place": "GAZA", "kicker": "GAZA", "chip": ("REPORTED", OCHRE),
     "headline": "Gaza a 'toxic wasteland'", "deck": "99% contaminated: Oxfam."},
    {"art": "mexico", "place": "MEXICO", "kicker": "MEXICO", "chip": ("CONFIRMED", GREEN),
     "headline": "'Chapo Isidro' captured", "deck": "Sinaloa cartel leader seized."},
    {"art": "kerch", "place": "KERCH", "kicker": "UKRAINE", "chip": ("REPORTED", OCHRE),
     "headline": "Kerch Bridge crippled", "deck": "Road shut; one track left."},
    {"art": "westbank", "place": "WEST BANK", "kicker": "WEST BANK", "chip": ("REPORTED", OCHRE),
     "headline": "Settler arson is 'Jewish terrorism'", "deck": "PM-elect Eisenkot's words."},
    {"art": "saudi", "place": "RABIGH", "kicker": "SAUDI ARABIA", "chip": ("CLAIMED", CRIMSON),
     "headline": "Houthis claim Rabigh refinery hit", "deck": "Riyadh has not confirmed it."},
]

BRIEFS = [
    (15, "Trump: Iran wants a deal, but not one 'acceptable' to him."),
    (16, "Vance: 'not say if he would authorise strikes on Iran.'"),
    (17, "Bahrain: 2 hurt in Iran strike on site; US warning."),
    (18, "CLAIMED: IRGC claims it shot down a 20th US MQ-1 drone."),
    (19, "Trump claims Iran killed 81,000 protesters — not verified."),
    (20, "New Russia–US–Ukraine talks 'soon', maybe in Abu Dhabi."),
    (21, "Russia fires 153 drones; Kyiv claims 2,471 troops lost."),
    (22, "Russia captures Sosnovy Bor in Kharkiv region."),
    (23, "Denmark accuses Russian intel of a plot to kill a rapper."),
    (24, "Poland: Kh-101 missile was built in late 2026; no Article 4."),
    (25, "S. Korea education minister quits over AI cheating scandal."),
    (26, "China warns citizens off Mount Fuji; $75,000 reward."),
    (27, "Bangladesh: Hasina will be jailed if she returns from India."),
    (28, "Oregon and Virginia sue SpaceX over AI safety claims."),
    (29, "Belgium anti-austerity strike paralyses transport."),
    (30, "Brazil storm kills 5 and injures 265 in Tupã."),
    (31, "Sudan: drones hit homes, UN site in Khartoum; 3 staff hurt."),
    (32, "Nigeria boat capsize toll rises to 24."),
    (33, "Argentina's Paredes collapses in post-match interview."),
    (34, "Anthropic's $93.5bn IPO: shares fell 8.5% on Friday."),
    (35, "Bitcoin $61,417, up 0.9%; gold jumps 3%."),
    (36, "Brent crude near $91.70 a barrel, down 1%."),
    (37, "Nepal's PM Balendra Shah visits India and meets Modi."),
]

REGION_LINE = "EUROPE 10 · MIDDLE EAST 7 · ASIA 6 · AMERICAS 11 · AFRICA 3"

# (story number, x, y) inside the 416 x 150 map box
PINS = [
    (6, 75, 38), (11, 58, 68), (3, 244, 32), (4, 262, 36),
    (24, 228, 22), (12, 268, 48), (2, 248, 50), (5, 232, 68),
    (10, 262, 60), (1, 296, 64), (17, 278, 72), (14, 262, 86),
    (31, 248, 96), (27, 332, 62), (9, 352, 100),
]

CONTINENTS = [
    [(28, 18), (95, 10), (150, 18), (158, 55), (120, 72), (75, 66), (40, 50)],
    [(105, 82), (140, 78), (158, 105), (140, 132), (112, 128), (98, 100)],
    [(205, 18), (248, 14), (258, 38), (232, 48), (208, 38)],
    [(210, 55), (252, 50), (268, 82), (250, 112), (222, 100), (205, 75)],
    [(262, 14), (400, 10), (408, 55), (360, 72), (300, 60), (262, 40)],
    [(330, 102), (392, 98), (398, 122), (340, 128)],
]

MAP_LABELS = [
    ("N. AMERICA", 28, 4), ("EUROPE", 206, 4), ("ASIA", 336, 4),
    ("S. AMERICA", 96, 134), ("AUSTRALIA", 330, 134),
]


def _label_strip(d, x, y, w, h, text):
    """Dark strip with a white place label at the bottom of an art panel."""
    f = sans(11, bold=True)
    d.rectangle([x, y + h - 16, x + w, y + h], fill=(20, 20, 20))
    d.text((x + 6, y + h - 14), text, font=f, fill=WHITE)


def _corner_label(d, x, y, text, fill=WHITE):
    d.text((x + 5, y + 3), text, font=sans(10, bold=True), fill=fill)


def art_hormuz(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SKY)
    d.ellipse([x + w - 26, y + 6, x + w - 10, y + 22], fill=(255, 140, 0))
    sea_y = y + int(h * 0.62)
    d.rectangle([x, sea_y, x + w, y + h], fill=(46, 110, 158))
    d.rectangle([x + 12, sea_y + 6, x + int(w * 0.62), sea_y + 16], fill=(30, 30, 30))
    d.rectangle([x + int(w * 0.22), sea_y - 4, x + int(w * 0.22) + 18, sea_y + 6], fill=(30, 30, 30))
    d.rectangle([x + int(w * 0.48), sea_y - 2, x + int(w * 0.48) + 8, sea_y + 6], fill=(30, 30, 30))
    for mx, my in ((0.72, 0.80), (0.86, 0.74)):
        cx, cy = x + int(w * mx), y + int(h * my)
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(15, 15, 15))
    _label_strip(d, x, y, w, h, "STRAIT OF HORMUZ")


def art_cop(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(226, 240, 226))
    cx, cy, r = x + w // 2, y + h // 2 - 4, 19
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 140, 200))
    d.ellipse([cx - 12, cy - 10, cx + 2, cy + 2], fill=(90, 170, 90))
    d.ellipse([cx + 2, cy + 4, cx + 14, cy + 14], fill=(90, 170, 90))
    d.line([(cx - 14, cy - 12), (cx - 2, cy + 2), (cx + 6, cy - 6), (cx + 14, cy + 10)],
           fill=CRIMSON, width=2)
    _label_strip(d, x, y, w, h, "COP31 · ANTALYA")


def art_nato(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=NAVY)
    cx, cy = x + w // 2, y + h // 2 - 4
    star = [(cx, cy - 22), (cx + 5, cy - 5), (cx + 22, cy), (cx + 5, cy + 5),
            (cx, cy + 22), (cx - 5, cy + 5), (cx - 22, cy), (cx - 5, cy - 5)]
    d.polygon(star, fill=WHITE)
    _label_strip(d, x, y, w, h, "NATO · BRUSSELS")


def art_kyiv(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=DARKPANEL)
    d.arc([x + w - 26, y + 2, x + w - 10, y + 18], start=200, end=340,
          fill=(255, 220, 120), width=2)
    bx, by = x + int(w * 0.30), y + 12
    for dx, dy in ((-8, 0), (8, 0), (0, -8), (0, 8), (-6, -6), (6, 6), (-6, 6), (6, -6)):
        d.line([(bx, by), (bx + dx, by + dy)], fill=(255, 140, 0), width=2)
    d.ellipse([bx - 4, by - 4, bx + 4, by + 4], fill=(255, 180, 40))
    base = y + h
    for i, (bw, bh) in enumerate(((16, 14), (12, 22), (18, 10), (12, 18), (16, 12))):
        bx0 = x + 8 + i * 30
        d.rectangle([bx0, base - bh, bx0 + bw, base], fill=(8, 8, 16))
    _corner_label(d, x, y, "KYIV")


def art_merkury(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(120, 170, 210))
    d.line([(x + 8, y + h - 8), (x + w - 8, y + h - 8)], fill=WHITE, width=1)
    d.polygon([(x + 14, y + h - 8), (x + w - 14, y + h - 8),
               (x + w - 26, y + h - 20), (x + 26, y + h - 20)], fill=(80, 80, 80))
    d.rectangle([x + w // 2 - 2, y + h - 34, x + w // 2 + 2, y + h - 20], fill=(60, 60, 60))
    _corner_label(d, x, y, "MERKURY")


def art_usa(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(200, 225, 245))
    cx = x + w // 2
    d.pieslice([cx - 18, y + 6, cx + 18, y + 30], start=180, end=360, fill=WHITE)
    d.rectangle([cx - 22, y + 16, cx + 22, y + h - 4], fill=WHITE)
    for lx in (-14, -5, 4, 13):
        d.line([(cx + lx, y + 18), (cx + lx, y + h - 6)], fill=(180, 200, 220), width=1)
    _corner_label(d, x, y, "USA", fill=INK)


def art_markets(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=DARKPANEL)
    d.text((x + w - 40, y + 3), "-10%", font=sans(11, bold=True), fill=(230, 60, 60))
    pts = [(x + 8, y + 16), (x + int(w * 0.3), y + 18), (x + int(w * 0.5), y + 24),
           (x + int(w * 0.7), y + 30), (x + w - 8, y + h - 6)]
    d.line(pts, fill=(230, 60, 60), width=2)
    _corner_label(d, x, y, "NASDAQ")


def art_tech(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(20, 60, 40))
    d.rectangle([x + int(w * 0.28), y + 8, x + int(w * 0.72), y + h - 8],
                fill=(40, 110, 70), outline=(140, 200, 160))
    draw_centered(d, x + w // 2, y + h // 2 - 7, "NVDA", sans(12, bold=True), WHITE)
    _corner_label(d, x, y, "NVDA")


def art_indonesia(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(200, 70, 40))
    d.rectangle([x + 10, y + h - 14, x + w - 10, y + h - 4], fill=(60, 20, 15))
    d.rectangle([x + 16, y + h - 26, x + 24, y + h - 14], fill=(60, 20, 15))
    d.rectangle([x + w - 26, y + h - 30, x + w - 18, y + h - 14], fill=(60, 20, 15))
    for fx in (0.35, 0.55, 0.75):
        px = x + int(w * fx)
        d.polygon([(px - 6, y + h - 14), (px + 6, y + h - 14), (px, y + h - 26)],
                  fill=(255, 180, 40))
    _corner_label(d, x, y, "INDONESIA")


def art_gaza(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(150, 150, 150))
    d.text((x + w - 42, y + 3), "99%", font=sans(15, bold=True), fill=WHITE)
    d.line([(x + 6, y + 22), (x + int(w * 0.4), y + 18), (x + int(w * 0.65), y + 24),
            (x + w - 6, y + 20)], fill=(200, 40, 40), width=2)
    for i, bw in enumerate((26, 18, 30, 14)):
        bx0 = x + 6 + i * 36
        d.rectangle([bx0, y + h - 10, bx0 + bw, y + h - 4], fill=(70, 70, 70))
    _corner_label(d, x, y, "GAZA")


def art_mexico(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(190, 220, 240))
    cx, cy = x + w // 2, y + h // 2 - 2
    d.ellipse([cx - 9, cy - 12, cx + 9, cy + 6], fill=(255, 200, 0))
    d.polygon([(cx - 6, cy + 2), (cx + 6, cy + 2), (cx, cy + 14)], fill=(255, 200, 0))
    d.text((cx - 4, cy - 10), "$", font=sans(11, bold=True), fill=INK)
    _corner_label(d, x, y, "MEXICO", fill=INK)


def art_kerch(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(140, 190, 220))
    mid = y + h // 2
    d.line([(x + 4, mid), (x + w - 4, mid)], fill=(40, 40, 40), width=2)
    for px in (0.25, 0.5, 0.75):
        px0 = x + int(w * px)
        d.line([(px0, mid), (px0, mid + 10)], fill=(40, 40, 40), width=2)
    d.polygon([(x + int(w * 0.55), mid - 6), (x + int(w * 0.55) + 6, mid),
               (x + int(w * 0.55), mid + 6), (x + int(w * 0.55) - 6, mid)],
              fill=(255, 140, 0))
    _corner_label(d, x, y, "KERCH")


def art_westbank(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(230, 215, 170))
    d.pieslice([x - 10, y + h - 22, x + int(w * 0.6), y + h + 6], start=180, end=360,
               fill=(200, 180, 130))
    d.pieslice([x + int(w * 0.4), y + h - 18, x + w + 10, y + h + 8], start=180, end=360,
               fill=(185, 165, 115))
    d.rectangle([x + int(w * 0.62), y + h - 26, x + int(w * 0.62) + 16, y + h - 12],
                fill=(90, 70, 50))
    _corner_label(d, x, y, "WEST BANK", fill=INK)


def art_saudi(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(225, 225, 215))
    d.rectangle([x + 14, y + 10, x + 22, y + h - 6], fill=(120, 120, 115))
    d.rectangle([x + 30, y + 16, x + 36, y + h - 6], fill=(120, 120, 115))
    d.rectangle([x + 44, y + 6, x + 52, y + h - 6], fill=(120, 120, 115))
    d.line([(x + 10, y + 12), (x + w - 10, y + 12)], fill=(100, 100, 95), width=2)
    d.ellipse([x + w - 26, y + 4, x + w - 14, y + 16], fill=(160, 160, 155))
    d.ellipse([x + w - 34, y + 10, x + w - 24, y + 20], fill=(170, 170, 165))
    _corner_label(d, x, y, "RABIGH", fill=INK)


ART = {
    "hormuz": art_hormuz, "cop": art_cop, "nato": art_nato,
    "kyiv": art_kyiv, "merkury": art_merkury, "usa": art_usa,
    "markets": art_markets, "tech": art_tech, "indonesia": art_indonesia,
    "gaza": art_gaza, "mexico": art_mexico, "kerch": art_kerch,
    "westbank": art_westbank, "saudi": art_saudi,
}

def lead_card(d, x, y, w, h, item):
    d.rectangle([x, y, x + w, y + h], outline=INK, width=1)
    ART[item["art"]](d, x + 1, y + 1, w - 2, 56)
    ky = y + 62
    d.text((x + 6, ky), item["kicker"], font=sans(11, bold=True), fill=CRIMSON)
    label, color = item["chip"]
    cw = chip_width(label)
    draw_chip(d, x + w - 6 - cw, ky - 1, label, color)
    headline = wrap_text(serif(20, bold=True), item["headline"], w - 12)[:2]
    draw_lines(d, x + 6, y + 80, headline, serif(20, bold=True), INK, 22)
    deck = wrap_text(sans(12), item["deck"], w - 12)[:2]
    draw_lines(d, x + 6, y + 126, deck, sans(12), INK, 15)
    d.text((x + 6, y + 158), "Source: " + item["source"], font=sans(10), fill=GREY)


def secondary_card(d, x, y, w, h, item):
    d.rectangle([x, y, x + w, y + h], outline=INK, width=1)
    ART[item["art"]](d, x + 1, y + 1, w - 2, 40)
    ky = y + 45
    d.text((x + 5, ky), item["kicker"], font=sans(10, bold=True), fill=CRIMSON)
    label, color = item["chip"]
    cw = chip_width(label, size=9)
    draw_chip(d, x + w - 5 - cw, ky - 1, label, color, size=9, height=13)
    headline = wrap_text(serif(13, bold=True), item["headline"], w - 10)[:2]
    draw_lines(d, x + 5, y + 60, headline, serif(13, bold=True), INK, 15)
    deck = wrap_text(sans(10), item["deck"], w - 10)[:2]
    draw_lines(d, x + 5, y + 90, deck, sans(10), INK, 12)


def draw_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SKY, outline=INK, width=1)
    for poly in CONTINENTS:
        pts = [(x + px, y + py) for px, py in poly]
        d.polygon(pts, fill=LAND, outline=(190, 175, 130))
    for text, lx, ly in MAP_LABELS:
        d.text((x + lx, y + ly), text, font=sans(9, bold=True), fill=(120, 120, 115))
    fnum = sans(10, bold=True)
    for num, px, py in PINS:
        cx, cy = x + px, y + py
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=CRIMSON, outline=WHITE, width=1)
        s = str(num)
        tw = fnum.getlength(s)
        d.text((cx - tw / 2, cy - 7), s, font=fnum, fill=WHITE)


def draw_briefs(d, x, y, w, columns):
    col_w = (w - 2 * 8) // 3
    fnum = sans(9, bold=True)
    ftext = sans(9)
    bottom = y
    for ci, items in enumerate(columns):
        cx = x + ci * (col_w + 8)
        cy = y
        for num, text in items:
            tag = str(num) + "."
            d.text((cx, cy), tag, font=fnum, fill=CRIMSON)
            tag_w = fnum.getlength(tag) + 4
            lines = wrap_text(ftext, text, col_w - tag_w)
            draw_lines(d, cx + tag_w, cy, lines, ftext, INK, 11)
            cy += max(len(lines), 1) * 11 + 4
        bottom = max(bottom, cy)
    return bottom


def build_page():
    img = Image.new("RGB", (PAGE_W, PAGE_H), IVORY)
    d = ImageDraw.Draw(img)

    # Masthead and date.
    draw_centered(d, PAGE_W // 2, 6, "THE WORLD TODAY", serif(58, bold=True), INK)
    draw_centered(d, PAGE_W // 2, 66, "MONDAY, 23 NOVEMBER 2026", serif(22, bold=True), CRIMSON)
    draw_rule(d, 94)

    # Three-line red headline band.
    hy = 100
    for line in ("IRAN WAR WIDENS — BAHRAIN HIT, TANKERS MINED IN HORMUZ",
                 "COP31 COLLAPSE: THE BLAME GAME — 'WORST EVER' SUMMIT",
                 "NATO IN EMERGENCY SESSION — RUSSIAN MISSILES FELL IN POLAND"):
        draw_centered(d, PAGE_W // 2, hy, line, sans(19, bold=True), CRIMSON)
        hy += 21
    draw_rule(d, 168)

    # The day in UTC.
    uy = 174
    d.rectangle([MARGIN, uy, MARGIN + 110, uy + 44], fill=CRIMSON)
    d.text((MARGIN + 8, uy + 5), "THE DAY", font=sans(13, bold=True), fill=WHITE)
    d.text((MARGIN + 8, uy + 21), "IN UTC", font=sans(13, bold=True), fill=WHITE)
    cell_x = MARGIN + 116
    cell_w = (PAGE_W - MARGIN - cell_x) // 7
    for i, (t, cap) in enumerate(UTC_MARKS):
        cx = cell_x + i * cell_w
        if i:
            d.line([(cx, uy + 4), (cx, uy + 40)], fill=FAINT, width=1)
        d.text((cx + 6, uy + 4), t, font=sans(12, bold=True), fill=CRIMSON)
        cap_lines = wrap_text(sans(10), cap, cell_w - 12)[:2]
        draw_lines(d, cx + 6, uy + 20, cap_lines, sans(10), INK, 12)

    # The day in numbers.
    ny = 222
    d.rectangle([MARGIN, ny, PAGE_W - MARGIN, ny + 38], fill=INK)
    num_w = CONTENT_W // 6
    for i, (num, cap) in enumerate(NUMBERS):
        cx = MARGIN + i * num_w + num_w // 2
        draw_centered(d, cx, ny + 4, num, sans(22, bold=True), WHITE)
        draw_centered(d, cx, ny + 28, cap, sans(10), WHITE)

    # Coverage line.
    draw_centered(d, PAGE_W // 2, 266,
                  "37 STORIES · 5 REGIONS · 9 FIELDS — MONDAY 23 NOVEMBER 2026",
                  sans(14, bold=True), INK)

    # Three leads.
    lx = MARGIN
    for i, item in enumerate(LEADS):
        w = (CONTENT_W - 16) // 3 + (1 if i else 0)
        lead_card(d, lx, 286, w, 170, item)
        lx += w + 8

    # Eleven secondaries in two rows.
    sx = MARGIN
    for item in SECONDARIES_TOP:
        secondary_card(d, sx, 464, 161, 116, item)
        sx += 167
    sx = MARGIN
    for i, item in enumerate(SECONDARIES_BOTTOM):
        w = 194 if i < 3 else 195
        secondary_card(d, sx, 588, w, 116, item)
        sx += w + 6

    # Map and briefs.
    d.text((MARGIN, 712), "WHERE IT HAPPENED", font=sans(15, bold=True), fill=INK)
    d.text((440, 712), "ALSO ON MONDAY 23 NOVEMBER", font=sans(15, bold=True), fill=INK)
    draw_map(d, MARGIN, 732, 416, 150)
    d.text((MARGIN, 888), REGION_LINE, font=sans(11, bold=True), fill=INK)
    d.text((MARGIN, 904), "Numbers match the stories. Schematic map, not to scale.",
           font=sans(9), fill=GREY)
    draw_briefs(d, 440, 732, 570, [BRIEFS[0:8], BRIEFS[8:16], BRIEFS[16:23]])

    # Date-check box.
    d.rectangle([MARGIN, 978, PAGE_W - MARGIN, 1004], outline=CRIMSON, width=2)
    draw_centered(d, PAGE_W // 2, 983,
                  "DATE CHECK — NOT 23 NOV, SO NOT IN THIS PAPER:  COP31 collapse itself (22 Nov) · "
                  "Merkury sinking (22 Nov) · ICJ Myanmar ruling (20 Nov)",
                  sans(11, bold=True), CRIMSON)

    # Footer.
    d.text((MARGIN, 1008), "All stories first reported Mon 23 Nov 2026.",
           font=sans(10), fill=GREY)
    legend = [("CONFIRMED", GREEN), ("REPORTED", OCHRE), ("CLAIMED", CRIMSON)]
    total = sum(chip_width(label, size=9) for label, _ in legend) + 2 * 8
    fx = PAGE_W // 2 - total // 2
    for label, color in legend:
        cw = chip_width(label, size=9)
        draw_chip(d, fx, 1007, label, color, size=9, height=13)
        fx += cw + 8
    sources = "Sources: AP, Reuters, AFP, CNN, Zacks, TradingView."
    d.text((PAGE_W - MARGIN - sans(10).getlength(sources), 1008), sources,
           font=sans(10), fill=GREY)

    return img


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    here = Path(__file__).resolve().parent
    img = build_page()
    local_target = here / "entry.png"
    img.save(local_target, format="PNG")
    data = local_target.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        print("error: entry.png is not a PNG file", file=sys.stderr)
        return 1
    digest = hashlib.sha256(data).hexdigest()

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    if out_dir.resolve() != here.resolve():
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / "entry.png"
        target.write_bytes(data)
        if sha256_of(target) != digest:
            print("error: copy of entry.png does not match the source", file=sys.stderr)
            return 1
        print(f"wrote {target} ({len(data)} bytes, sha256 {digest})")
    print(f"wrote {local_target} ({len(data)} bytes, sha256 {digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
