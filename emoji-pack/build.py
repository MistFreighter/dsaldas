#!/usr/bin/env python3
"""Генератор пака Discord-эмодзи (стиль Persona / ZZZ): SVG -> PNG 128x128."""
import io
import math
import random
import zipfile
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw

ROOT = Path(__file__).parent
RED, BLACK, WHITE = "#E60012", "#0B0B0D", "#F7F7F7"
DARK_RED, DARK_GREY = "#9C000C", "#2B2B30"


def pts(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def star4(cx, cy, r, fill, inner=0.3):
    p = []
    for i in range(8):
        rr = r if i % 2 == 0 else r * inner
        a = math.pi / 4 * i - math.pi / 2
        p.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return f'<polygon points="{pts(p)}" fill="{fill}"/>'


def badge(name, glyph, variant):
    """Наклонная «вырезанная» плашка с белой обводкой и смещённой тенью."""
    rnd = random.Random(name)
    j = lambda v: v + rnd.uniform(-3, 3)
    quad = [(j(12), j(20)), (j(100), j(9)), (j(110), j(98)), (j(22), j(110))]
    shadow = [(x + 8, y + 8) for x, y in quad]
    main, shade, dots = (RED, BLACK, DARK_RED) if variant == "red" else (BLACK, RED, DARK_GREY)
    halftone = "".join(
        f'<circle cx="{x}" cy="{y}" r="{max(0.6, (x + y - 130) / 16):.1f}" fill="{dots}"/>'
        for x in range(56, 120, 9) for y in range(56, 120, 9) if x + y > 138
    )
    return f"""
<defs><clipPath id="c"><polygon points="{pts(quad)}"/></clipPath></defs>
<polygon points="{pts(shadow)}" fill="{shade}" stroke="{WHITE}" stroke-width="5" stroke-linejoin="miter"/>
<polygon points="{pts(quad)}" fill="{main}" stroke="{WHITE}" stroke-width="5" stroke-linejoin="miter"/>
<g clip-path="url(#c)">{halftone}</g>
<g transform="translate(61,59) rotate(-6) scale(0.98)">{glyph}</g>"""


def bare(glyph):
    return f'<g transform="translate(64,64)">{glyph}</g>'


def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">{body}</svg>'


# ---------- глифы (координаты от центра, примерно -36..36) ----------
def sword(fill_tip=None, stroke=BLACK, guard=RED):
    tip = f'<polygon points="0,-40 6,-31 6,-10 -6,-10 -6,-31" fill="{fill_tip}" stroke="{WHITE}" stroke-width="3"/>' if fill_tip else ""
    return f"""<g stroke="{stroke}" stroke-width="2.5" stroke-linejoin="round">
<polygon points="0,-40 6,-31 6,13 -6,13 -6,-31" fill="{WHITE}"/>
<rect x="-4" y="19" width="8" height="15" fill="{WHITE}"/>
<rect x="-16" y="12" width="32" height="8" rx="2" fill="{guard}"/>
<circle cx="0" cy="36" r="5.5" fill="{guard}"/></g>{tip}"""


def chevron(dx, fill):
    p = [(-30, -27), (-13, -27), (8, 0), (-13, 27), (-30, 27), (-9, 0)]
    return f'<polygon points="{pts([(x + dx, y) for x, y in p])}" fill="{fill}"/>'


def burst(n=10, r1=37, r2=17):
    rnd = random.Random(7)
    p = []
    for i in range(n * 2):
        r = (r1 - rnd.uniform(0, 9)) if i % 2 == 0 else (r2 + rnd.uniform(0, 4))
        a = math.pi / n * i - math.pi / 2
        p.append((r * math.cos(a), r * math.sin(a)))
    return pts(p)


WING = "M5,4 C2,-18 -12,-31 -35,-30 C-38,-22 -34,-15 -29,-13 C-33,-8 -30,-1 -24,0 C-26,6 -21,11 -15,10 C-14,16 -6,18 0,13Z"
EYE = "M-42,0 C-22,-36 22,-36 42,0 C22,36 -22,36 -42,0Z"
BOLT = [(10, -42), (-20, 6), (-2, 6), (-10, 42), (22, -10), (4, -10), (20, -42)]


def tomoe(a0, fill):
    """Одна «запятая» томоэ: голова-круг и сужающийся хвост по дуге."""
    a0 = math.radians(a0)
    n, span = 24, math.radians(115)
    outer = [(29 * math.cos(a0 + span * i / n), 29 * math.sin(a0 + span * i / n)) for i in range(n + 1)]
    inner = []
    for i in range(n, -1, -1):
        t = i / n
        r = 29 - 24 * (1 - t) ** 1.5
        inner.append((r * math.cos(a0 + span * t), r * math.sin(a0 + span * t)))
    return (f'<circle cx="{17 * math.cos(a0):.1f}" cy="{17 * math.sin(a0):.1f}" r="12" fill="{fill}"/>'
            f'<polygon points="{pts(outer + inner)}" fill="{fill}"/>')


def spiral(cx, cy, r, turns=1.6):
    p = [(cx + r * t / 30 * math.cos(turns * 2 * math.pi * t / 30), cy + r * t / 30 * math.sin(turns * 2 * math.pi * t / 30))
         for t in range(31)]
    return f'<polyline points="{pts(p)}" fill="none" stroke="{WHITE}" stroke-width="3.5" stroke-linecap="round"/>'


def finger(x, top):
    return f'<polygon points="{x},{top + 5} {x + 4},{top} {x + 10},{top} {x + 13},{top + 4} {x + 13},8 {x},8" fill="{WHITE}" stroke="{BLACK}" stroke-width="2.5" stroke-linejoin="round"/>'

G = {
    # заголовки (красная плашка, акцент — чёрный)
    "license": f"""<rect x="-35" y="-25" width="70" height="50" rx="6" fill="{WHITE}"/>
<rect x="-28" y="-17" width="24" height="27" rx="2" fill="{BLACK}"/>
<circle cx="-16" cy="-8" r="6" fill="{WHITE}"/><path d="M-26,10 Q-16,-6 -6,10Z" fill="{WHITE}"/>
<rect x="2" y="-16" width="26" height="6" fill="{BLACK}"/><rect x="2" y="-5" width="20" height="6" fill="{BLACK}"/>
<rect x="2" y="6" width="26" height="4" fill="{RED}"/><rect x="-28" y="15" width="56" height="4" fill="{RED}"/>""",
    "status": f"""<rect x="-26" y="-29" width="52" height="64" rx="6" fill="{WHITE}"/>
<rect x="-12" y="-37" width="24" height="15" rx="4" fill="{BLACK}" stroke="{WHITE}" stroke-width="3"/>
<rect x="-18" y="10" width="9" height="16" fill="{BLACK}"/><rect x="-5" y="-1" width="9" height="27" fill="{BLACK}"/>
<rect x="8" y="-13" width="9" height="39" fill="{RED}"/>""",
    "arsenal": f"""<g transform="rotate(-42) scale(1.45,1.05)">{sword(guard=BLACK)}</g><g transform="rotate(42) scale(1.45,1.05)">{sword(guard=BLACK)}</g>""",
    # параметры (чёрная плашка, акцент — красный)
    "strength": f"""<polygon points="{burst(12, 46, 27)}" fill="{RED}"/>
<g transform="rotate(-8) translate(0,2)"><polygon points="-27,4 28,4 23,29 -19,29" fill="{WHITE}" stroke="{BLACK}" stroke-width="2.5" stroke-linejoin="round"/>
{finger(-27, -19)}{finger(-13, -25)}{finger(1, -26)}{finger(15, -20)}
<polygon points="-31,7 6,5 14,13 7,22 -25,21" fill="{WHITE}" stroke="{BLACK}" stroke-width="3" stroke-linejoin="round"/></g>""",
    "agility": f"""<rect x="-38" y="-18" width="14" height="6" fill="{RED}"/><rect x="-40" y="-3" width="18" height="6" fill="{WHITE}"/><rect x="-38" y="12" width="14" height="6" fill="{RED}"/>
{chevron(6, WHITE)}{chevron(30, RED)}""",
    "endurance": f"""<path d="M0,-37 L30,-26 L30,2 C30,20 15,31 0,38 C-15,31 -30,20 -30,2 L-30,-26Z" fill="{WHITE}"/>
<path d="M0,-27 L-21,-19 L-21,2 C-21,14 -11,22 0,27Z" fill="{BLACK}"/>
<path d="M0,-27 L21,-19 L21,2 C21,14 11,22 0,27Z" fill="{RED}"/>
<rect x="-3" y="-27" width="6" height="54" fill="{WHITE}"/><rect x="-21" y="-7" width="42" height="6" fill="{WHITE}"/>""",
    "durability": f"""<path d="M0,35 C-46,4 -39,-33 -17,-33 C-7,-33 0,-26 0,-19 C0,-26 7,-33 17,-33 C39,-33 46,4 0,35Z" fill="{RED}" stroke="{WHITE}" stroke-width="5" stroke-linejoin="round"/>
<rect x="-6" y="-19" width="12" height="34" fill="{WHITE}"/><rect x="-17" y="-8" width="34" height="12" fill="{WHITE}"/>""",
    "reaction": f"""<polygon points="{pts([(x + 6, y + 5) for x, y in BOLT])}" fill="{RED}"/><polygon points="{pts(BOLT)}" fill="{WHITE}"/>
<polygon points="-38,-24 -24,-30 -29,-15" fill="{RED}"/><polygon points="-36,22 -24,14 -25,28" fill="{WHITE}"/>
<polygon points="27,18 40,22 30,31" fill="{WHITE}"/><polygon points="30,-30 40,-36 38,-22" fill="{RED}"/>""",
    "magic": f"""<rect x="-21" y="-33" width="42" height="66" rx="5" fill="{WHITE}" stroke="{BLACK}" stroke-width="3" transform="rotate(-16) translate(-8,2)"/>
<g transform="rotate(10) translate(5,0)"><rect x="-21" y="-33" width="42" height="66" rx="5" fill="{WHITE}" stroke="{BLACK}" stroke-width="3"/>
<rect x="-15" y="-27" width="30" height="54" rx="2" fill="{RED}"/>{star4(0, 0, 17, WHITE)}<circle cx="0" cy="-20" r="2.5" fill="{WHITE}"/><circle cx="0" cy="20" r="2.5" fill="{WHITE}"/></g>""",
    "ticket": f"""<g transform="rotate(-12)"><path d="M-36,-21 H36 V-8 A8,8 0 0 0 36,8 V21 H-36 V8 A8,8 0 0 0 -36,-8Z" fill="{WHITE}"/>
<path d="M12,-21 H36 V-8 A8,8 0 0 0 36,8 V21 H12Z" fill="{RED}"/>
<line x1="12" y1="-19" x2="12" y2="19" stroke="{BLACK}" stroke-width="3" stroke-dasharray="5 4"/>{star4(-12, 0, 14, BLACK, 0.38)}</g>""",
    # арсенал
    "fruit": f"""<path d="M0,-16 Q1,-32 16,-37" fill="none" stroke="{WHITE}" stroke-width="7" stroke-linecap="round"/>
<path d="M4,-25 Q-12,-38 -22,-26 Q-10,-18 4,-25Z" fill="{WHITE}"/>
<circle cx="0" cy="8" r="27" fill="{RED}" stroke="{WHITE}" stroke-width="5"/>
{spiral(-10, 1, 10)}{spiral(11, 8, 9)}{spiral(-3, 22, 8)}""",
    "elements": f"""<g transform="scale(1.3)">{tomoe(-90, WHITE)}{tomoe(30, RED)}{tomoe(150, WHITE)}</g>""",
    "flesh": f"""<path d="M-4,-38 C10,-16 24,-4 24,11 A28,26 0 0 1 -32,11 C-32,-4 -18,-16 -4,-38Z" fill="{RED}" stroke="{WHITE}" stroke-width="5" stroke-linejoin="round"/>
<path d="M-20,10 A16,15 0 0 0 -6,25" fill="none" stroke="{WHITE}" stroke-width="5" stroke-linecap="round"/>
<path d="M27,-34 C32,-26 37,-22 37,-16 A10,10 0 0 1 17,-16 C17,-22 22,-26 27,-34Z" fill="{WHITE}"/>""",
    "flame": f"""<path d="M2,-40 C8,-22 30,-12 26,12 C24,29 11,37 0,37 C-11,37 -24,29 -26,12 C-28,-2 -18,-8 -14,-20 C-10,-12 -8,-10 -5,-10 C-9,-22 -4,-32 2,-40Z" fill="{WHITE}"/>
<path d="M1,-8 C5,2 14,6 13,17 C12,28 5,32 0,32 C-6,32 -13,28 -13,17 C-13,9 -5,4 1,-8Z" fill="{RED}"/>""",
    "haki": f"""<polygon points="{burst()}" fill="{WHITE}"/><circle r="15" fill="{BLACK}"/><circle r="10" fill="{RED}"/><circle r="4" fill="{WHITE}"/>""",
    "armament": f"""<g transform="rotate(40) scale(1.6,1.12)">{sword(fill_tip=BLACK)}</g>
<polygon points="-34,-12 -22,-18 -26,-8" fill="{RED}"/><polygon points="-30,8 -18,4 -24,14" fill="{RED}"/>""",
    "observation": f"""<polygon points="-24,-27 -18,-42 -11,-31" fill="{WHITE}"/><polygon points="-6,-34 0,-48 6,-34" fill="{WHITE}"/><polygon points="11,-31 18,-42 24,-27" fill="{WHITE}"/>
<polygon points="-24,27 -18,42 -11,31" fill="{RED}"/><polygon points="-6,34 0,48 6,34" fill="{RED}"/><polygon points="11,31 18,42 24,27" fill="{RED}"/>
<path d="{EYE}" fill="{WHITE}"/><circle r="20" fill="{BLACK}"/><circle r="15.5" fill="{RED}"/><circle r="7" fill="{BLACK}"/><circle cx="-7" cy="-8" r="4" fill="{WHITE}"/>""",
    "conqueror": f"""<polygon points="-31,18 -37,-22 -17,-4 0,-34 17,-4 37,-22 31,18" fill="{WHITE}"/>
<rect x="-31" y="22" width="62" height="10" fill="{RED}"/>
<circle cx="-37" cy="-24" r="5" fill="{RED}"/><circle cx="0" cy="-36" r="5" fill="{RED}"/><circle cx="37" cy="-24" r="5" fill="{RED}"/>
<polygon points="0,-6 8,5 0,16 -8,5" fill="{RED}"/>""",
    "extra": f"""<g transform="translate(6,6)" fill="{RED}"><rect x="-9" y="-32" width="18" height="64"/><rect x="-32" y="-9" width="64" height="18"/></g>
<rect x="-9" y="-32" width="18" height="64" fill="{WHITE}"/><rect x="-32" y="-9" width="64" height="18" fill="{WHITE}"/>
{star4(29, -29, 11, WHITE)}{star4(-29, 29, 9, RED)}""",
    "patron": f"""<ellipse cx="0" cy="-30" rx="16" ry="6" fill="none" stroke="{RED}" stroke-width="6"/>
<g transform="translate(-7,2)"><path d="{WING}" fill="{WHITE}"/></g><g transform="translate(7,2) scale(-1,1)"><path d="{WING}" fill="{WHITE}"/></g>
{star4(0, 12, 17, RED, 0.36)}""",
    "none": f"""<circle r="27" fill="none" stroke="{WHITE}" stroke-width="10"/><line x1="-27" y1="27" x2="27" y2="-27" stroke="{RED}" stroke-width="11" stroke-linecap="square"/>""",
    "banner": f"""<line x1="-24" y1="-38" x2="-24" y2="38" stroke="{WHITE}" stroke-width="7" stroke-linecap="round"/>
<polygon points="-20,-32 34,-32 34,22 7,10 -20,22" fill="{RED}" stroke="{WHITE}" stroke-width="4" stroke-linejoin="miter"/>
<rect x="3" y="-27" width="8" height="30" fill="{WHITE}"/><rect x="-7" y="-19" width="28" height="8" fill="{WHITE}"/>""",
}


def diamond(cx, cy, r, fill, **kw):
    extra = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'<polygon points="{cx},{cy - r} {cx + r},{cy} {cx},{cy + r} {cx - r},{cy}" fill="{fill}" {extra}/>'


def hexagon(r, **kw):
    p = [(r * math.cos(math.pi / 3 * i - math.pi / 2), r * math.sin(math.pi / 3 * i - math.pi / 2)) for i in range(6)]
    extra = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'<polygon points="{pts(p)}" {extra}/>'


OUT = dict(stroke=BLACK, stroke_width=5, stroke_linejoin="miter")

# маркеры без плашки — крупные, чтобы читались в строке текста
BARE = {
    "diamond": diamond(7, 7, 46, RED, stroke=WHITE, stroke_width=4) + diamond(-3, -3, 46, WHITE, **OUT)
    + diamond(-3, -3, 30, BLACK) + diamond(-3, -3, 15, RED),
    "hex": f'<g transform="translate(6,6)">{hexagon(46, fill=RED, stroke=WHITE, stroke_width=4)}</g>'
    + f'<g transform="translate(-3,-3)">{hexagon(46, fill=WHITE, **OUT)}{hexagon(30, fill=BLACK)}{hexagon(13, fill=RED)}</g>',
    "power": diamond(0, 32, 25, WHITE, **OUT) + diamond(-32, 0, 25, WHITE, **OUT) + diamond(32, 0, 25, WHITE, **OUT)
    + diamond(0, -32, 25, RED, stroke=WHITE, stroke_width=5) + diamond(0, 0, 9, RED),
    "branch": f"""<path d="M-28,-52 V24 H34" fill="none" stroke="{BLACK}" stroke-width="28" stroke-linejoin="miter"/>
<path d="M-28,-50 V24 H30" fill="none" stroke="{WHITE}" stroke-width="18" stroke-linejoin="miter"/>"""
    + diamond(38, 24, 20, RED, stroke=WHITE, stroke_width=5),
    "sub": f"""<path d="M-28,-52 Q-28,24 30,24" fill="none" stroke="{BLACK}" stroke-width="28" stroke-linecap="butt"/>
<path d="M-28,-50 Q-28,24 28,24" fill="none" stroke="{WHITE}" stroke-width="18"/>
<polygon points="22,0 56,24 22,48" fill="{RED}" stroke="{WHITE}" stroke-width="5"/>""",
    "sep": diamond(0, -40, 19, WHITE, **OUT) + diamond(0, 0, 19, RED, stroke=WHITE, stroke_width=5) + diamond(0, 40, 19, WHITE, **OUT),
}


def divider(kind):
    """Куски рваной красной полосы-разделителя: div_l + div_m × N + div_r."""
    rnd = random.Random(kind)
    xs = list(range(0, 129, 8))
    top = [(x, 46 + rnd.uniform(-9, 9)) for x in xs]
    bot = [(x, 82 + rnd.uniform(-9, 9)) for x in xs]
    # стыки между кусками фиксированы, чтобы полоса сходилась
    top[0], top[-1], bot[0], bot[-1] = (0, 46), (128, 46), (0, 82), (128, 82)
    if kind == "div_l":
        top = [(6, 64)] + [(x, y) for x, y in top if x >= 32]
        bot = [(6, 64)] + [(x, y) for x, y in bot if x >= 32]
    if kind == "div_r":
        top = [(x, y) for x, y in top if x <= 96] + [(122, 64)]
        bot = [(x, y) for x, y in bot if x <= 96] + [(122, 64)]
    poly = top + bot[::-1]
    return (f'<polygon points="{pts([(x, y + 6) for x, y in poly])}" fill="{BLACK}"/>'
            f'<polygon points="{pts(poly)}" fill="{RED}"/>'
            f'<polygon points="36,60 100,58 96,64 32,66" fill="{WHITE}" opacity="0.9"/>')


RED_BADGE = {"license", "status", "arsenal"}
ORDER = ["license", "status", "arsenal", "diamond", "hex", "power", "sep", "branch", "sub", "ticket",
         "strength", "agility", "endurance", "durability", "reaction", "magic",
         "fruit", "elements", "flesh", "flame", "haki", "armament", "observation", "conqueror",
         "extra", "patron", "none", "banner", "div_l", "div_m", "div_r"]
PREFIX = "kz_"


def build():
    (ROOT / "svg").mkdir(exist_ok=True)
    (ROOT / "png").mkdir(exist_ok=True)
    images = {}
    for name in ORDER:
        if name in G:
            body = badge(name, G[name], "red" if name in RED_BADGE else "black")
        elif name in BARE:
            body = bare(BARE[name])
        else:
            body = divider(name)
        src = svg(body)
        (ROOT / "svg" / f"{PREFIX}{name}.svg").write_text(src, encoding="utf-8")
        # рендер 4x и уменьшение — края чище, чем прямой рендер в 128
        big = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=src.encode(), output_width=512, output_height=512)))
        img = big.convert("RGBA").resize((128, 128), Image.LANCZOS)
        img.save(ROOT / "png" / f"{PREFIX}{name}.png", optimize=True)
        images[name] = img
    preview(images)
    with zipfile.ZipFile(ROOT / "kz_emoji_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for folder in ("png", "svg"):
            for f in sorted((ROOT / folder).iterdir()):
                z.write(f, f"{folder}/{f.name}")
        z.write(ROOT / "TEMPLATE.md", "TEMPLATE.md")
    print(f"{len(images)} emoji, max png = {max(f.stat().st_size for f in (ROOT / 'png').iterdir())} bytes")


def preview(images):
    """Контактный лист: крупно + реальный размер в Discord (22px и 48px) на тёмном и светлом фоне."""
    cols, cell = 8, 150
    rows = math.ceil(len(images) / cols)
    grid_h = rows * cell
    sheet = Image.new("RGBA", (cols * cell, grid_h + 190), "#1E1F22")
    d = ImageDraw.Draw(sheet)
    for i, (name, img) in enumerate(images.items()):
        x, y = (i % cols) * cell, (i // cols) * cell
        sheet.alpha_composite(img, (x + 11, y + 4))
        d.text((x + 11, y + 134), name, fill="#B5BAC1")
    for row, (bg, size) in enumerate([("#1E1F22", 22), ("#313338", 22), ("#FFFFFF", 22), ("#1E1F22", 48)]):
        y = grid_h + 6 + row * 34 + (0 if size == 22 else 6)
        d.rectangle([0, y - 4, sheet.width, y + size + 4], fill=bg)
        for i, img in enumerate(images.values()):
            sheet.alpha_composite(img.resize((size, size), Image.LANCZOS), (8 + i * (size + (8 if size == 22 else 0)), y))
    sheet.convert("RGB").save(ROOT / "preview.png")


if __name__ == "__main__":
    build()
