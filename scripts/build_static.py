#!/usr/bin/env python3
"""
Genera las piezas fijas del perfil: portada, proyectos, herramientas y botones de contacto.

Uso:
  python scripts/build_static.py
"""
import json
import math
import os

from typeset import THEMES, Type, svg, width, wrap

OUT = os.environ.get("OUT_DIR", "assets")
W = 1200
X0, X1 = 80, 1120  # márgenes de contenido, compartidos con relieve.py
COL = 350          # columna de contenido de las tablas (herramientas y proyectos anteriores)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "icons.json")) as f:
    ICONS = json.load(f)

NAME = "Eric Zager"
PLACE = "Buenos Aires, Argentina"
BIO =("I’m a fourth-year Computer Engineering student at UADE, "
       "focused on full-stack development and data analysis.")

STACK = [
    ("Languages", ["Java", "TypeScript", "JavaScript", "Python", "SQL"]),
    ("Backend", ["Spring Boot", "JPA / Hibernate", "Node.js", "Express", "JWT & OAuth"]),
    ("Frontend", ["React", "Next.js", "React Native", "Tailwind CSS"]),
    ("Databases", ["PostgreSQL", "SQL Server", "MongoDB", "Neo4j", "Redis"]),
    ("Data", ["pandas", "scikit-learn"]),
    ("Tools", ["Git", "Docker", "Supabase", "Vercel", "Render", "Postman", "Claude Code"]),
]

# nombre, contexto, etiqueta de estado, descripción, tecnologías
PROJECTS = [
    ("Odofull", "Personal · Solo · 2026", None,
     "Scheduling app for independent dentists. It confirms appointments over WhatsApp and "
     "offers cancelled slots to the next patient automatically.",
     ["Next.js", "TypeScript", "PostgreSQL", "Supabase", "WhatsApp Cloud API"]),
    ("GrandPrixTracker", "UADE · Team of 4 · 2026", "In progress",
     "Booking platform for Formula 1 race packages. One atomic checkout covers hotel, tickets "
     "and flights, with live stock checks against a legacy SOAP system.",
     ["Java", "Spring Boot", "Next.js", "PostgreSQL", "Microservices", "ETL"]),
    ("PoleBid", "UADE · Team of 4 · 2026", None,
     "Mobile app for real-time bidding at live auctions, built on top of an existing database "
     "with concurrency control so simultaneous bids stay consistent.",
     ["React Native", "TypeScript", "Node.js", "Express", "PostgreSQL", "Supabase Realtime"]),
    ("F1 Driver DNA", "UADE · Team of 4 · 2026", None,
     "Data science system that compares F1 drivers across 70+ years, with a custom Elo rating "
     "that separates driver from car, and clusters drivers into archetypes.",
     ["Python", "pandas", "scikit-learn", "UMAP", "Streamlit"]),
]
EARLIER = [
    ("FitBridge", "Marketplace that connects clients with personal trainers: listings, booking, "
     "payments and scheduling. Built solo.", ["React", "Node.js", "Express", "Prisma", "PostgreSQL"]),
    ("Sports matchmaking", "Backend to publish and find pickup games, with matchmaking and "
     "notifications. I led a team of four.", ["Java", "Spring Boot", "PostgreSQL"]),
]

LINKS = [
    ("linkedin", "LinkedIn ↗", "LinkedIn", True),
    ("mail", "ericzager0@gmail.com", "ericzager0@gmail.com", False),
]


def kicker(ty, t, label, y):
    return ty.text(label.upper(), X0, y, "mono-md", 16, t["accent"], tracking=.14)


def balance(items, widths, gap, avail):
    """Reparte los ítems en líneas parejas, para que ninguno quede solo abajo."""
    total = sum(widths) + gap*(len(items) - 1)
    if total <= avail:
        return [list(range(len(items)))]
    line_w = lambda a, b: sum(widths[a:b]) + gap*(b - a - 1)
    k = min(range(1, len(items)), key=lambda k: max(line_w(0, k), line_w(k, len(items))))
    return [list(range(k)), list(range(k, len(items)))]


