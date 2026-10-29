"""
Tipografía y paleta compartidas por todos los SVG del perfil.

GitHub muestra los SVG como imágenes y no garantiza que carguen fuentes, así que
los textos se convierten en contornos con HarfBuzz (con kerning real). Cada glifo
se define una sola vez en <defs> y se reutiliza con <use>, para que pesen poco.
"""
import base64
import math
import os
import random
import struct
import zlib
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
.tide{animation:tide 10s ease-in-out infinite}
@keyframes tide{0%,100%{opacity:.3}50%{opacity:1}}
.leg{animation:leg 10s cubic-bezier(.5,0,.3,1) infinite backwards}
@keyframes leg{0%{stroke-dashoffset:.16}9.6%,100%{stroke-dashoffset:-1}}
.ping{transform-box:fill-box;transform-origin:center;animation:ping 10s ease-out infinite}
@keyframes ping{0%{opacity:.7;transform:scale(.45)}14%,100%{opacity:0;transform:scale(1)}}
.led{animation:led 10s ease-out infinite}
@keyframes led{0%{opacity:1}12%,100%{opacity:0}}
.live{animation:live 2.5s ease-in-out infinite}
@keyframes live{50%{opacity:.3}}
.pulse{transform-box:fill-box;transform-origin:center;animation:pulse 5s ease-out infinite}
@keyframes pulse{0%{opacity:.5;transform:scale(.25)}70%,100%{opacity:0;transform:scale(1)}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}"""


# ---------- la hoja ----------
def mix(a, b, k):
    return "#" + "".join(f"{round(int(a[i:i + 2], 16)*(1 - k) + int(b[i:i + 2], 16)*k):02X}" for i in (1, 3, 5))



def _png_tile(size=96, seed=7):
    """Un PNG gris con transparencia de ruido: el grano del papel, que se repite sin que se note."""
    rng = random.Random(seed)
    rows = b"".join(b"\0" + bytes(v for _ in range(size) for v in (128, rng.choice((0, 0, 0, 0, 9, 16, 26)))) for _ in range(size))
    chunk = lambda kind, data: struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 4, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))
    return base64.b64encode(png).decode()


GRAIN = _png_tile()


def _edge(x0, y0, x1, y1, seed):
    """El contorno de la hoja: un rectángulo redondeado cuyo borde ondula apenas y tiene algo de fibra,
    como papel que no salió de una imprenta."""
    rng = random.Random(seed)
    ph = [rng.uniform(0, 2*math.pi) for _ in range(4)]
    radii = [rng.uniform(17, 24) for _ in range(4)]
    pts, s = [], 0.0
    corners = [(x1, y0, -math.pi/2), (x1, y1, 0), (x0, y1, math.pi/2), (x0, y0, math.pi)]
    for k, (cx, cy, a0) in enumerate(corners):
        r = radii[k]
        ox, oy = cx - r*(1 if cx == x1 else -1), cy - r*(1 if cy == y1 else -1)
        nxt = corners[(k + 1) % 4]
        rn = radii[(k + 1) % 4]
        # el arco de la esquina y después el lado hasta la esquina siguiente
        for i in range(7):
            a = a0 + i/6*math.pi/2
            pts.append((ox + r*math.cos(a), oy + r*math.sin(a), math.cos(a), math.sin(a)))
        a = a0 + math.pi/2
        ex, ey = ox + r*math.cos(a), oy + r*math.sin(a)
        nox, noy = nxt[0] - rn*(1 if nxt[0] == x1 else -1), nxt[1] - rn*(1 if nxt[1] == y1 else -1)
        tx, ty_ = nox + rn*math.cos(nxt[2]), noy + rn*math.sin(nxt[2])
        n = max(int(math.hypot(tx - ex, ty_ - ey)/8), 1)
        for i in range(1, n):
            pts.append((ex + (tx - ex)*i/n, ey + (ty_ - ey)*i/n, math.cos(a), math.sin(a)))
    d, s = [], 0.0
    for i, (x, y, nx, ny) in enumerate(pts):
        if i:
            s += math.hypot(x - pts[i - 1][0], y - pts[i - 1][1])
        w = (1.6*math.sin(s/97 + ph[0]) + .7*math.sin(s/29 + ph[1]) + .3*math.sin(s/7.3 + ph[2])
             + .25*math.sin(s/3.1 + ph[3]) + rng.uniform(-.35, .35))
        d.append(f"{'M' if not i else 'L'}{x + nx*w:.1f} {y + ny*w:.1f}")
    return "".join(d) + "Z"


def sheet(t, w, h, seed=1):
    """La hoja de cada tarjeta, apoyada sobre otra que asoma abajo: borde vivo, luz que entra en diagonal,
    manchas tenues, fibras y grano, y marcas de registro en las esquinas como en un plano.
    Define #sheet para recortar lo que va adentro."""
    m = 5
    edge = _edge(m, m, w - m, h - m - 7, seed)
    under = _edge(m + 14, m + 14, w - m - 10, h - m - 1, seed + 17)
    rng = random.Random(seed*31)
    dark = t["page"] != "#FFFFFF"
    shade = "#000" if dark else t["ink"]
    blots = "".join(f'<ellipse cx="{rng.uniform(0, w):.0f}" cy="{rng.uniform(0, h):.0f}" rx="{rng.uniform(140, 320):.0f}" '
                    f'ry="{rng.uniform(90, 220):.0f}" fill="url(#blot)"/>' for _ in range(max(3, int(h/180))))
    fibers = []
    for _ in range(int(w*h/9000)):
        x, y, a, n = rng.uniform(m, w - m), rng.uniform(m, h - m), rng.uniform(0, math.pi), rng.uniform(6, 22)
        dx, dy, bend = n*math.cos(a), n*math.sin(a), rng.uniform(-5, 5)
        fibers.append(f"M{x:.0f} {y:.0f}q{dx/2 - dy*bend/n:.0f} {dy/2 + dx*bend/n:.0f} {dx:.0f} {dy:.0f}")
    marks = "".join(f'<path d="M{x - 6} {y}H{x + 6}M{x} {y - 6}V{y + 6}"/>'
                    for x in (m + 26, w - m - 26) for y in (m + 26, h - m - 33))
    return f'''<defs>
  <path id="edge" d="{edge}"/>
  <clipPath id="sheet"><use href="#edge"/></clipPath>
  <pattern id="grain" width="96" height="96" patternUnits="userSpaceOnUse"><image width="96" height="96" href="data:image/png;base64,{GRAIN}"/></pattern>
  <radialGradient id="blot"><stop offset="0" stop-color="{t['edge']}" stop-opacity=".55"/><stop offset="1" stop-color="{t['edge']}" stop-opacity="0"/></radialGradient>
  <radialGradient id="vig" cx=".5" cy=".45" r=".75"><stop offset=".6" stop-color="{shade}" stop-opacity="0"/><stop offset="1" stop-color="{shade}" stop-opacity="{.22 if dark else .05}"/></radialGradient>
  <linearGradient id="light" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="{.05 if dark else .45}"/><stop offset=".55" stop-color="#fff" stop-opacity="0"/></linearGradient>
</defs>
<path d="{under}" transform="translate(0 2)" fill="{shade}" fill-opacity="{.35 if dark else .06}"/>
<path d="{under}" fill="{mix(t['paper'], t['edge'], .55)}" stroke="{t['edge']}" stroke-width="1.2"/>
<use href="#edge" y="2.5" fill="{shade}" fill-opacity="{.3 if dark else .06}"/>
<use href="#edge" fill="{t['paper']}"/>
<g clip-path="url(#sheet)">{blots}<rect width="{w}" height="{h}" fill="url(#light)"/><rect width="{w}" height="{h}" fill="url(#vig)"/>
<path d="{"".join(fibers)}" fill="none" stroke="{mix(t['edge'], t['topo'], .45)}" stroke-width=".8" stroke-linecap="round" stroke-opacity=".55"/>
<rect width="{w}" height="{h}" fill="url(#grain)" opacity="{.35 if dark else .5}"/></g>
<use href="#edge" fill="none" stroke="{t['edge']}" stroke-width="1.5"/>
<g stroke="{t['topo']}" stroke-width="1.2" stroke-opacity=".8">{marks}</g>'''


def svg(w, h, label, body, ty, motion=True):
    style = f"<style>{MOTION}</style>" if motion and not os.environ.get("STATIC") else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{escape(label)}">\n{style}\n<defs>{ty.defs()}</defs>\n{body}\n</svg>\n')
