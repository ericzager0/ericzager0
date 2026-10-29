#!/usr/bin/env python3
"""
Genera las piezas fijas del perfil: portada, proyectos, herramientas y botones de contacto.

Uso:
  python scripts/build_static.py
"""
import json
import math
import os
import random

from typeset import THEMES, Type, mix, sheet, svg, width, wrap

OUT = os.environ.get("OUT_DIR", "assets")
W = 1200
X0, X1 = 80, 1120  # márgenes de contenido, compartidos con relieve.py
COL = 350          # columna de contenido de las tablas (herramientas y proyectos anteriores)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "icons.json")) as f:
    ICONS = json.load(f)

NAME = "Eric Zager"
PLACE = "Buenos Aires, Argentina"
BIO = ("Soy estudiante de cuarto año de Ingeniería en Informática en UADE, "
       "enfocado en desarrollo full-stack y análisis de datos.")

# las categorías van en español; los nombres de cada tecnología, como se escriben siempre
STACK = [
    ("Lenguajes", ["Java", "TypeScript", "JavaScript", "Python", "SQL"]),
    ("Backend", ["Spring Boot", "JPA / Hibernate", "Node.js", "Express", "JWT & OAuth"]),
    ("Frontend", ["React", "Next.js", "React Native", "Tailwind CSS"]),
    ("Bases de datos", ["PostgreSQL", "SQL Server", "MongoDB", "Neo4j", "Redis"]),
    ("Datos", ["pandas", "scikit-learn"]),
    ("Herramientas", ["Git", "Docker", "Supabase", "Vercel", "Render", "Postman", "Claude Code"]),
]

