"""
Tipografía y paleta compartidas por todos los SVG del perfil.

GitHub muestra los SVG como imágenes y no garantiza que carguen fuentes, así que
los textos se convierten en contornos con HarfBuzz (con kerning real). Cada glifo
se define una sola vez en <defs> y se reutiliza con <use>, para que pesen poco.
"""
import os
from html import escape

import uharfbuzz as hb

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# Fraunces para lo editorial, IBM Plex Mono para los detalles técnicos
FACES = {
    "display": ("Fraunces.ttf", {"opsz": 144, "wght": 330, "SOFT": 60, "WONK": 0}),
    "heading": ("Fraunces.ttf", {"opsz": 72, "wght": 360, "SOFT": 50, "WONK": 0}),
    "text": ("Fraunces.ttf", {"opsz": 24, "wght": 380, "SOFT": 40, "WONK": 0}),
    "mono": ("IBMPlexMono-Regular.ttf", {}),
    "mono-md": ("IBMPlexMono-Medium.ttf", {}),
}

# page = el fondo de GitHub detrás de las imágenes (no se dibuja, sirve de referencia)
THEMES = {
    "light": dict(page="#FFFFFF", paper="#F5EFE6", edge="#EBE3D6", ink="#1F1B16", ink2="#4E463D",
                  muted="#71665A", rule="#E2D9CB", accent="#A84A2C", topo="#BBA990", bar="#988670",
                  btn_ink="#FBF6EF"),
    "dark": dict(page="#0D1117", paper="#191613", edge="#2C2721", ink="#EFE8DC", ink2="#C4BAAB",
                 muted="#978C7E", rule="#2F2A24", accent="#DE8A64", topo="#4F463D", bar="#7A6D5F",
                 btn_ink="#1A1612"),
}

_cache = {}


def _font(face):
    if face not in _cache:
        file, variations = FACES[face]
        with open(os.path.join(FONTS, file), "rb") as f:
            blob = hb.Blob(f.read())
        font = hb.Font(hb.Face(blob))
        if variations:
            font.set_variations(variations)
        _cache[face] = (font, font.face.upem)
    return _cache[face]


def _shape(s, face, features):
    font, _ = _font(face)
    buf = hb.Buffer()
    buf.add_str(s)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True, **(features or {})})
    return [(i.codepoint, p.x_advance, p.x_offset, p.y_offset) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


class _Pen:
    def __init__(self):
        self.d = []

    def moveTo(self, p): self.d.append(f"M{p[0]:.0f} {p[1]:.0f}")
    def lineTo(self, p): self.d.append(f"L{p[0]:.0f} {p[1]:.0f}")
    def qCurveTo(self, c, p): self.d.append(f"Q{c[0]:.0f} {c[1]:.0f} {p[0]:.0f} {p[1]:.0f}")
    def curveTo(self, c1, c2, p): self.d.append(f"C{c1[0]:.0f} {c1[1]:.0f} {c2[0]:.0f} {c2[1]:.0f} {p[0]:.0f} {p[1]:.0f}")
    def closePath(self): self.d.append("Z")


def width(s, face, size, tracking=0, features=None):
    _, upem = _font(face)
    glyphs = _shape(s, face, features)
    return sum(g[1] for g in glyphs)*size/upem + tracking*size*max(len(glyphs) - 1, 0)


def wrap(s, face, size, max_w):
    lines, cur = [], ""
    for word in s.split():
        test = f"{cur} {word}".strip()
        if cur and width(test, face, size) > max_w:
            lines.append(cur); cur = word
        else:
            cur = test
    return lines + [cur] if cur else lines


class Type:
    """Junta los glifos que usa un SVG y devuelve cada texto como contornos."""

    def __init__(self):
        self.glyphs = {}

    def text(self, s, x, y, face, size, fill, anchor="start", tracking=0, opacity=None, features=None, extra=""):
        font, upem = _font(face)
        k = size/upem
        w = width(s, face, size, tracking, features)
        x -= {"start": 0, "middle": w/2, "end": w}[anchor]
        uses, pen_x = [], 0.0
        for gid, adv, xo, yo in _shape(s, face, features):
            key = f"{face[0]}{'m' if 'md' in face else ''}{gid}"
            if key not in self.glyphs:
                pen = _Pen()
                font.draw_glyph_with_pen(gid, pen)
                self.glyphs[key] = "".join(pen.d)
            if self.glyphs[key]:
                dy = f' y="{yo}"' if yo else ""
                uses.append(f'<use href="#{key}" x="{pen_x + xo:.0f}"{dy}/>')
            pen_x += adv + tracking*upem
        op = f' fill-opacity="{opacity}"' if opacity is not None else ""
        return (f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.5f} {-k:.5f})" fill="{fill}"{op}{extra}>'
                + "".join(uses) + "</g>")

    def defs(self):
        return "".join(f'<path id="{k}" d="{d}"/>' for k, d in self.glyphs.items() if d)


MOTION = """
.draw{animation:draw 3.2s cubic-bezier(.45,.05,.2,1) backwards}
@keyframes draw{from{stroke-dasharray:1;stroke-dashoffset:1}to{stroke-dasharray:1;stroke-dashoffset:0}}
.in{animation:in 1.2s ease-out backwards}
@keyframes in{from{opacity:0}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}"""


def svg(w, h, label, body, ty, motion=True):
    style = f"<style>{MOTION}</style>" if motion and not os.environ.get("STATIC") else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{escape(label)}">\n{style}\n<defs>{ty.defs()}</defs>\n{body}\n</svg>\n')