# ---------- curvas de nivel ----------
def terrain(bumps):
    def z(x, y):
        h = sum(a*math.exp(-((x - cx)**2 + (y - cy)**2)/(2*s*s)) for cx, cy, s, a in bumps)
        return h + .05*math.sin(x/97 + y/151) + .035*math.sin(y/63 - x/211)
    return z


# Silueta de Argentina muy simplificada (longitud, latitud): un guiño, no un mapa exacto.
# Arranca en el límite con Bolivia y recorre el país en sentido horario.
ARGENTINA = [
    (-66.2, -21.8), (-64.3, -22.0), (-62.7, -22.1), (-60.5, -23.6), (-58.2, -24.4), (-57.6, -25.4),
    (-55.8, -26.0), (-54.6, -25.6), (-53.7, -26.3), (-54.0, -27.2), (-55.8, -27.6), (-57.4, -29.6),
    (-57.9, -31.5), (-58.3, -33.4), (-58.4, -34.5), (-57.2, -35.7), (-56.8, -36.6), (-57.6, -38.1),
    (-61.0, -38.9), (-62.3, -39.0), (-62.2, -40.6), (-63.9, -41.2), (-65.0, -41.0), (-64.4, -42.5),
    (-65.2, -43.4), (-65.4, -45.0), (-67.4, -46.0), (-65.9, -47.8), (-67.7, -49.4), (-68.9, -51.5),
    (-68.4, -52.4), (-67.0, -53.7), (-65.3, -54.8), (-67.6, -55.0), (-68.6, -54.6), (-69.4, -52.3),
    (-71.9, -52.0), (-72.4, -50.8), (-73.3, -49.4), (-72.4, -47.9), (-71.8, -46.4), (-71.6, -44.6),
    (-71.9, -42.2), (-71.5, -39.8), (-71.1, -37.8), (-70.4, -35.6), (-70.0, -33.1), (-69.8, -30.6),
    (-68.8, -28.0), (-68.4, -25.4), (-67.3, -23.9), (-67.1, -22.7),
]
MALVINAS = [
    [(-61.3, -51.3), (-60.6, -51.25), (-59.9, -51.4), (-59.7, -51.8), (-60.2, -52.2), (-60.9, -52.1), (-61.35, -51.8)],
    [(-59.4, -51.4), (-58.6, -51.3), (-57.8, -51.5), (-57.7, -51.8), (-58.3, -52.1), (-59.0, -52.3), (-59.4, -51.9)],
]
BUENOS_AIRES = (-58.4, -34.6)
MAP_TOP, MAP_H, MAP_CX = 26, 448, 965   # el mapa ocupa casi todo el alto de la portada


def project(lon, lat):
    k = MAP_H/33.2
    return MAP_CX + (lon + 63.4)*math.cos(math.radians(38))*k, MAP_TOP + (-21.8 - lat)*k


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0, min(1, ((px - ax)*dx + (py - ay)*dy)/(dx*dx + dy*dy)))
    return math.hypot(px - ax - t*dx, py - ay - t*dy)


def coast():
    """Los polígonos del país ya proyectados, y una función que da (adentro, distancia a la costa)."""
    polys = [[project(*p) for p in shape] for shape in [ARGENTINA] + MALVINAS]
    edges = [(a, b) for poly in polys for a, b in zip(poly, poly[1:] + poly[:1])]

    def locate(x, y):
        inside = False
        for (ax, ay), (bx, by) in edges:
            if (ay > y) != (by > y) and x < ax + (y - ay)*(bx - ax)/(by - ay):
                inside = not inside
        return inside, min(seg_dist(x, y, *a, *b) for a, b in edges)
    return polys, locate