# nombre, contexto, etiqueta de estado, descripción, tecnologías
PROJECTS = [
    ("Odofull", "Personal · Individual · 2026", None,
     "Agenda para odontólogos independientes. Confirma los turnos por WhatsApp y ofrece "
     "automáticamente los turnos cancelados al siguiente paciente.",
     ["Next.js", "TypeScript", "PostgreSQL", "Supabase", "WhatsApp Cloud API"]),
    ("GrandPrixTracker", "UADE · Equipo de 4 · 2026", "En curso",
     "Plataforma de reservas de paquetes para carreras de Fórmula 1. Un único checkout atómico cubre "
     "hotel, entradas y vuelos, con control de stock en vivo contra un sistema SOAP heredado.",
     ["Java", "Spring Boot", "Next.js", "PostgreSQL", "Microservicios", "ETL"]),
    ("PoleBid", "UADE · Equipo de 4 · 2026", None,
     "App móvil para pujar en tiempo real en subastas en vivo, construida sobre una base de datos "
     "existente, con control de concurrencia para que las ofertas simultáneas sean consistentes.",
     ["React Native", "TypeScript", "Node.js", "Express", "PostgreSQL", "Supabase Realtime"]),
    ("F1 Driver DNA", "UADE · Equipo de 4 · 2026", None,
     "Sistema de ciencia de datos que compara pilotos de F1 a lo largo de más de 70 años, con un rating "
     "Elo propio que separa al piloto del auto, y agrupa a los pilotos en arquetipos.",
     ["Python", "pandas", "scikit-learn", "UMAP", "Streamlit"]),
]
EARLIER = [
    ("FitBridge", "Marketplace que conecta clientes con entrenadores personales: publicaciones, reservas, "
     "pagos y agenda. Lo desarrollé solo.", ["React", "Node.js", "Express", "Prisma", "PostgreSQL"]),
    ("Matchmaking deportivo", "Backend para publicar y encontrar partidos, con matchmaking y "
     "notificaciones. Lideré un equipo de cuatro.", ["Java", "Spring Boot", "PostgreSQL"]),
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
def hill():
    """Un cerro inventado a la derecha de la portada: dos cumbres unidas por un collado, una tercera
    más baja abajo, una loma que se pierde hacia el texto y otra debajo de la portada, que asoma en la
    esquina de proyectos. El plano se ondula antes de medir la altura, para que las curvas no salgan
    como círculos."""
    peaks = [(925, 285, 78, 1.0), (1095, 120, 62, .86), (1010, 200, 70, .5), (790, 455, 85, .38), (1112, 402, 52, .55),
             (1020, 650, 110, .42)]

    def z(x, y):
        wx = x + 24*math.sin(y/83 + 1) + 10*math.sin((x + y)/41) + 4*math.sin(y/17)
        wy = y + 20*math.sin(x/97) + 8*math.sin((x - y)/37) + 4*math.sin(x/19)
        return sum(a*math.exp(-((wx - cx)**2 + (wy - cy)**2)/(2*s*s)) for cx, cy, s, a in peaks)
    return z


HERO_H = 500
GAP = 23   # el aire que deja GitHub entre imágenes, en unidades del SVG con el ancho habitual del README


def relief():
    """El cerro de la portada: la función de altura, su cumbre y los niveles de las curvas.
    La esquina de proyectos lo usa también, para que el terreno siga por debajo de la portada."""
    z = hill()
    sx, sy = max(((x, y) for x in range(800, 1120, 2) for y in range(120, 380, 2)), key=lambda p: z(*p))
    return z, (sx, sy), [z(sx, sy)*(.05 + .07*i) for i in range(13)]


def contour_style(t, i, n):
    """Color, grosor y desfasaje de la marea de la curva i de n: las de arriba toman el color de acento,
    y la marea baja desde la cumbre."""
    warm = max(0, (i - (n - 5))/4)
    return (f'stroke="{mix(t["topo"], t["accent"], .75*warm)}" stroke-width="{1 + .3*warm:.2f}" '
            f'style="animation-delay:{(n - 1 - i)*1.1 - 20:.1f}s"')


def contour_rings(z, levels, x0, y0, x1, y1):
    """Las curvas de cada nivel ya suavizadas, sin los aros sueltos del tamaño de un punto."""
    rings = {lv: [] for lv in levels}
    for lv, pts, closed in isolines(z, x0, y0, x1, y1, 4, levels):
        xs, ys = zip(*pts)
        d = smooth_path(pts, closed, every=2)
        if d and max(max(xs) - min(xs), max(ys) - min(ys)) > 24:
            rings[lv].append(d)
    return rings


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
def node(t, x, y, pings, kind="server"):
    """Un nodo de la red centrado en (x, y): servidor de dos unidades, base de datos, navegador o celular.
    Cada vez que recibe algo se le enciende una luz y lo rodea un anillo que se abre."""
    ink = f'fill="{t["paper"]}" stroke="{t["ink2"]}" stroke-width="1.8"'
    soft = f'stroke="{t["ink2"]}" stroke-opacity=".5" stroke-width="1.5" stroke-linecap="round"'
    if kind == "server":
        w, uh, gap = 46, 16, 4
        x0, y0, h = x - w/2, y - uh - gap/2, 2*uh + gap
        shape = "".join(f'<rect x="{x0:.1f}" y="{y0 + k*(uh + gap):.1f}" width="{w}" height="{uh}" rx="4" {ink}/>'
                        f'<path d="M{x0 + 24:.1f} {y0 + k*(uh + gap) + uh/2:.1f}h14" {soft}/>' for k in range(2))
        leds = [f'<circle cx="{x0 + 10:.1f}" cy="{y0 + k*(uh + gap) + uh/2:.1f}" r="3"' for k in range(2)]
    elif kind == "db":
        w, h, ry = 40, 44, 6
        x0, y0 = x - w/2, y - h/2
        band = lambda yy: f'M{x0:.1f} {yy:.1f}A{w/2} {ry} 0 0 0 {x0 + w:.1f} {yy:.1f}'
        shape = (f'<path d="M{x0:.1f} {y0 + ry:.1f}V{y0 + h - ry:.1f}A{w/2} {ry} 0 0 0 {x0 + w:.1f} {y0 + h - ry:.1f}'
                 f'V{y0 + ry:.1f}" {ink}/><ellipse cx="{x:.1f}" cy="{y0 + ry:.1f}" rx="{w/2}" ry="{ry}" {ink}/>'
                 f'<path d="{band(y0 + h*.43)}{band(y0 + h*.71)}" fill="none" {soft}/>')
        leds = [f'<circle cx="{x0 + w - 9:.1f}" cy="{y0 + h*f + 6:.1f}" r="3"' for f in (.43, .71)]
    elif kind == "web":
        # una ventana de navegador: barra con tres puntos y una página con renglones
        w, h = 58, 42
        x0, y0 = x - w/2, y - h/2
        shape = (f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h}" rx="5" {ink}/>'
                 f'<path d="M{x0:.1f} {y0 + 11:.1f}h{w}" {soft}/>'
                 + "".join(f'<circle cx="{x0 + 7 + 5*k:.1f}" cy="{y0 + 5.5:.1f}" r="1.6" fill="{t["ink2"]}" fill-opacity=".6"/>'
                           for k in range(3))
                 + f'<path d="M{x0 + 8:.1f} {y0 + 28:.1f}h{w - 22}M{x0 + 8:.1f} {y0 + 35:.1f}h{w - 32}" {soft}/>')
        leds = [f'<rect x="{x0 + 8:.1f}" y="{y0 + 17:.1f}" width="{w - 16}" height="4" rx="2"']
    else:
        # un celular: pantalla con un renglón que se enciende y el parlante arriba
        w, h = 26, 46
        x0, y0 = x - w/2, y - h/2
        shape = (f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h}" rx="6" {ink}/>'
                 f'<path d="M{x - 4:.1f} {y0 + 5:.1f}h8M{x0 + 6:.1f} {y0 + 25:.1f}h{w - 12}M{x0 + 6:.1f} {y0 + 31:.1f}h{w - 17}" {soft}/>')
        leds = [f'<rect x="{x0 + 6:.1f}" y="{y0 + 15:.1f}" width="{w - 12}" height="4" rx="2"']
    # cada luz tiene una base tenue y un destello por cada recepción que le toca: las recepciones se
    # reparten entre las luces en orden, y con una sola recepción se encienden todas, una tras otra
    flashes = ([(k, pings[0] + .12*k) for k in range(len(leds))] if len(pings) == 1
               else [(i % len(leds), at) for i, at in enumerate(pings)])
    shape += "".join(f'{tag} fill="{t["accent"]}" fill-opacity=".35"/>' for tag in leds)
    shape += "".join(f'{leds[k]} class="led" fill="{t["accent"]}" opacity="0" style="animation-delay:{at:.2f}s"/>'
                     for k, at in flashes)
    rings = "".join(f'<rect class="ping" x="{x0 - 8:.1f}" y="{y0 - 8:.1f}" width="{w + 16}" height="{h + 16}" rx="12" '
                    f'fill="none" stroke="{t["accent"]}" stroke-width="1.5" opacity="0" style="animation-delay:{at:.2f}s"/>'
                    for at in pings)
    return f'{rings}<g class="in" style="animation-delay:2.6s">{shape}</g>'


