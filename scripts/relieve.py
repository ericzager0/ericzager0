#!/usr/bin/env python3
"""
Dibuja tu actividad de GitHub del último año como un relieve topográfico.

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

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

USER = os.environ.get("GH_USER", "ericzager0")
OUT = os.environ.get("OUT_DIR", "assets")
TZ = ZoneInfo("America/Argentina/Buenos_Aires")

SERIF = "Georgia, 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', serif"
THEMES = {
    "light": dict(bg="#F3EEE3", ink="#26231F", muted="#7E7366", line="#9A6B4F", accent="#B8573A"),
    "dark": dict(bg="#1E1C1A", ink="#EFEAE0", muted="#988D80", line="#C08A68", accent="#E07A57"),
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
def smooth(seg):
    pts = seg[::2]
    if not np.allclose(pts[-1], seg[-1]):
        pts = np.vstack([pts, seg[-1]])
    closed = np.hypot(*(seg[0] - seg[-1])) < 1e-6
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(1, len(pts) - 1):
        mx, my = (pts[i] + pts[i + 1]) / 2
        d += f" Q{pts[i][0]:.1f} {pts[i][1]:.1f} {mx:.1f} {my:.1f}"
    return d + f" L{pts[-1][0]:.1f} {pts[-1][1]:.1f}" + ("Z" if closed else "")


W, H = 1280, 420
X0, X1, Y0, Y1 = 84, 1196, 166, 306


def terrain(weeks):
    nw = len(weeks)
    cw, ch = (X1 - X0) / nw, (Y1 - Y0) / 7
    pts = []
    for wi, week in enumerate(weeks):
        for _, n, wd in week:
            if n > 0:
                pts.append((X0 + (wi + .5)*cw, Y0 + (wd + .5)*ch, np.log1p(n)))
    xs = np.arange(0, W + 4, 4); ys = np.arange(0, H + 4, 4)
    X, Y = np.meshgrid(xs, ys)
    # leve deformación para que el relieve se sienta orgánico
    Xw = X + 6*np.sin(Y*0.045 + 1.3) + 4*np.sin(X*0.013)
    Yw = Y + 5*np.sin(X*0.021 + 0.4)
    Z = np.zeros_like(X, dtype=float)
    for px, py, v in pts:
        Z += v*np.exp(-(((Xw - px)/(cw*1.25))**2 + ((Yw - py)/(ch*1.15))**2)/2)
    return X, Y, Z, cw


def contour_paths(X, Y, Z):
    zmax = Z.max()
    if zmax <= 0:
        return [], 0
    levels = np.linspace(0.10*zmax, 0.92*zmax, 10)
    fig, ax = plt.subplots(); cs = ax.contour(X, Y, Z, levels=levels); plt.close(fig)
    return [(li, smooth(s)) for li, segs in enumerate(cs.allsegs) for s in segs if len(s) >= 5], len(levels)


# ---------- dibujo ----------
def render(total, weeks, t, today):
    X, Y, Z, cw = terrain(weeks)
    paths, nl = contour_paths(X, Y, Z)

    css = """
