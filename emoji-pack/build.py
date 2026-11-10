#!/usr/bin/env python3
"""Генератор пака Discord-эмодзи: силуэты game-icons.net (CC BY 3.0) в стиле Persona / ZZZ.

  python3 build.py            — собрать пак
  python3 build.py cand a b…  — лист-примерка для произвольных иконок из ICONS_DIR
"""
import io
import math
import random
import re
import shutil
import sys
import zipfile
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw

ROOT = Path(__file__).parent
ICONS_DIR = Path("/tmp/gi")  # клон https://github.com/game-icons/icons
SRC = ROOT / "src"  # использованные исходники, чтобы пак собирался без клона
RED, BLACK, WHITE = "#E60012", "#0B0B0D", "#F7F7F7"
PREFIX = "kz_"

# имя эмодзи -> (иконка game-icons, y начала красного среза слева, справа; None — без среза)
ICONS = {
    "license": ("delapouite/id-card", 400, 300),
    "status": ("skoll/rank-3", 400, 300),
    "arsenal": ("lorc/crossed-swords", 400, 300),
    "ticket": ("delapouite/ticket", 400, 300),
    "strength": ("delapouite/biceps", 400, 300),
    "agility": ("lorc/sprint", 400, 300),
    "endurance": ("lorc/checked-shield", 400, 300),
    "durability": ("delapouite/chest-armor", 400, 300),
    "reaction": ("lorc/power-lightning", 400, 300),
    "magic": ("lorc/magic-swirl", 400, 300),
    "fruit": ("lorc/shiny-apple", 400, 300),
    "elements": ("lorc/triple-yin", 400, 300),
    "flesh": ("lorc/meat", 400, 300),
    "flame": ("carl-olsen/flame", 400, 300),
    "haki": ("lorc/aura", 400, 300),
    "armament": ("lorc/mailed-fist", 400, 300),
    "observation": ("delapouite/eye-target", 400, 300),
    "conqueror": ("lorc/queen-crown", 400, 300),
    "extra": ("lorc/jigsaw-piece", 400, 300),
    "patron": ("lorc/angel-outfit", 400, 300),
    "none": ("sbed/cancel", 400, 300),
    "banner": ("delapouite/knight-banner", 400, 300),
}