def link(a, b, bend):
    """Un enlace curvo entre dos nodos, en un sentido y en el otro, para que los paquetes viajen por el mismo trazo."""
    (ax, ay), (bx, by) = a, b
    dist = math.dist(a, b)
    ux, uy = (bx - ax)/dist, (by - ay)/dist
    c1 = (ax + ux*dist*.3 - uy*bend, ay + uy*dist*.3 + ux*bend)
    c2 = (bx - ux*dist*.3 + uy*bend, by - uy*dist*.3 - ux*bend)
    go = f"M{ax} {ay}C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {bx} {by}"
    back = f"M{bx} {by}C{c2[0]:.1f} {c2[1]:.1f} {c1[0]:.1f} {c1[1]:.1f} {ax} {ay}"
    return go, back


def hero(t):
    H = HERO_H
    ty = Type()
    z, (sx, sy), levels = relief()
    rings = contour_rings(z, levels, 520, -24, W + 24, H + 24)

    # se dibujan de afuera hacia la cumbre, que toma el color de acento; después respiran en una onda
    # que baja desde la cumbre, la misma marea lenta del resto del perfil
    topo, n = [], len(levels)
    for i, lv in enumerate(levels):
        paths = "".join(f'<path class="draw" pathLength="1" d="{d}" style="animation-delay:{.1 + .14*i:.2f}s"/>'
                        for d in rings[lv])
        topo.append(f'<g class="tide" {contour_style(t, i, n)}>{paths}</g>')

    name = ty.text(NAME, X0 - 5, 258, "display", 136, t["ink"], tracking=-.012)
    bio = "".join(ty.text(line, X0, 336 + i*44, "text", 30, t["ink2"])
                  for i, line in enumerate(wrap(BIO, "text", 30, 600)))
    place = ty.text(PLACE.upper(), X0, 100, "mono-md", 16, t["muted"], tracking=.14)

    # dos peticiones completas recorren el cerro, una después de la otra: el navegador le pide al servidor web
    # y el celular a la API móvil; los dos servidores consultan la misma base de datos y la respuesta vuelve
    # por el mismo camino. Entre una y otra, el servidor web le avisa a la API y la API le confirma.
    # Cada tramo tarda lo mismo y el ciclo dura 10 s.
    peak = lambda x0, x1, y0, y1: max(((x, y) for x in range(x0, x1, 2) for y in range(y0, y1, 2)), key=lambda p: z(*p))
    web, api, db = (sx, sy), peak(1030, 1170, 50, 220), peak(1050, 1170, 330, 470)
    browser, phone = (836, 418), (958, 78)
    (b_web, web_b), (p_api, api_p) = link(browser, web, 20), link(phone, api, -18)
    (web_db, db_web), (api_db, db_api) = link(web, db, 22), link(api, db, -24)
    web_api, api_web = link(web, api, 26)
    start = 4.4
    legs = [(b_web, 0), (web_db, 1.2), (db_web, 2.4), (web_b, 3.6),       # (trazo, salida)
            (web_api, 3.6), (api_web, 4.8),
            (p_api, 5), (api_db, 6.2), (db_api, 7.4), (api_p, 8.6)]
    packets = "".join(f'<path class="leg" pathLength="1" d="{d}" stroke-width="4.5" stroke-dasharray=".16 2" '
                      f'stroke-dashoffset=".16" style="animation-delay:{start + at:.1f}s"/>' for d, at in legs)
    # cada nodo recibe un poco antes de que el paquete termine de entrar
    nodes = "".join(node(t, *xy, [start + at for at in pings], kind) for xy, pings, kind in [
        (web, [.9, 3.3, 5.7], "server"), (api, [4.5, 5.9, 8.3], "server"), (db, [2.1, 7.1], "db"),
        (browser, [4.5], "web"), (phone, [9.5], "phone")])

    body = f'''{sheet(t, W, H, seed=3)}
<defs>
  <linearGradient id="fade" x1="0" x2="1"><stop offset=".45" stop-color="#fff" stop-opacity="0"/><stop offset=".7" stop-color="#fff"/></linearGradient>
  <mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
</defs>
<g clip-path="url(#sheet)"><g mask="url(#m)" fill="none" stroke-linecap="round" stroke-linejoin="round">
{chr(10).join(topo)}
</g></g>
<g fill="none" stroke="{t['accent']}" stroke-linecap="round">
  <g class="in" stroke-width="3.2" stroke-opacity=".8" stroke-dasharray="0 9" style="animation-delay:3s"><path d="{b_web}"/><path d="{p_api}"/><path d="{web_db}"/><path d="{api_db}"/><path d="{web_api}"/></g>
  {packets}
</g>
{nodes}
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


def clusters(t):
    """Una nube de puntos que se agrupa sola en tres clusters, como k-means: los centroides buscan su lugar,
    cada punto toma el color de su grupo y se une a su centroide; después se sueltan y vuelven a empezar.
    En reposo (sin animación) queda el resultado: los tres grupos ya formados."""
    rng = random.Random(11)
    x0, x1, y0, y1 = 680, 1130, 34, 168
    centers = [(790, 112), (930, 70), (1055, 128)]
    colors = [t["accent"], t["ink2"], mix(t["topo"], t["ink2"], .35)]
    cycle = 11
    css, dots, spokes, marks = [], [], [], []
    for k, (cx, cy) in enumerate(centers):
        # el centroide arranca en cualquier lado y llega al centro de su grupo
        sx_, sy_ = rng.uniform(x0 + 30, x1 - 30), rng.uniform(y0 + 20, y1 - 20)
        css.append(f"@keyframes c{k}{{0%,18%{{transform:translate({sx_ - cx:.0f}px,{sy_ - cy:.0f}px);opacity:0}}"
                   f"30%{{opacity:1}}50%,78%{{transform:none;opacity:1}}92%,100%{{transform:none;opacity:0}}}}"
                   f".c{k}{{animation:c{k} {cycle}s ease-in-out infinite}}")
        css.append(f"@keyframes k{k}{{0%,18%,100%{{fill:{t['topo']}}}50%,78%{{fill:{colors[k]}}}}}")
        marks.append(f'<g class="c{k}"><circle cx="{cx}" cy="{cy}" r="7" fill="{t["paper"]}" stroke="{colors[k]}" stroke-width="2"/>'
                     f'<circle cx="{cx}" cy="{cy}" r="2.2" fill="{colors[k]}"/></g>')
        for _ in range(11):
            px = min(max(rng.gauss(cx, 26), x0), x1)
            py = min(max(rng.gauss(cy, 17), y0), y1)
            # cada punto sale de un lugar al azar y llega a su grupo con un leve desfasaje
            fx, fy = rng.uniform(x0, x1), rng.uniform(y0, y1)
            i = len(dots)
            lag = rng.uniform(0, .5)
            css.append(f"@keyframes p{i}{{0%,16%,100%{{transform:translate({fx - px:.0f}px,{fy - py:.0f}px)}}"
                       f"48%,80%{{transform:none}}}}")
            dots.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="4" fill="{colors[k]}" '
                        f'style="animation:p{i} {cycle}s ease-in-out {lag:.2f}s infinite,k{k} {cycle}s ease-in-out {lag:.2f}s infinite"/>')
            spokes.append(f"M{px:.0f} {py:.0f}L{cx} {cy}")
    css.append(f"@keyframes spokes{{0%,50%,82%,100%{{opacity:0}}58%,74%{{opacity:1}}}}"
               f".spokes{{animation:spokes {cycle}s ease-in-out infinite}}")
    style = "" if os.environ.get("STATIC") else f'<style>{"".join(css)}</style>'
    return (f'{style}<g class="in" style="animation-delay:.4s">'
            f'<path class="spokes" d="{"".join(spokes)}" stroke="{t["topo"]}" stroke-width="1" stroke-opacity=".7"/>'
            f'{"".join(dots)}{"".join(marks)}</g>')


def toolkit(t):
    ty = Type()
    parts = [clusters(t), kicker(ty, t, "Stack", 76),
             ty.text("Con qué trabajo", X0 - 2, 140, "heading", 52, t["ink"], tracking=-.01)]
    col, size, lh, gap = COL, 25, 46, 34
    ic, ic_gap = 24, 10
    y = 188
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
    label = "Stack. " + "; ".join(f"{k}: {', '.join(v)}" for k, v in STACK) + "."
    return svg(W, y + 48, label, sheet(t, W, y + 48, seed=5) + "\n".join(parts), ty)


# ---------- proyectos ----------
def projects(t):
    ty = Type()
    rule = lambda y: f'<path d="M{X0} {y}H{X1}" stroke="{t["rule"]}" stroke-width="1.5"/>'
    # en la esquina sigue el mismo cerro de la portada, como si el terreno pasara por debajo de la hoja:
    # las curvas que salen por abajo de la portada vuelven a entrar acá, con el mismo color y la misma marea,
    # y se desvanecen antes del contenido. Las animaciones de entrada ya terminaron, así que solo respiran.
    z, _, levels = relief()
    top = 200
    rings = contour_rings(lambda x, y: z(x, y + HERO_H + GAP), levels, 520, -24, W + 24, top)
    topo = "".join(f'<g class="tide" {contour_style(t, i, len(levels))}>' + "".join(f'<path d="{d}"/>' for d in rings[lv]) + "</g>"
                   for i, lv in enumerate(levels) if rings[lv])
    parts = [f'''<defs>
  <linearGradient id="fx" x1="0" x2="1"><stop offset=".45" stop-color="#fff" stop-opacity="0"/><stop offset=".7" stop-color="#fff"/></linearGradient>
  <linearGradient id="fy" x1="0" x2="0" y1="0" y2="1"><stop offset=".1" stop-color="#fff"/><stop offset=".9" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <mask id="mx"><rect width="{W}" height="{top}" fill="url(#fx)"/></mask>
  <mask id="my"><rect width="{W}" height="{top}" fill="url(#fy)"/></mask>