def country_relief():
    """Relieve evocado: llano adentro, con la cordillera al oeste. Devuelve la función de altura."""
    polys, locate = coast()
    # la cordillera corre por el borde oeste (del extremo sur hacia el norte), un poco hacia adentro
    andes = [(x + 22, y) for x, y in polys[0][polys[0].index(project(-69.4, -52.3)):]]
    # sierras de Córdoba, de Tandil y la meseta patagónica, para que el interior no quede vacío
    hills = [(*project(lon, lat), s, a) for lon, lat, s, a in
             [(-64.6, -31.6, 13, .38), (-59.6, -37.6, 9, .2), (-68.6, -43.2, 26, .22)]]

    def z(x, y):
        inside, edge = locate(x, y)
        if not inside:
            return 0
        ridge = min(seg_dist(x, y, *a, *b) for a, b in zip(andes, andes[1:]))
        ease = lambda v: min(v, 1)*min(v, 1)*(3 - 2*min(v, 1))
        noise = .5 + .25*math.sin(x/23 + y/41) + .25*math.sin(y/17 - x/37)
        bumps = sum(a*math.exp(-((x - cx)**2 + (y - cy)**2)/(2*s*s)) for cx, cy, s, a in hills)
        # la costa sube rápido; la cordillera, de a poco, para que sus curvas no se apilen en el borde
        return ease(edge/10)*(.12 + .06*noise) + ease(edge/34)*(.8*math.exp(-ridge*ridge/(2*24*24)) + bumps)
    return z


def sea_depth():
    """Fondo del mar alrededor del país: la distancia a la costa, ondulada para que se vea natural."""
    _, locate = coast()

    def z(x, y):
        inside, edge = locate(x, y)
        if inside:
            return 0
        return edge + min(edge/40, 1)*(7*math.sin(x/53 + y/89) + 5*math.sin(y/37 - x/71))
    return z


def isolines(f, x0, y0, x1, y1, step, levels):
    nx, ny = int((x1 - x0)/step) + 1, int((y1 - y0)/step) + 1
    v = [[f(x0 + i*step, y0 + j*step) for i in range(nx)] for j in range(ny)]
    table = {1: [("L", "B")], 2: [("B", "R")], 3: [("L", "R")], 4: [("T", "R")], 6: [("T", "B")],
             7: [("T", "L")], 8: [("T", "L")], 9: [("T", "B")], 11: [("T", "R")], 12: [("L", "R")],
             13: [("R", "B")], 14: [("L", "B")]}
    out = []
    for lv in levels:
        def point(e):
            kind, i, j = e
            a = v[j][i]
            b = v[j][i + 1] if kind == "h" else v[j + 1][i]
            t = (lv - a)/(b - a)
            return (x0 + (i + t)*step, y0 + j*step) if kind == "h" else (x0 + i*step, y0 + (j + t)*step)

        adj = {}
        for j in range(ny - 1):
            for i in range(nx - 1):
                tl, tr, br, bl = v[j][i], v[j][i + 1], v[j + 1][i + 1], v[j + 1][i]
                case = (tl > lv)*8 + (tr > lv)*4 + (br > lv)*2 + (bl > lv)
                edges = {"T": ("h", i, j), "R": ("v", i + 1, j), "B": ("h", i, j + 1), "L": ("v", i, j)}
                if case in (5, 10):
                    joined = (tl + tr + br + bl)/4 > lv
                    segs = {(5, False): [("T", "R"), ("L", "B")], (5, True): [("T", "L"), ("R", "B")],
                            (10, False): [("T", "L"), ("R", "B")], (10, True): [("T", "R"), ("L", "B")]}[(case, joined)]
                else:
                    segs = table.get(case, [])
                for a, b in segs:
                    adj.setdefault(edges[a], []).append(edges[b])
                    adj.setdefault(edges[b], []).append(edges[a])
        seen = set()
        starts = [e for e in adj if len(adj[e]) == 1] + list(adj)
        for s in starts:
            if s in seen:
                continue
            chain, cur, prev = [s], s, None
            seen.add(s)
            while True:
                nxt = [n for n in adj[cur] if n != prev and n not in seen]
                if not nxt:
                    break
                prev, cur = cur, nxt[0]
                seen.add(cur); chain.append(cur)
            closed = len(adj[s]) == 2 and s in adj[chain[-1]] and len(chain) > 2
            if len(chain) > 3:
                out.append((lv, [point(e) for e in chain], closed))
    return out