def pts(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def load_paths(icon):
    """Пути силуэта без чёрной подложки 512x512."""
    f = SRC / (icon.replace("/", "__") + ".svg")
    if not f.exists():
        f = ICONS_DIR / f"{icon}.svg"
    ds = re.findall(r'\sd="([^"]+)"', f.read_text(encoding="utf-8"))
    return [d for d in ds if not re.fullmatch(r"M0 0h512v512H0z", d.strip())]


def styled(paths, cut=(400, 300)):
    """Белый силуэт с чёрной обводкой, красной жёсткой тенью и диагональным красным срезом."""
    g = "".join(f'<path d="{d}"/>' for d in paths)
    band = ""
    if cut:
        band = (f'<g clip-path="url(#g)"><polygon points="-60,{cut[0]} 572,{cut[1]} 572,572 -60,572" fill="{RED}"/>'
                f'<polygon points="-60,{cut[0] - 14} 572,{cut[1] - 14} 572,{cut[1]} -60,{cut[0]}" fill="{BLACK}"/></g>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<defs><clipPath id="g">{g}</clipPath></defs>
<g transform="translate(246,246) rotate(-6) scale(0.8) translate(-256,-256)" stroke-linejoin="round">
<g transform="translate(34,34)"><g fill="{BLACK}" stroke="{BLACK}" stroke-width="40">{g}</g><g fill="{RED}" stroke="{RED}" stroke-width="10">{g}</g></g>
<g fill="{BLACK}" stroke="{BLACK}" stroke-width="40">{g}</g>
<g fill="{WHITE}">{g}</g>{band}
</g></svg>"""


# ---------- маркеры и разделитель (чистая геометрия) ----------
def diamond(cx, cy, r, fill, **kw):
    extra = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'<polygon points="{cx},{cy - r} {cx + r},{cy} {cx},{cy + r} {cx - r},{cy}" fill="{fill}" {extra}/>'


def hexagon(r, **kw):
    p = [(r * math.cos(math.pi / 3 * i - math.pi / 2), r * math.sin(math.pi / 3 * i - math.pi / 2)) for i in range(6)]
    extra = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'<polygon points="{pts(p)}" {extra}/>'


OUT = dict(stroke=BLACK, stroke_width=5, stroke_linejoin="miter")
BARE = {
    "diamond": diamond(7, 7, 46, RED, stroke=BLACK, stroke_width=4) + diamond(-3, -3, 46, WHITE, **OUT)
    + diamond(-3, -3, 30, BLACK) + diamond(-3, -3, 15, RED),
    "hex": f'<g transform="translate(6,6)">{hexagon(46, fill=RED, stroke=BLACK, stroke_width=4)}</g>'
    + f'<g transform="translate(-3,-3)">{hexagon(46, fill=WHITE, **OUT)}{hexagon(30, fill=BLACK)}{hexagon(13, fill=RED)}</g>',
    "power": diamond(0, 32, 25, WHITE, **OUT) + diamond(-32, 0, 25, WHITE, **OUT) + diamond(32, 0, 25, WHITE, **OUT)
    + diamond(0, -32, 25, RED, **OUT) + diamond(0, 0, 9, RED),
    "branch": f"""<path d="M-28,-52 V24 H34" fill="none" stroke="{BLACK}" stroke-width="28" stroke-linejoin="miter"/>
<path d="M-28,-50 V24 H30" fill="none" stroke="{WHITE}" stroke-width="18" stroke-linejoin="miter"/>"""
    + diamond(38, 24, 20, RED, **OUT),
    "sub": f"""<path d="M-28,-52 Q-28,24 30,24" fill="none" stroke="{BLACK}" stroke-width="28" stroke-linecap="butt"/>
<path d="M-28,-50 Q-28,24 28,24" fill="none" stroke="{WHITE}" stroke-width="18"/>
<polygon points="22,0 56,24 22,48" fill="{RED}" stroke="{BLACK}" stroke-width="5"/>""",
    "sep": diamond(0, -40, 19, WHITE, **OUT) + diamond(0, 0, 19, RED, **OUT) + diamond(0, 40, 19, WHITE, **OUT),
}


def bare(glyph):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><g transform="translate(64,64)">{glyph}</g></svg>'


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
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">'
            f'<polygon points="{pts([(x, y + 6) for x, y in poly])}" fill="{BLACK}"/>'
            f'<polygon points="{pts(poly)}" fill="{RED}"/>'
            f'<polygon points="36,60 100,58 96,64 32,66" fill="{WHITE}" opacity="0.9"/></svg>')


ORDER = ["license", "status", "arsenal", "diamond", "hex", "power", "sep", "branch", "sub", "ticket",
         "strength", "agility", "endurance", "durability", "reaction", "magic",
         "fruit", "elements", "flesh", "flame", "haki", "armament", "observation", "conqueror",
         "extra", "patron", "none", "banner", "div_l", "div_m", "div_r"]


def rasterize(src):
    # рендер 4x и уменьшение — края чище, чем прямой рендер в 128
    big = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=src.encode(), output_width=512, output_height=512)))
    return big.convert("RGBA").resize((128, 128), Image.LANCZOS)


def sheet(images, path, cols=8):
    """Контактный лист: крупно + реальный размер в Discord (22px и 48px) на тёмном и светлом фоне."""
    cell = 150
    rows = math.ceil(len(images) / cols)
    grid_h = rows * cell
    out = Image.new("RGBA", (cols * cell, grid_h + 190), "#313338")
    d = ImageDraw.Draw(out)
    for i, (name, img) in enumerate(images.items()):
        x, y = (i % cols) * cell, (i // cols) * cell
        out.alpha_composite(img, (x + 11, y + 4))
        d.text((x + 6, y + 134), name[-24:], fill="#B5BAC1")
    for row, (bg, size) in enumerate([("#1E1F22", 22), ("#313338", 22), ("#FFFFFF", 22), ("#313338", 48)]):
        y = grid_h + 6 + row * 34 + (0 if size == 22 else 6)
        d.rectangle([0, y - 4, out.width, y + size + 4], fill=bg)
        for i, img in enumerate(images.values()):
            x = 8 + i * (size + (8 if size == 22 else 0))
            if x + size <= out.width:
                out.alpha_composite(img.resize((size, size), Image.LANCZOS), (x, y))
    out.convert("RGB").save(path)


def build():
    for folder in ("svg", "png"):
        shutil.rmtree(ROOT / folder, ignore_errors=True)
        (ROOT / folder).mkdir()
    SRC.mkdir(exist_ok=True)
    images = {}
    for name in ORDER:
        if name in ICONS:
            icon, a, b = ICONS[name]
            cached = SRC / (icon.replace("/", "__") + ".svg")
            if not cached.exists():
                shutil.copy(ICONS_DIR / f"{icon}.svg", cached)
            src = styled(load_paths(icon), (a, b) if a else None)
        elif name in BARE:
            src = bare(BARE[name])
        else:
            src = divider(name)
        (ROOT / "svg" / f"{PREFIX}{name}.svg").write_text(src, encoding="utf-8")
        images[name] = rasterize(src)
        images[name].save(ROOT / "png" / f"{PREFIX}{name}.png", optimize=True)
    sheet(images, ROOT / "preview.png")
    with zipfile.ZipFile(ROOT / "kz_emoji_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for folder in ("png", "svg"):
            for f in sorted((ROOT / folder).iterdir()):
                z.write(f, f"{folder}/{f.name}")
        for f in ("TEMPLATE.md", "CREDITS.md"):
            z.write(ROOT / f, f)
    print(f"{len(images)} emoji, max png = {max(f.stat().st_size for f in (ROOT / 'png').iterdir())} bytes")


def candidates(icons):
    images = {}
    for icon in icons:
        try:
            images[icon] = rasterize(styled(load_paths(icon)))
        except Exception as e:  # примерка: отсутствующие иконки просто пропускаем
            print("skip", icon, type(e).__name__)
    sheet(images, "/tmp/cand.png", cols=10)


if __name__ == "__main__":
    candidates(sys.argv[2:]) if sys.argv[1:2] == ["cand"] else build()