</defs>
<g clip-path="url(#sheet)"><g mask="url(#my)"><g mask="url(#mx)" fill="none" stroke-linecap="round" stroke-linejoin="round">{topo}</g></g></g>''',
             kicker(ty, t, "Proyectos", 76),
             ty.text("Lo que construí", X0 - 2, 140, "heading", 52, t["ink"], tracking=-.01)]
    y = 188
    for name, meta, status, desc, tech in PROJECTS:
        parts.append(rule(y))
        parts.append(ty.text(name, X0 - 1, y + 60, "heading", 36, t["ink"], tracking=-.005))
        if name in ICONS:
            # el logo va después del nombre, a la altura de sus mayúsculas, sin tocar el margen izquierdo
            parts.append(icon(name, X0 + width(name, "heading", 36, -.005) + 14, y + 32, 30, t["ink2"]))
        parts.append(ty.text(meta.upper(), X1, y + 58, "mono", 14, t["muted"], anchor="end", tracking=.12))
        if status:
            x = X0 + width(name, "heading", 36, -.005) + 20
            w = width(status.upper(), "mono-md", 12, .12) + 38
            # una luz de estado, la misma de los nodos de la portada: el proyecto sigue vivo
            parts.append(f'<rect x="{x:.1f}" y="{y + 34}" width="{w:.1f}" height="28" rx="14" fill="none" '
                         f'stroke="{t["accent"]}" stroke-width="1.5"/>'
                         f'<circle class="pulse" cx="{x + 15:.1f}" cy="{y + 48}" r="9" fill="none" stroke="{t["accent"]}" '
                         f'stroke-width="1.2" opacity="0" style="animation-delay:1.5s"/>'
                         f'<circle class="live" cx="{x + 15:.1f}" cy="{y + 48}" r="3.5" fill="{t["accent"]}"/>')
            parts.append(ty.text(status.upper(), x + 26, y + 52.4, "mono-md", 12, t["accent"], tracking=.12))
        lines = wrap(desc, "text", 25, 940)
        for i, line in enumerate(lines):
            parts.append(ty.text(line, X0, y + 106 + i*36, "text", 25, t["ink2"]))
        tech_y = y + 106 + (len(lines) - 1)*36 + 42
        parts.append(ty.text(" · ".join(tech), X0, tech_y, "mono", 15, t["muted"], tracking=.02))
        y = tech_y + 40

    # proyectos anteriores, en formato compacto como la tabla de herramientas
    parts.append(rule(y))
    parts.append(ty.text("ANTERIORES · 2025", X0, y + 52, "mono-md", 15, t["muted"], tracking=.14))
    y += 80
    for name, desc, tech in EARLIER:
        parts.append(rule(y))
        # el nombre se parte en renglones si no entra en su columna, para no pisar la descripción
        for i, line in enumerate(wrap(name, "text", 25, COL - X0 - 24)):
            parts.append(ty.text(line, X0, y + 46 + i*32, "text", 25, t["ink"]))
        lines = wrap(desc, "text", 22, X1 - COL)
        for i, line in enumerate(lines):
            parts.append(ty.text(line, COL, y + 46 + i*32, "text", 22, t["ink2"]))
        tech_y = y + 46 + (len(lines) - 1)*32 + 34
        parts.append(ty.text(" · ".join(tech), COL, tech_y, "mono", 14, t["muted"], tracking=.02))
        y = tech_y + 32
    parts.append(rule(y))

    label = ("Proyectos. " + " ".join(f"{n} ({m}{', ' + s if s else ''}): {d} Hecho con {', '.join(k)}."
                                     for n, m, s, d, k in PROJECTS)
             + " Anteriores, 2025: " + " ".join(f"{n}: {d} Hecho con {', '.join(k)}." for n, d, k in EARLIER))
    return svg(W, y + 48, label, sheet(t, W, y + 48, seed=4) + "\n".join(parts), ty)


# ---------- botones ----------
def button(t, text, label, primary):
    """Botones nítidos, del mismo material que las tarjetas: el secundario es un trozo de la misma hoja,
    y los dos llevan la sombra corta de las hojas. Sin grano ni borde vivo, para que se lean como botones."""
    ty = Type()
    h, pad, size = 42, 22, 15
    w = round(width(text, "mono-md", size) + 2*pad)
    # las tarjetas se ven reducidas al ancho del README (1200 unidades en unos 830 px) y los botones no:
    # el margen, el borde y la sombra se pasan a esa escala para que el botón arranque donde arranca la hoja
    # y tenga su mismo trazo
    k = 830/W
    x0, line, drop = 5*k, 1.5*k, 2.5*k
    dark = t["page"] != "#FFFFFF"
    shape = (f'<rect x="{x0 + line/2:.2f}" y="{drop + line/2:.2f}" width="{w - line:.2f}" height="{h - line:.2f}" '
             f'rx="{(h - line)/2:.2f}" fill="{"#000" if dark else t["ink"]}" fill-opacity="{.35 if dark else .08}"/>')
    if primary:
        shape += f'<rect x="{x0:.2f}" width="{w}" height="{h}" rx="{h/2}" fill="{t["accent"]}"/>'
        ink = t["btn_ink"]
    else:
        shape += (f'<rect x="{x0 + line/2:.2f}" y="{line/2:.2f}" width="{w - line:.2f}" height="{h - line:.2f}" '
                  f'rx="{(h - line)/2:.2f}" fill="{t["paper"]}" stroke="{t["edge"]}" stroke-width="{line:.2f}"/>')
        ink = t["ink"]
    body = shape + ty.text(text, x0 + w/2, h/2 + 5.2, "mono-md", size, ink, anchor="middle")
    return svg(round(w + x0 + .5), round(h + drop), label, body, ty, motion=False)


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