def smooth_path(pts, closed, every=3):
    pts = pts[::every] + ([] if closed else [pts[-1]])
    if len(pts) < 3:
        return ""
    mid = lambda a, b: ((a[0] + b[0])/2, (a[1] + b[1])/2)
    if closed:
        m0 = mid(pts[-1], pts[0])
        d = f"M{m0[0]:.1f} {m0[1]:.1f}"
        for i, p in enumerate(pts):
            m = mid(p, pts[(i + 1) % len(pts)])
            d += f"Q{p[0]:.1f} {p[1]:.1f} {m[0]:.1f} {m[1]:.1f}"
        return d + "Z"
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(1, len(pts) - 1):
        m = mid(pts[i], pts[i + 1])
        d += f"Q{pts[i][0]:.1f} {pts[i][1]:.1f} {m[0]:.1f} {m[1]:.1f}"
    return d + f"L{pts[-1][0]:.1f} {pts[-1][1]:.1f}"


# ---------- portada ----------
def hero(t):
    H = 500
    ty = Type()
    levels = [.03, .17, .27, .38, .5, .62, .74, .86]
    lines = isolines(country_relief(), 740, 0, 1130, H, 3, levels)
    topo = []
    for lv, pts, closed in lines:
        d = smooth_path(pts, closed, every=2)
        if not d:
            continue
        coast = lv == levels[0]
        sw = 1.5 if coast else 1.1
        op = "1" if coast else f"{.55 + .4*levels.index(lv)/len(levels):.2f}"
        stroke = t["ink2"] if coast else t["topo"]
        topo.append(f'<path class="draw" pathLength="1" d="{d}" stroke="{stroke}" stroke-width="{sw}" '
                    f'stroke-opacity="{op}" style="animation-delay:{.1 + .12*levels.index(lv):.2f}s"/>')

    name = ty.text(NAME, X0 - 5, 258, "display", 136, t["ink"], tracking=-.012)
    bio = "".join(ty.text(line, X0, 336 + i*44, "text", 30, t["ink2"])
                  for i, line in enumerate(wrap(BIO, "text", 30, 600)))
    place = ty.text(PLACE.upper(), X0, 100, "mono-md", 16, t["muted"], tracking=.14)
    px, py = (round(v, 1) for v in project(*BUENOS_AIRES))

    # el mar alrededor: una marea lenta que se aleja de la costa, una vez que el mapa ya está dibujado
    depths = [12, 26, 44, 66, 92, 122, 156, 194]
    sea = []
    for lv, pts, closed in isolines(sea_depth(), 560, -24, W + 24, H + 24, 6, depths):
        d = smooth_path(pts, closed)
        if d:
            i = depths.index(lv)
            sea.append(f'<path class="tide" d="{d}" stroke-opacity="{.85 - .06*i:.2f}" '
                       f'style="animation-delay:{i*1.1 - 20:.1f}s"/>')

    body = f'''<defs>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="20"/></clipPath>
  <linearGradient id="fade" x1="0" x2="1"><stop offset=".45" stop-color="#fff" stop-opacity="0"/><stop offset=".68" stop-color="#fff"/></linearGradient>
  <mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
</defs>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="19.25" fill="{t['paper']}" stroke="{t['edge']}" stroke-width="1.5"/>
<g clip-path="url(#card)"><g class="in" mask="url(#m)" fill="none" stroke="{t['topo']}" stroke-width="1" style="animation-delay:1.2s">
{chr(10).join(sea)}
</g></g>
<g fill="none" stroke-linecap="round" stroke-linejoin="round">
{chr(10).join(topo)}
</g>
<ellipse class="pulse" cx="{px}" cy="{py + 1}" rx="20" ry="6.5" fill="none" stroke="{t['accent']}" stroke-width="1.5" opacity="0" style="animation-delay:3.4s"/>
<ellipse class="in" cx="{px}" cy="{py + 1}" rx="8" ry="2.6" fill="{t['ink']}" fill-opacity=".18" style="animation-delay:2.3s"/>
<g class="drop" style="animation-delay:2.2s">
  <path d="M{px} {py}C{px - 2} {py - 6} {px - 11} {py - 15} {px - 11} {py - 26}A11 11 0 1 1 {px + 11} {py - 26}C{px + 11} {py - 15} {px + 2} {py - 6} {px} {py}Z" fill="{t['accent']}"/>
  <circle cx="{px}" cy="{py - 26}" r="4" fill="{t['paper']}"/>
</g>
{place}
{name}
{bio}'''
    label = f"{NAME}. {PLACE}. {BIO}"
    return svg(W, H, label, body, ty)


