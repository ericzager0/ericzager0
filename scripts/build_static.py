#!/usr/bin/env python3
"""
Genera las piezas fijas del perfil: portada, herramientas y botones de contacto.

Uso:
  python scripts/build_static.py
"""
import math
import os

from typeset import THEMES, Type, svg, width, wrap

OUT = os.environ.get("OUT_DIR", "assets")
W = 1200
X0, X1 = 80, 1120  # márgenes de contenido, compartidos con relieve.py
COL = 350          # columna de contenido de las tablas (herramientas y proyectos anteriores)

NAME = "Eric Zager"
PLACE = "Buenos Aires, Argentina"
COORDS = "34°36′S  58°22′W"
BIO = ("I’m a fourth-year Computer Engineering student at UADE, "
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
    ("Odofull", "Personal · Solo · 2026", "Beta · 5 clinics",
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
BUMPS = [(935, 240, 150, 1.0), (1110, 450, 120, .62), (740, 30, 140, .5), (1200, 80, 95, .42), (600, 530, 160, .3)]


def height(x, y):
    z = sum(a*math.exp(-((x - cx)**2 + (y - cy)**2)/(2*s*s)) for cx, cy, s, a in BUMPS)
    return z + .05*math.sin(x/97 + y/151) + .035*math.sin(y/63 - x/211)


def summit():
    cx, cy = BUMPS[0][:2]
    return max(((x, y) for x in range(cx - 90, cx + 91, 2) for y in range(cy - 90, cy + 91, 2)),
               key=lambda p: height(*p))


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
    levels = [.12 + i*.075 for i in range(12)]
    lines = isolines(height, -24, -24, W + 24, H + 24, 6, levels)
    accent_lv = levels[-2]
    topo = []
    for n, (lv, pts, closed) in enumerate(lines):
        d = smooth_path(pts, closed)
        if not d:
            continue
        hot = lv == accent_lv and closed
        stroke = t["accent"] if hot else t["topo"]
        sw = 1.6 if hot else 1.1
        op = ".9" if hot else f"{.45 + .5*(lv - levels[0])/(levels[-1] - levels[0]):.2f}"
        topo.append(f'<path class="draw" pathLength="1" d="{d}" stroke="{stroke}" stroke-width="{sw}" '
                    f'stroke-opacity="{op}" style="animation-delay:{.15 + .08*levels.index(lv):.2f}s"/>')

    name = ty.text(NAME, X0 - 5, 258, "display", 136, t["ink"], tracking=-.012)
    bio = "".join(ty.text(line, X0, 336 + i*44, "text", 30, t["ink2"])
                  for i, line in enumerate(wrap(BIO, "text", 30, 600)))
    place = ty.text(PLACE.upper(), X0, 100, "mono-md", 16, t["muted"], tracking=.14)
    px, py = summit()
    cw = width(COORDS, "mono", 15, .04)
    coords = (f'<rect x="{px + 16}" y="{py - 14}" width="{cw + 16:.0f}" height="28" rx="6" fill="{t["paper"]}"/>'
              + ty.text(COORDS, px + 24, py + 5.5, "mono", 15, t["muted"], tracking=.04))

    body = f'''<defs>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="20"/></clipPath>
  <linearGradient id="fade" x1="0" x2="1">
    <stop offset=".4" stop-color="#fff" stop-opacity="0"/><stop offset=".7" stop-color="#fff" stop-opacity="1"/>
  </linearGradient>
  <mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
</defs>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="19.25" fill="{t['paper']}" stroke="{t['edge']}" stroke-width="1.5"/>
<g clip-path="url(#card)"><g mask="url(#m)" fill="none" stroke-linecap="round" stroke-linejoin="round">
{chr(10).join(topo)}
</g></g>
<g class="in" style="animation-delay:1.6s">
  <circle cx="{px}" cy="{py}" r="10" fill="{t['paper']}"/>
  <circle cx="{px}" cy="{py}" r="5" fill="{t['accent']}"/>
  {coords}
</g>
{place}
{name}
{bio}'''
    label = f"{NAME}. {PLACE}. {BIO}"
    return svg(W, H, label, body, ty)


# ---------- herramientas ----------
def toolkit(t):
    ty = Type()
    parts = [kicker(ty, t, "Toolkit", 44),
             ty.text("What I build with", X0 - 2, 108, "heading", 52, t["ink"], tracking=-.01)]
    col, size, lh, gap = COL, 27, 42, 40
    dot_w = width("·", "text", size)
    y = 156
    for label, items in STACK:
        parts.append(f'<path d="M{X0} {y}H{X1}" stroke="{t["rule"]}" stroke-width="1.5"/>')
        parts.append(ty.text(label.upper(), X0, y + 45, "mono-md", 15, t["muted"], tracking=.14))
        widths = [width(item, "text", size) for item in items]
        lines = balance(items, widths, gap, X1 - col)
        for n, line in enumerate(lines):
            x, base = col, y + 48 + n*lh
            for k, i in enumerate(line):
                if k:
                    parts.append(ty.text("·", x - gap/2 - dot_w/2, base, "text", size, t["topo"]))
                parts.append(ty.text(items[i], x, base, "text", size, t["ink"]))
                x += widths[i] + gap
        y += 76 + (len(lines) - 1)*lh
    parts.append(f'<path d="M{X0} {y}H{X1}" stroke="{t["rule"]}" stroke-width="1.5"/>')
    label = "Toolkit. " + "; ".join(f"{k}: {', '.join(v)}" for k, v in STACK) + "."
    return svg(W, y + 30, label, "\n".join(parts), ty, motion=False)


# ---------- proyectos ----------
def projects(t):
    ty = Type()
    rule = lambda y: f'<path d="M{X0} {y}H{X1}" stroke="{t["rule"]}" stroke-width="1.5"/>'
    parts = [kicker(ty, t, "Projects", 44),
             ty.text("What I’ve built", X0 - 2, 108, "heading", 52, t["ink"], tracking=-.01)]
    y = 156
    for name, meta, status, desc, tech in PROJECTS:
        parts.append(rule(y))
        parts.append(ty.text(name, X0 - 1, y + 60, "heading", 36, t["ink"], tracking=-.005))
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
    return svg(W, y + 30, label, "\n".join(parts), ty, motion=False)


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