.c{fill:none;stroke-linecap:round;stroke-linejoin:round}
.draw{animation:draw 2.6s cubic-bezier(.4,.1,.2,1) backwards}
@keyframes draw{from{stroke-dasharray:1;stroke-dashoffset:1}to{stroke-dasharray:1;stroke-dashoffset:0}}
.in{animation:in 1s ease-out backwards}
@keyframes in{from{opacity:0}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}"""

    lines = []
    for li, d in paths:
        op = 0.3 + 0.5*(li/max(nl - 1, 1))
        lines.append(f'<path class="c draw" pathLength="1" d="{d}" stroke="{t["line"]}" '
                     f'stroke-width="{1.9 if li % 4 == 3 else 1.0}" stroke-opacity="{op:.2f}" '
                     f'style="animation-delay:{0.1*li:.2f}s"/>')
    if not paths:
        lines.append(f'<path d="M{X0} {(Y0+Y1)/2:.0f} H{X1}" stroke="{t["line"]}" stroke-opacity=".4"/>')

    # eje de meses
    axis = [f'<path d="M{X0} 344 H{X1}" stroke="{t["muted"]}" stroke-opacity=".35" stroke-width="1"/>']
    starts, last_m = [], None
    for wi, week in enumerate(weeks):
        m = int(week[0][0][5:7])
        if m != last_m:
            starts.append((wi, m)); last_m = m
    if len(starts) > 1 and starts[1][0] - starts[0][0] < 3:
        starts = starts[1:]  # el primer mes es solo un pedacito: no lo rotulamos
    last_x = -999
    for wi, m in starts:
            x = X0 + wi*cw
            if x - last_x > 64 and x < X1 - 30:
                axis.append(f'<path d="M{x:.0f} 340 V348" stroke="{t["muted"]}" stroke-opacity=".5"/>')
                axis.append(f'<text x="{x:.0f}" y="374" font-family="{SERIF}" font-style="italic" '
                            f'font-size="19" fill="{t["muted"]}">{MES[m-1]}</text>')
                last_x = x

    # semana más activa
    marker = ""
    sums = [sum(n for _, n, _ in w) for w in weeks]
    if max(sums) > 0:
        wi = int(np.argmax(sums))
        x = X0 + (wi + .5)*cw
        col = np.argmin(abs(X[0] - x))
        y = Y[:, col][np.argmax(Z[:, col])]
        d0 = dt.date.fromisoformat(weeks[wi][0][0])
        label = f"Semana del {d0.day} de {MES_LARGO[d0.month-1]}"
        anchor = "start" if x < 260 else ("end" if x > W - 260 else "middle")
        common = (f'x="{x:.0f}" y="{y-24:.0f}" text-anchor="{anchor}" font-family="{SERIF}" '
                  f'font-style="italic" font-size="21"')
        marker = f'''<g class="in" style="animation-delay:{0.1*nl+1.2:.1f}s">
  <circle cx="{x:.0f}" cy="{y:.0f}" r="12" fill="none" stroke="{t['accent']}" stroke-width="1.5" stroke-opacity=".55"/>
  <circle cx="{x:.0f}" cy="{y:.0f}" r="4.5" fill="{t['accent']}"/>
  <text {common} fill="{t['bg']}" stroke="{t['bg']}" stroke-width="8" stroke-linejoin="round">{label}</text>
  <text {common} fill="{t['ink']}">{label}</text>
</g>'''

    total_txt = f"{total:,}".replace(",", ".")
    noun = "contribución" if total == 1 else "contribuciones"
    updated = f"Actualizado el {today.day} de {MES_LARGO[today.month-1]} de {today.year}"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
  aria-label="Relieve de la actividad de {USER} en GitHub: {total_txt} {noun} en el último año. {updated}.">
<style>{css}</style>
<defs><clipPath id="clip"><rect width="{W}" height="{H}" rx="24"/></clipPath></defs>
<rect width="{W}" height="{H}" rx="24" fill="{t['bg']}"/>
<text x="72" y="92" font-family="{SERIF}" font-size="40" fill="{t['ink']}" letter-spacing="-.5">Actividad del último año</text>
<path d="M76 116 q 18 -9 36 0 t 36 0 t 36 0" fill="none" stroke="{t['accent']}" stroke-width="2.5" stroke-linecap="round"/>
<text x="1208" y="84" text-anchor="end" font-family="{SERIF}" font-size="26" fill="{t['ink']}">{total_txt} {noun}</text>
<text x="1208" y="114" text-anchor="end" font-family="{SERIF}" font-style="italic" font-size="19" fill="{t['muted']}">{updated}</text>
<g clip-path="url(#clip)">
{chr(10).join(lines)}
</g>
{marker}
{chr(10).join(axis)}
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