# ---------- herramientas ----------
def icon(name, x, y, size, color):
    """Logo monocromático de una tecnología, con su esquina superior izquierda en (x, y)."""
    ic = ICONS[name]
    paint = (f'fill="none" stroke="{color}" stroke-width="1.9" stroke-linecap="round"'
             if ic.get("stroke") else f'fill="{color}"' + (' fill-rule="evenodd"' if ic.get("evenodd") else ""))
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({size/ic["box"]:.4f})" {paint}>'
            + "".join(f'<path d="{d}"/>' for d in ic["paths"]) + "</g>")


def toolkit(t):
    ty = Type()
    parts = [kicker(ty, t, "Toolkit", 44),
             ty.text("What I build with", X0 - 2, 108, "heading", 52, t["ink"], tracking=-.01)]
    col, size, lh, gap = COL, 25, 46, 34
    ic, ic_gap = 24, 10
    y = 156
    for label, items in STACK:
        parts.append(f'<path d="M{X0} {y}H{X1}" stroke="{t["rule"]}" stroke-width="1.5"/>')
        parts.append(ty.text(label.upper(), X0, y + 45, "mono-md", 15, t["muted"], tracking=.14))
        widths = [ic + ic_gap + width(item, "text", size) for item in items]
        lines = balance(items, widths, gap, X1 - col)
        for n, line in enumerate(lines):
            x, base = col, y + 48 + n*lh
            for i in line:
                parts.append(icon(items[i], x, base - 20.5, ic, t["ink2"]))
                parts.append(ty.text(items[i], x + ic + ic_gap, base, "text", size, t["ink"]))
                x += widths[i] + gap
        y += 76 + (len(lines) - 1)*lh
    parts.append(f'<path d="M{X0} {y}H{X1}" stroke="{t["rule"]}" stroke-width="1.5"/>')
    label = "Toolkit. " + "; ".join(f"{k}: {', '.join(v)}" for k, v in STACK) + "."
    return svg(W, y + 30, label, "\n".join(parts), ty, motion=False)


