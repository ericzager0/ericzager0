#!/usr/bin/env python3
"""
Dibuja tu actividad de GitHub del último año como un perfil de montaña.

Genera assets/relieve-light.svg y assets/relieve-dark.svg.
Solo consulta la cantidad de contribuciones por día; nunca lee código ni repos.

Uso:
  GH_TOKEN=... GH_USER=ericzager0 python scripts/relieve.py
  python scripts/relieve.py --demo     (datos inventados, para probar el diseño)
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from zoneinfo import ZoneInfo

import numpy as np

USER = os.environ.get("GH_USER", "ericzager0")
OUT = os.environ.get("OUT_DIR", "assets")
TZ = ZoneInfo("America/Argentina/Buenos_Aires")

SERIF = "Georgia, 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', serif"
THEMES = {
    "light": dict(bg="#F3EEE3", ink="#26231F", muted="#7E7366", line="#9A6B4F", accent="#B8573A"),
    "dark": dict(bg="#22201D", ink="#E4DDD1", muted="#8C8378", line="#8F7765", accent="#C08670"),
}
MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MES_LARGO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
  }
}"""


# ---------- datos ----------
def fetch():
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("Falta GH_TOKEN.")
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "relieve-de-actividad"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("errors"):
        sys.exit(f"Error de la API: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[(d["date"], d["contributionCount"], d["weekday"]) for d in w["contributionDays"]]
             for w in cal["weeks"]]
    return cal["totalContributions"], weeks


def demo():
    rng = np.random.default_rng(3)
    end = dt.date.today()
    start = end - dt.timedelta(days=364 + (end.weekday() + 1) % 7)
    weeks, cur, total = [], [], 0
    d = start
    while d <= end:
        season = 0.6 + 0.5*np.sin((d.timetuple().tm_yday/365)*2*np.pi*2 + 1.2)
        burst = 2.5 if rng.random() < 0.06 else 1.0
        n = int(rng.poisson(max(season, 0.05)*2.2*burst)) if rng.random() > 0.3 else 0
        wd = (d.weekday() + 1) % 7
        cur.append((d.isoformat(), n, wd)); total += n
        if wd == 6:
            weeks.append(cur); cur = []
        d += dt.timedelta(days=1)
    if cur:
        weeks.append(cur)
    return total, weeks


# ---------- geometría ----------
W, H = 1280, 408
X0, X1, BASE, PEAK = 84, 1196, 336, 148   # el pico más alto llega a BASE - PEAK


def curve(pts):
    """Curva suave (Catmull-Rom) que pasa por todos los puntos."""
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0])/6, p1[1] + (p2[1] - p0[1])/6)
        c2 = (p2[0] - (p3[0] - p1[0])/6, p2[1] - (p3[1] - p1[1])/6)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def weekly(weeks):
    raw = [sum(n for _, n, _ in w) for w in weeks]
    # suavizado leve para que la cordillera se vea orgánica sin falsear los datos
    sm = [(raw[max(i-1, 0)] + 2*raw[i] + raw[min(i+1, len(raw)-1)])/4 for i in range(len(raw))]
    return raw, sm


# ---------- dibujo ----------
def render(total, weeks, t, today):
    raw, sm = weekly(weeks)
    n = len(sm)
    xs = [X0 + i*(X1 - X0)/max(n - 1, 1) for i in range(n)]
    mx = max(sm) if max(sm) > 0 else 1

    def layer(scale, expo):
        return [(x, BASE - ((v/mx)**expo)*PEAK*scale) for x, v in zip(xs, sm)]

    main = layer(1.0, 0.85)
    mid = layer(0.74, 1.25)
    back = layer(0.5, 1.7)
    close = f" L{X1} {BASE} L{X0} {BASE}Z"

    css = """
.draw{animation:draw 2.4s cubic-bezier(.4,.1,.2,1) backwards}
@keyframes draw{from{stroke-dasharray:1;stroke-dashoffset:1}to{stroke-dasharray:1;stroke-dashoffset:0}}
.in{animation:in 1.2s ease-out backwards}
@keyframes in{from{opacity:0}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}"""

    hills = f'''<g class="in" style="animation-delay:.2s">
  <path d="{curve(back)}{close}" fill="{t['accent']}" fill-opacity=".05"/>
  <path d="{curve(mid)}" fill="none" stroke="{t['line']}" stroke-opacity=".3" stroke-width="1.2"/>
  <path d="{curve(main)}{close}" fill="{t['accent']}" fill-opacity=".07"/>
</g>
<path class="draw" pathLength="1" d="{curve(main)}" fill="none" stroke="{t['line']}" stroke-width="2.2"
      stroke-linejoin="round" stroke-linecap="round"/>'''

    # eje de meses
    axis = [f'<path d="M{X0} {BASE} H{X1}" stroke="{t["muted"]}" stroke-opacity=".35" stroke-width="1"/>']
    starts, last_m = [], None
    for wi, week in enumerate(weeks):
        m = int(week[0][0][5:7])
        if m != last_m:
            starts.append((wi, m)); last_m = m
    if len(starts) > 1 and starts[1][0] - starts[0][0] < 3:
        starts = starts[1:]  # el primer mes es solo un pedacito: no lo rotulamos
    last_x = -999
    for wi, m in starts:
        x = xs[wi]
        if x - last_x > 64 and x < X1 - 30:
            axis.append(f'<path d="M{x:.0f} {BASE} V{BASE+6}" stroke="{t["muted"]}" stroke-opacity=".5"/>')
            axis.append(f'<text x="{x:.0f}" y="{BASE+34}" font-family="{SERIF}" font-style="italic" '
                        f'font-size="19" fill="{t["muted"]}">{MES[m-1]}</text>')
            last_x = x

    # semana más activa
    marker = ""
    if max(raw) > 0:
        wi = int(np.argmax(sm))
        x, y = main[wi]
        d0 = dt.date.fromisoformat(weeks[wi][0][0])
        label = f"Semana del {d0.day} de {MES_LARGO[d0.month-1]}"
        anchor = "start" if x < 260 else ("end" if x > W - 260 else "middle")
        common = (f'x="{x:.0f}" y="{y-24:.0f}" text-anchor="{anchor}" font-family="{SERIF}" '
                  f'font-style="italic" font-size="21"')
        marker = f'''<g class="in" style="animation-delay:2.2s">
  <circle cx="{x:.0f}" cy="{y:.0f}" r="12" fill="none" stroke="{t['accent']}" stroke-width="1.5" stroke-opacity=".55"/>
  <circle cx="{x:.0f}" cy="{y:.0f}" r="4.5" fill="{t['accent']}"/>
  <text {common} fill="{t['bg']}" stroke="{t['bg']}" stroke-width="8" stroke-linejoin="round">{label}</text>
  <text {common} fill="{t['ink']}">{label}</text>
</g>'''
    else:
        hills = (f'<text x="{W/2:.0f}" y="{BASE-40}" text-anchor="middle" font-family="{SERIF}" '
                 f'font-style="italic" font-size="22" fill="{t["muted"]}">Todavía no hay actividad este año</text>')

    total_txt = f"{total:,}".replace(",", ".")
    noun = "contribución" if total == 1 else "contribuciones"
    updated = f"Actualizado el {today.day} de {MES_LARGO[today.month-1]} de {today.year}"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
  aria-label="Perfil de la actividad de {USER} en GitHub: {total_txt} {noun} en el último año. {updated}.">
<style>{css}</style>
<rect width="{W}" height="{H}" rx="24" fill="{t['bg']}"/>
<text x="72" y="92" font-family="{SERIF}" font-size="40" fill="{t['ink']}" letter-spacing="-.5">Actividad del último año</text>
<path d="M76 116 q 18 -9 36 0 t 36 0 t 36 0" fill="none" stroke="{t['accent']}" stroke-width="2.5" stroke-linecap="round"/>
<text x="1208" y="84" text-anchor="end" font-family="{SERIF}" font-size="26" fill="{t['ink']}">{total_txt} {noun}</text>
<text x="1208" y="114" text-anchor="end" font-family="{SERIF}" font-style="italic" font-size="19" fill="{t['muted']}">{updated}</text>
{hills}
{chr(10).join(axis)}
{marker}
</svg>'''


def main():
    total, weeks = demo() if "--demo" in sys.argv else fetch()
    today = dt.datetime.now(TZ).date()
    os.makedirs(OUT, exist_ok=True)
    for name, t in THEMES.items():
        with open(os.path.join(OUT, f"relieve-{name}.svg"), "w", encoding="utf-8") as f:
            f.write(render(total, weeks, t, today))
    print(f"Listo: {total} contribuciones en {len(weeks)} semanas.")


if __name__ == "__main__":
    main()