# ---------- proyectos ----------
def projects(t):
    ty = Type()
    rule = lambda y: f'<path d="M{X0} {y}H{X1}" stroke="{t["rule"]}" stroke-width="1.5"/>'
    # un fragmento de relieve en la esquina, que retoma la portada y se desvanece antes del contenido;
    # respira con la misma marea que el mar de la portada, porque las animaciones de entrada ya terminaron
    corner = terrain([(1240, -50, 170, 1.0), (1000, -110, 130, .6)])
    levels = [.08 + i*.07 for i in range(11)]
    paths = [d for d in (smooth_path(p, c) for _, p, c in isolines(corner, 520, -24, W + 24, 170, 6, levels)) if d]
    topo = "".join(f'<path class="tide" d="{d}" style="animation-delay:{i*1.1 - 20:.1f}s"/>' for i, d in enumerate(paths))
    parts = [f'''<defs>
  <linearGradient id="fx" x1="0" x2="1"><stop offset=".5" stop-color="#fff" stop-opacity="0"/><stop offset=".85" stop-color="#fff"/></linearGradient>
  <linearGradient id="fy" x1="0" x2="0" y1="0" y2="1"><stop offset=".1" stop-color="#fff"/><stop offset=".85" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <mask id="mx"><rect width="{W}" height="170" fill="url(#fx)"/></mask>
  <mask id="my"><rect width="{W}" height="170" fill="url(#fy)"/></mask>
</defs>
<g mask="url(#my)"><g mask="url(#mx)" fill="none" stroke="{t['topo']}" stroke-width="1.1">{topo}</g></g>''',
             kicker(ty, t, "Projects", 44),
             ty.text("What I’ve built", X0 - 2, 108, "heading", 52, t["ink"], tracking=-.01)]
    y = 156
    for name, meta, status, desc, tech in PROJECTS:
        parts.append(rule(y))
        parts.append(ty.text(name, X0 - 1, y + 60, "heading", 36, t["ink"], tracking=-.005))
        if name in ICONS:
            # el logo va después del nombre, a la altura de sus mayúsculas, sin tocar el margen izquierdo
            parts.append(icon(name, X0 + width(name, "heading", 36, -.005) + 14, y + 32, 30, t["ink2"]))
        parts.append(ty.text(meta.upper(), X1, y + 58, "mono", 14, t["muted"], anchor="end", tracking=.12))
        if status:
            x = X0 + width(name, "heading", 36, -.005) + 20
            w = width(status.upper(), "mono-md", 12, .12) + 24
            parts.append(f'<rect x="{x:.1f}" y="{y + 34}" width="{w:.1f}" height="28" rx="14" fill="none" '
                         f'stroke="{t["accent"]}" stroke-width="1.5"/>')
            parts.append(ty.text(status.upper(), x + 12, y + 52.4, "mono-md", 12, t["accent"], tracking=.12))
        lines = wrap(desc, "text", 25, 940)
        for i, line in enumerate(lines):
            parts.append(ty.text(line, X0, y + 106 + i*36, "text", 25, t["ink2"]))
        tech_y = y + 106 + (len(lines) - 1)*36 + 42
        parts.append(ty.text(" · ".join(tech), X0, tech_y, "mono", 15, t["muted"], tracking=.02))
        y = tech_y + 40

    # proyectos anteriores, en formato compacto como la tabla de herramientas
    parts.append(rule(y))
    parts.append(ty.text("EARLIER · 2025", X0, y + 52, "mono-md", 15, t["muted"], tracking=.14))
    y += 80
    for name, desc, tech in EARLIER:
        parts.append(rule(y))
        parts.append(ty.text(name, X0, y + 46, "text", 25, t["ink"]))
        lines = wrap(desc, "text", 22, X1 - COL)
        for i, line in enumerate(lines):
            parts.append(ty.text(line, COL, y + 46 + i*32, "text", 22, t["ink2"]))
        tech_y = y + 46 + (len(lines) - 1)*32 + 34
        parts.append(ty.text(" · ".join(tech), COL, tech_y, "mono", 14, t["muted"], tracking=.02))
        y = tech_y + 32
    parts.append(rule(y))

    label = ("Projects. " + " ".join(f"{n} ({m}{', ' + s if s else ''}): {d} Built with {', '.join(k)}."
                                     for n, m, s, d, k in PROJECTS)
             + " Earlier, 2025: " + " ".join(f"{n}: {d} Built with {', '.join(k)}." for n, d, k in EARLIER))
    return svg(W, y + 30, label, "\n".join(parts), ty)


# ---------- botones ----------
def button(t, text, label, primary):
    ty = Type()
    h, pad, size = 44, 22, 15
    w = round(width(text, "mono-md", size) + 2*pad)
    if primary:
        shape = f'<rect width="{w}" height="{h}" rx="{h/2}" fill="{t["accent"]}"/>'
        ink = t["btn_ink"]
    else:
        shape = f'<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="{h/2 - .75}" fill="none" stroke="{t["ink2"]}" stroke-opacity=".55" stroke-width="1.5"/>'
        ink = t["ink"]
    body = shape + ty.text(text, w/2, h/2 + 5.2, "mono-md", size, ink, anchor="middle")
    return svg(w, h, label, body, ty, motion=False)


def main():
    os.makedirs(OUT, exist_ok=True)
    for theme, t in THEMES.items():
        files = {"hero": hero(t), "projects": projects(t), "stack": toolkit(t)}
        files.update({key: button(t, text, label, primary) for key, text, label, primary in LINKS})
        for key, content in files.items():
            with open(os.path.join(OUT, f"{key}-{theme}.svg"), "w", encoding="utf-8") as f:
                f.write(content)
    print("Listo.")


if __name__ == "__main__":
    main()
